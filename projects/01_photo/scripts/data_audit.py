"""STEP 2 audit for the educational Photo PR training data.

This script is deliberately read-only with respect to the source CSV. It does
not impute, correct, remove, correlate, or model any observations.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path
from statistics import median


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "datasets/student/01_photo/A/train.csv"
SCHEMA = ROOT / "datasets/schema.json"
OUTPUT = ROOT / "projects/01_photo/outputs/data_audit"
FIGURES = OUTPUT / "figures"

IDENTIFIERS = {"sample_id", "lot_id", "tool_id", "sequence"}
CATEGORICAL = {"pr_tone", "retained_pattern_source", "spec_pass"}
UNITS = {
    "nominal_cd_nm": "nm", "exposure_dose_mj_cm2": "mJ/cm^2",
    "normalized_dose_pct": "%", "focus_um": "um",
    "coat_thickness_nm": "nm", "softbake_temp_c": "degC",
    "peb_temp_c": "degC", "develop_time_s": "s",
    "developer_concentration_pct": "%", "field_x": "normalized position",
    "field_y": "normalized position", "resist_line_cd_nm": "nm",
    "cdu_3sigma_nm": "nm", "ler_nm": "nm",
    "scum_probability": "probability [0,1]",
    "pattern_collapse_probability": "probability [0,1]",
    "defect_probability": "probability [0,1]",
}
# Broad audit bounds, not process specifications. They only flag values for review.
PHYSICAL_REVIEW_BOUNDS = {
    "nominal_cd_nm": (0, None), "exposure_dose_mj_cm2": (0, None),
    "normalized_dose_pct": (0, None), "focus_um": (-5, 5),
    "coat_thickness_nm": (0, None), "softbake_temp_c": (50, 200),
    "peb_temp_c": (50, 200), "develop_time_s": (0, None),
    "developer_concentration_pct": (0, 100), "field_x": (-1, 1),
    "field_y": (-1, 1), "resist_line_cd_nm": (0, None),
    "cdu_3sigma_nm": (0, None), "ler_nm": (0, None),
    "scum_probability": (0, 1), "pattern_collapse_probability": (0, 1),
    "defect_probability": (0, 1),
}


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def numeric_values(rows: list[dict], column: str, tone: str | None = None) -> list[float]:
    values = []
    for row in rows:
        if tone is not None and row["pr_tone"] != tone:
            continue
        if row[column] != "":
            try:
                values.append(float(row[column]))
            except ValueError:
                pass
    return values


def quantile(values: list[float], q: float) -> float:
    values = sorted(values)
    if not values:
        return math.nan
    pos = (len(values) - 1) * q
    low, high = math.floor(pos), math.ceil(pos)
    if low == high:
        return values[low]
    return values[low] * (high - pos) + values[high] * (pos - low)


def svg_bar_chart(path: Path, title: str, labels: list[str], values: list[float],
                  y_label: str, color: str = "#3973ac") -> None:
    width = max(900, 85 * len(labels) + 180)
    height, left, top, bottom = 560, 90, 70, 170
    chart_h = height - top - bottom
    max_v = max(values) if values else 1
    max_v = max(max_v, 1)
    bar_w = (width - left - 40) / max(len(labels), 1)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width/2}" y="32" text-anchor="middle" font-family="sans-serif" font-size="20">{title}</text>',
        f'<text x="18" y="{top+chart_h/2}" transform="rotate(-90 18 {top+chart_h/2})" text-anchor="middle" font-family="sans-serif" font-size="13">{y_label}</text>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+chart_h}" stroke="#333"/>',
        f'<line x1="{left}" y1="{top+chart_h}" x2="{width-30}" y2="{top+chart_h}" stroke="#333"/>',
    ]
    for index, (label, value) in enumerate(zip(labels, values)):
        x = left + index * bar_w + bar_w * 0.15
        h = chart_h * value / max_v
        y = top + chart_h - h
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w*0.7:.1f}" height="{h:.1f}" fill="{color}"/>')
        parts.append(f'<text x="{x+bar_w*0.35:.1f}" y="{y-6:.1f}" text-anchor="middle" font-family="sans-serif" font-size="11">{value:g}</text>')
        parts.append(f'<text x="{x+bar_w*0.35:.1f}" y="{top+chart_h+12}" transform="rotate(55 {x+bar_w*0.35:.1f} {top+chart_h+12})" text-anchor="start" font-family="sans-serif" font-size="10">{label}</text>')
    parts.append('</svg>')
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    with SOURCE.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = reader.fieldnames or []
    with SCHEMA.open(encoding="utf-8") as handle:
        expected = json.load(handle)["01_photo"]["variants"]["A"]
    features, targets = set(expected["features"]), set(expected["targets"])

    summary = [
        {"section": "dataset", "item": "source", "value": SOURCE.relative_to(ROOT).as_posix(), "unit_or_note": "read-only"},
        {"section": "dataset", "item": "rows", "value": len(rows), "unit_or_note": f"schema expected {expected['student_train_rows']}"},
        {"section": "dataset", "item": "columns", "value": len(columns), "unit_or_note": "including identifiers/features/targets"},
    ]
    for column in columns:
        if column in IDENTIFIERS:
            role = "identifier/context"
        elif column in features:
            role = "feature"
        elif column in targets:
            role = "target"
        else:
            role = "unclassified"
        summary.append({"section": "column", "item": column, "value": role,
                        "unit_or_note": UNITS.get(column, "category" if column in CATEGORICAL or column in IDENTIFIERS else "index")})
    for tone, count in sorted(Counter(r["pr_tone"] for r in rows).items()):
        summary.append({"section": "pr_tone_distribution", "item": tone or "MISSING", "value": count,
                        "unit_or_note": f"{100*count/len(rows):.2f}%"})
    write_csv(OUTPUT / "data_audit_summary.csv", ["section", "item", "value", "unit_or_note"], summary)

    missing = []
    for column in columns:
        count = sum(row[column] == "" for row in rows)
        missing.append({"column": column, "missing_count": count,
                        "missing_pct": f"{100*count/len(rows):.4f}"})
    write_csv(OUTPUT / "missing_summary.csv", ["column", "missing_count", "missing_pct"], missing)

    full_keys = [tuple(row[c] for c in columns) for row in rows]
    sample_counts = Counter(row["sample_id"] for row in rows)
    duplicate_rows = [
        {"check": "exact_full_row", "duplicate_groups": sum(v > 1 for v in Counter(full_keys).values()),
         "affected_rows": sum(v for v in Counter(full_keys).values() if v > 1), "extra_rows": sum(v - 1 for v in Counter(full_keys).values() if v > 1)},
        {"check": "sample_id", "duplicate_groups": sum(v > 1 for v in sample_counts.values()),
         "affected_rows": sum(v for v in sample_counts.values() if v > 1), "extra_rows": sum(v - 1 for v in sample_counts.values() if v > 1)},
    ]
    write_csv(OUTPUT / "duplicate_summary.csv", ["check", "duplicate_groups", "affected_rows", "extra_rows"], duplicate_rows)

    numeric = [c for c in columns if c not in IDENTIFIERS | CATEGORICAL | {"retained_pattern_source"}]
    bounds = {}
    for tone in sorted({r["pr_tone"] for r in rows}):
        for column in numeric:
            values = numeric_values(rows, column, tone)
            q1, q3 = quantile(values, .25), quantile(values, .75)
            iqr = q3 - q1
            bounds[(tone, column)] = (q1 - 1.5 * iqr, q3 + 1.5 * iqr)
    outliers = []
    for row in rows:
        tone = row["pr_tone"]
        for column in numeric:
            raw = row[column]
            if raw == "":
                continue
            try:
                value = float(raw)
            except ValueError:
                outliers.append({"sample_id": row["sample_id"], "lot_id": row["lot_id"], "tool_id": row["tool_id"], "sequence": row["sequence"], "pr_tone": tone, "column": column, "value": raw, "flag_type": "non_numeric", "review_reason": "numeric column could not be parsed", "action": "review_only_no_removal"})
                continue
            reasons = []
            low, high = bounds[(tone, column)]
            if value < low or value > high:
                reasons.append(f"tone_specific_IQR_1.5 [{low:.6g}, {high:.6g}]")
            physical = PHYSICAL_REVIEW_BOUNDS.get(column)
            if physical and ((physical[0] is not None and value < physical[0]) or (physical[1] is not None and value > physical[1])):
                reasons.append(f"broad_physical_review_range {physical}")
            if reasons:
                outliers.append({"sample_id": row["sample_id"], "lot_id": row["lot_id"], "tool_id": row["tool_id"], "sequence": row["sequence"], "pr_tone": tone, "column": column, "value": raw, "flag_type": "candidate", "review_reason": "; ".join(reasons), "action": "review_only_no_removal"})
    write_csv(OUTPUT / "outlier_review.csv", ["sample_id", "lot_id", "tool_id", "sequence", "pr_tone", "column", "value", "flag_type", "review_reason", "action"], outliers)

    group_rows = []
    for group_type, column in (("tool_id", "tool_id"), ("lot_id", "lot_id"), ("pr_tone", "pr_tone")):
        for value, count in sorted(Counter(r[column] for r in rows).items()):
            group_rows.append({"group_type": group_type, "group_value": value or "MISSING", "pr_tone": "ALL",
                               "count": count, "pct_of_dataset": f"{100*count/len(rows):.4f}"})
    for column in ("tool_id", "lot_id"):
        for (value, tone), count in sorted(Counter((r[column], r["pr_tone"]) for r in rows).items()):
            group_rows.append({"group_type": column, "group_value": value, "pr_tone": tone or "MISSING",
                               "count": count, "pct_of_dataset": f"{100*count/len(rows):.4f}"})
    write_csv(OUTPUT / "group_counts.csv", ["group_type", "group_value", "pr_tone", "count", "pct_of_dataset"], group_rows)

    svg_bar_chart(FIGURES / "missing_by_column.svg", "Missing values by column",
                  [r["column"] for r in missing], [float(r["missing_count"]) for r in missing], "Missing row count")
    tool_counts = sorted(Counter(r["tool_id"] for r in rows).items())
    tone_counts = sorted(Counter(r["pr_tone"] for r in rows).items())
    labels = [f"Tool {k}" for k, _ in tool_counts] + [f"Tone {k or 'MISSING'}" for k, _ in tone_counts]
    values = [v for _, v in tool_counts] + [v for _, v in tone_counts]
    svg_bar_chart(FIGURES / "tool_and_pr_tone_counts.svg", "Tool and PR tone representation",
                  labels, values, "Row count", "#c55a11")

    print(f"Audited {len(rows)} rows x {len(columns)} columns (source unchanged).")
    print(f"Outlier review flags: {len(outliers)}; output: {OUTPUT}")


if __name__ == "__main__":
    main()
