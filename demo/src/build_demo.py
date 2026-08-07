from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


FEATURES = ["down_force", "platen_speed", "slurry_flow", "pad_age", "pattern_density"]


def load_rows(path: Path) -> list[dict[str, float]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = [{key: float(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    if len(rows) < 10:
        raise ValueError("At least 10 rows are required")
    return rows


def audit(rows: list[dict[str, float]]) -> dict[str, object]:
    missing = sum(value is None for row in rows for value in row.values())
    duplicate_count = len(rows) - len({tuple(row.items()) for row in rows})
    ranges = {
        key: {"min": min(row[key] for row in rows), "max": max(row[key] for row in rows)}
        for key in FEATURES
    }
    return {"rows": len(rows), "missing": missing, "duplicates": duplicate_count, "ranges": ranges}


def design(rows: list[dict[str, float]]) -> np.ndarray:
    base = np.array([[row[key] for key in FEATURES] for row in rows], dtype=float)
    interaction = (base[:, 2] * base[:, 4]).reshape(-1, 1)
    pad_squared = (base[:, 3] ** 2).reshape(-1, 1)
    return np.column_stack([np.ones(len(rows)), base, interaction, pad_squared])


def rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def build_payload(rows: list[dict[str, float]]) -> tuple[dict[str, object], dict[str, object]]:
    split = int(len(rows) * 0.8)
    train, test = rows[:split], rows[split:]
    x_train, x_test = design(train), design(test)
    y_train = np.array([row["removal_rate"] for row in train])
    y_test = np.array([row["removal_rate"] for row in test])
    coefficients, *_ = np.linalg.lstsq(x_train, y_train, rcond=None)
    baseline = np.full_like(y_test, y_train.mean())
    improved = x_test @ coefficients
    names = ["intercept", *FEATURES, "slurry_x_density", "pad_age_squared"]
    model = {
        "feature_names": names,
        "coefficients": {name: round(float(value), 8) for name, value in zip(names, coefficients)},
        "training_ranges": audit(rows)["ranges"],
        "educational_only": True,
    }
    metrics = {
        "train_rows": len(train),
        "holdout_rows": len(test),
        "baseline_rmse": round(rmse(y_test, baseline), 3),
        "improved_rmse": round(rmse(y_test, improved), 3),
        "audit": audit(rows),
    }
    return model, metrics


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    demo_root = Path(__file__).resolve().parents[1]
    output_root = (args.output_root or demo_root).resolve()
    rows = load_rows(demo_root / "data/raw/cmp_demo.csv")
    model, metrics = build_payload(rows)
    for folder in (output_root / "artifacts", output_root / "docs/artifacts"):
        write_json(folder / "model_params.json", model)
        write_json(folder / "metrics.json", metrics)
    print(json.dumps({"status": "ok", "output_root": str(output_root), **metrics}, ensure_ascii=False))


if __name__ == "__main__":
    main()
