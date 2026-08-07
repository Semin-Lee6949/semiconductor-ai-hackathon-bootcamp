#!/usr/bin/env python3
"""Create a compact data-quality report and chart gallery from noisy CMP data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


DEFAULT_INPUT = Path("datasets/student/05_cmp/A/train.csv")
DEFAULT_OUTPUT = Path("artifacts/data_quality")


def iqr_outlier_mask(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    q1, q3 = numeric.quantile([0.25, 0.75])
    iqr = q3 - q1
    if pd.isna(iqr) or iqr == 0:
        return pd.Series(False, index=series.index)
    return (numeric < q1 - 1.5 * iqr) | (numeric > q3 + 1.5 * iqr)


def build_report(data: pd.DataFrame) -> dict:
    numeric_columns = list(data.select_dtypes(include="number").columns)
    return {
        "rows": int(len(data)),
        "columns": int(len(data.columns)),
        "exact_duplicate_rows": int(data.duplicated().sum()),
        "missing_by_column": {
            column: int(count)
            for column, count in data.isna().sum().items()
            if count
        },
        "iqr_outlier_candidates": {
            column: int(iqr_outlier_mask(data[column]).sum())
            for column in numeric_columns
        },
        "samples_by_tool": {
            str(tool): int(count)
            for tool, count in data["tool_id"].value_counts().items()
        },
        "warning": (
            "IQR flags are review candidates, not automatic deletion rules. "
            "Determine physical, unit, tool, lot, and time context first."
        ),
    }


def prepare_visualization_view(data: pd.DataFrame) -> pd.DataFrame:
    view = data.drop_duplicates().copy()
    numeric_columns = view.select_dtypes(include="number").columns
    for column in numeric_columns:
        view[column] = view.groupby("tool_id")[column].transform(
            lambda values: values.fillna(values.median())
        )
        view[column] = view[column].fillna(view[column].median())
    return view


def draw_gallery(raw: pd.DataFrame, view: pd.DataFrame, output: Path) -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    figure, axes = plt.subplots(2, 3, figsize=(16, 9), constrained_layout=True)

    sns.histplot(data=raw, x="yield_proxy", hue="tool_id", element="step", ax=axes[0, 0])
    axes[0, 0].set_title("Distribution: yield by tool")

    sns.boxplot(data=view, x="tool_id", y="wiwnu_proxy", ax=axes[0, 1], color="#8ecae6")
    sns.stripplot(
        data=view.sample(min(250, len(view)), random_state=7),
        x="tool_id",
        y="wiwnu_proxy",
        ax=axes[0, 1],
        color="#023047",
        alpha=0.35,
        size=2,
    )
    axes[0, 1].set_title("Group comparison: box + observed points")

    sns.scatterplot(
        data=view,
        x="down_force_psi",
        y="yield_proxy",
        hue="tool_id",
        alpha=0.55,
        ax=axes[0, 2],
    )
    axes[0, 2].set_title("Relationship: force vs yield")

    ordered = view.sort_values("sequence").copy()
    ordered["rolling_yield"] = ordered["yield_proxy"].rolling(35, min_periods=8).median()
    sns.lineplot(data=ordered, x="sequence", y="rolling_yield", ax=axes[1, 0], color="#d62828")
    axes[1, 0].set_title("Time order: rolling median")

    missing = raw.isna().astype(int)
    missing_columns = list(missing.sum().sort_values(ascending=False).head(8).index)
    sns.heatmap(missing[missing_columns].T, cbar=False, cmap=["#f7f7f7", "#d62828"], ax=axes[1, 1])
    axes[1, 1].set_title("Missingness location")
    axes[1, 1].set_xlabel("row order")

    corr_columns = [
        "down_force_psi",
        "platen_speed_rpm",
        "pad_age_runs",
        "pattern_density",
        "removal_rate_proxy",
        "wiwnu_proxy",
        "dishing_nm",
        "yield_proxy",
    ]
    sns.heatmap(view[corr_columns].corr(), cmap="vlag", center=0, ax=axes[1, 2])
    axes[1, 2].set_title("Exploration only: correlation")

    figure.suptitle("Noisy CMP data audit — inspect before modeling", fontsize=16)
    figure.savefig(output, dpi=150)
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    data = pd.read_csv(args.input)
    args.output.mkdir(parents=True, exist_ok=True)
    report = build_report(data)
    view = prepare_visualization_view(data)

    summary_path = args.output / "cmp_audit_summary.json"
    figure_path = args.output / "cmp_audit_gallery.png"
    summary_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    draw_gallery(data, view, figure_path)

    print(f"rows={report['rows']} duplicates={report['exact_duplicate_rows']}")
    print(f"missing={sum(report['missing_by_column'].values())}")
    print(f"summary={summary_path}")
    print(f"figure={figure_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
