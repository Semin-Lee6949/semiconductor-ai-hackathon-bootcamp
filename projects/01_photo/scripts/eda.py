"""STEP 3: hypothesis-first EDA for Photo process A/train.csv only.

No holdout data, regression model, or machine-learning model is used.  Suspected
entry/unit errors are retained in the primary analysis and excluded only in a
clearly labelled sensitivity analysis for the affected variable.
"""

import os
from pathlib import Path

# Keep Matplotlib's cache inside the writable project tree for reproducible runs.
_PROJECT_FOR_CACHE = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(_PROJECT_FOR_CACHE / "outputs" / ".matplotlib-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
INPUT = PROJECT / "data" / "A" / "train.csv"
AUDIT_FLAGS = PROJECT / "outputs" / "data_audit" / "outlier_review.csv"
OUTPUT = PROJECT / "outputs" / "eda"
FIGURES = OUTPUT / "figures"
TARGET = "resist_line_cd_nm"
FEATURES = [
    "normalized_dose_pct",
    "focus_um",
    "coat_thickness_nm",
    "softbake_temp_c",
    "peb_temp_c",
    "develop_time_s",
    "developer_concentration_pct",
]
TONES = ["POSITIVE", "NEGATIVE"]

# Written before inspecting feature-CD relationships. Directions intentionally
# remain uncertain where PR chemistry, retained pattern, or operating window matters.
HYPOTHESES = [
    ("normalized_dose_pct", "기준 dose 대비 실제 노광량의 비율", "노광량은 PR 반응·용해도와 잔존 선폭을 바꿀 수 있음", "Positive: 음(-), Negative: 양(+)", "retained pattern 정의, dose 범위, focus·PEB 및 tone별 chemistry가 방향을 바꿀 수 있음"),
    ("focus_um", "최적 초점면 대비 defocus", "영상 contrast와 aerial-image 선폭이 focus offset에 따라 달라질 수 있음", "확인 필요", "0을 중심으로 한 비선형·비대칭 관계일 수 있고 tool/field 및 dose와 교란될 수 있음"),
    ("coat_thickness_nm", "도포 후 PR 막 두께", "흡광·standing wave·현상 경로 길이가 유효 CD에 관련될 수 있음", "확인 필요", "두께 범위 내 영향이 작거나 bake/tool/PR 조성과 함께 변한 결과일 수 있음"),
    ("softbake_temp_c", "노광 전 용매 제거를 위한 softbake 온도", "잔류 용매와 감도·막 특성을 변화시켜 CD와 관련될 수 있음", "확인 필요", "시간 정보가 없고 좁은 공정창에서는 관계가 약하거나 PEB·두께와 교란될 수 있음"),
    ("peb_temp_c", "노광 후 반응 확산을 진행시키는 PEB 온도", "산 확산·가교 등 반응 범위가 바뀌어 선폭과 관련될 수 있음", "확인 필요", "tone/chemistry에 따라 방향이 다르고 dose·PEB 시간·tool과 교란될 수 있음"),
    ("develop_time_s", "현상액 접촉 시간", "용해 진행과 잔막/패턴 침식 정도가 잔존 CD에 관련될 수 있음", "확인 필요", "현상 포화, 농도·온도·tone 및 retained pattern 정의에 따라 방향이 달라질 수 있음"),
    ("developer_concentration_pct", "현상액 유효 농도", "용해 속도와 선택비 변화가 잔존 CD에 관련될 수 있음", "확인 필요", "변동 범위가 좁거나 develop time·온도·PR chemistry와 교란될 수 있음"),
]

# Obvious decimal/unit-entry suspects identified in the prior audit and confirmed
# by comparison with the variable's operating range. IQR-only candidates are not excluded.
SENSITIVITY_FLAGS = {
    ("S00160", "focus_um"): "0.933515 um; tone 내 대부분 범위와 크게 달라 축 왜곡 가능, 소수점 입력 의심",
    ("S00748", "coat_thickness_nm"): "9.465512 nm; 통상 관측 군집(~70-136 nm) 대비 약 1/10, 단위/소수점 입력 의심",
    ("S00475", "softbake_temp_c"): "9.979035 C; 감사 물리 검토 하한 50 C 미만, 소수점 입력 의심",
    ("S00634", "developer_concentration_pct"): "12.21005%; 통상 관측 군집(~2.2-2.6%) 대비 약 5배, 소수점 입력 의심",
    ("S00636", "normalized_dose_pct"): "9.908105%; 같은 행 exposure dose 99.081051과 10배 차이, 소수점 입력 의심",
}


def tone_label(series: pd.Series) -> pd.Series:
    cleaned = series.astype("string").str.strip().str.upper()
    return cleaned.where(cleaned.notna() & cleaned.ne(""), "MISSING")


def safe_corr(frame: pd.DataFrame, feature: str) -> tuple[int, float]:
    pair = frame[[feature, TARGET]].dropna()
    if len(pair) < 2 or pair[feature].nunique() < 2 or pair[TARGET].nunique() < 2:
        return len(pair), np.nan
    return len(pair), pair[feature].corr(pair[TARGET], method="pearson")


def save_hypotheses() -> None:
    pd.DataFrame(HYPOTHESES, columns=[
        "variable", "photo_process_meaning", "reason_expected_to_relate_to_cd",
        "expected_direction_pre_eda", "counter_hypothesis_or_confounder",
    ]).to_csv(OUTPUT / "hypothesis_table.csv", index=False, encoding="utf-8-sig")


def save_flag_log(df: pd.DataFrame) -> None:
    rows = []
    for (sample_id, variable), reason in SENSITIVITY_FLAGS.items():
        hit = df.loc[df["sample_id"].eq(sample_id)]
        if len(hit) != 1:
            raise ValueError(f"Expected one row for {sample_id}, found {len(hit)}")
        row = hit.iloc[0]
        rows.append({
            "sample_id": sample_id, "lot_id": row["lot_id"], "tool_id": row["tool_id"],
            "pr_tone": row["pr_tone_group"], "variable": variable, "value": row[variable],
            "status": "flagged_and_excluded_only_for_affected_variable_sensitivity",
            "reason": reason,
            "primary_analysis_action": "retained",
            "sensitivity_analysis_action": f"excluded only from {variable} plot/correlation labelled flagged_excluded",
        })
    pd.DataFrame(rows).to_csv(OUTPUT / "excluded_or_flagged_rows.csv", index=False, encoding="utf-8-sig")


def summaries(df: pd.DataFrame) -> None:
    rows = []
    for tone in ["ALL", "POSITIVE", "NEGATIVE", "MISSING"]:
        part = df if tone == "ALL" else df[df["pr_tone_group"].eq(tone)]
        s = part[TARGET]
        rows.append({"pr_tone": tone, "n_rows": len(part), "cd_count": s.count(),
                     "cd_mean_nm": s.mean(), "cd_std_nm": s.std(), "cd_min_nm": s.min(),
                     "cd_q25_nm": s.quantile(.25), "cd_median_nm": s.median(),
                     "cd_q75_nm": s.quantile(.75), "cd_max_nm": s.max()})
    pd.DataFrame(rows).to_csv(OUTPUT / "summary_by_pr_tone.csv", index=False, encoding="utf-8-sig")

    tool = (df.groupby(["tool_id", "pr_tone_group"], dropna=False)[TARGET]
              .agg(n="size", mean_cd_nm="mean", std_cd_nm="std", median_cd_nm="median",
                   min_cd_nm="min", max_cd_nm="max").reset_index())
    counts = df.groupby("tool_id").size().rename("tool_total_n")
    tool = tool.join(counts, on="tool_id")
    tool["tool_pct_of_dataset"] = 100 * tool["tool_total_n"] / len(df)
    tool.to_csv(OUTPUT / "summary_by_tool_and_pr_tone.csv", index=False, encoding="utf-8-sig")


def correlations(df: pd.DataFrame) -> None:
    rows = []
    for tone in TONES:
        part = df[df["pr_tone_group"].eq(tone)]
        for feature in FEATURES:
            n, r = safe_corr(part, feature)
            rows.append({"pr_tone": tone, "variable": feature, "analysis": "original_including_flagged",
                         "n_complete_pairs": n, "pearson_r": r})
            flagged_ids = [sid for sid, var in SENSITIVITY_FLAGS if var == feature]
            clean = part[~part["sample_id"].isin(flagged_ids)]
            n2, r2 = safe_corr(clean, feature)
            rows.append({"pr_tone": tone, "variable": feature, "analysis": "flagged_excluded_sensitivity",
                         "n_complete_pairs": n2, "pearson_r": r2})
    pd.DataFrame(rows).to_csv(OUTPUT / "correlation_by_pr_tone.csv", index=False, encoding="utf-8-sig")

    by_tool = []
    for tone in TONES:
        for tool_id, part in df[df["pr_tone_group"].eq(tone)].groupby("tool_id"):
            for feature in FEATURES:
                n, r = safe_corr(part, feature)
                by_tool.append({"pr_tone": tone, "tool_id": tool_id, "variable": feature,
                                "n_complete_pairs": n, "pearson_r": r})
    pd.DataFrame(by_tool).to_csv(OUTPUT / "correlation_by_tool_and_pr_tone.csv", index=False, encoding="utf-8-sig")


def distribution_figures(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(df[TARGET], bins=30, color="#4C78A8", alpha=.8, edgecolor="white")
    ax.set(title="Resist line CD distribution (all rows)", xlabel="resist_line_cd_nm", ylabel="Count")
    fig.tight_layout(); fig.savefig(FIGURES / "cd_distribution_all.png", dpi=160); plt.close(fig)

    groups = [df.loc[df["pr_tone_group"].eq(t), TARGET] for t in ["POSITIVE", "NEGATIVE", "MISSING"]]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot(groups, tick_labels=["POSITIVE", "NEGATIVE", "MISSING"], showfliers=True)
    ax.set(title="CD distribution by PR tone", ylabel="resist_line_cd_nm")
    fig.tight_layout(); fig.savefig(FIGURES / "cd_distribution_by_pr_tone.png", dpi=160); plt.close(fig)

    order = sorted(df["tool_id"].dropna().unique())
    fig, ax = plt.subplots(figsize=(9, 5))
    positions, labels, values = [], [], []
    pos = 1
    for tool in order:
        for tone in TONES:
            values.append(df.loc[df["tool_id"].eq(tool) & df["pr_tone_group"].eq(tone), TARGET])
            positions.append(pos); labels.append(f"{tool}\n{tone[:3]}"); pos += 1
        pos += .5
    ax.boxplot(values, positions=positions, widths=.7, tick_labels=labels, showfliers=True)
    ax.set(title="CD by tool and PR tone (MISSING tone excluded)", ylabel="resist_line_cd_nm")
    fig.tight_layout(); fig.savefig(FIGURES / "cd_distribution_by_tool_and_pr_tone.png", dpi=160); plt.close(fig)


def add_trend(ax, x: pd.Series, y: pd.Series, color: str) -> None:
    pair = pd.DataFrame({"x": x, "y": y}).dropna().sort_values("x")
    if len(pair) >= 3 and pair["x"].nunique() >= 3:
        grid = np.linspace(pair["x"].min(), pair["x"].max(), 150)
        coef = np.polyfit(pair["x"], pair["y"], deg=2)
        ax.plot(grid, np.polyval(coef, grid), color=color, linewidth=2,
                label="quadratic visual guide (not causal)")


def scatter_figures(df: pd.DataFrame) -> None:
    colors = {"POSITIVE": "#E45756", "NEGATIVE": "#4C78A8"}
    for feature in FEATURES:
        flagged_ids = [sid for sid, var in SENSITIVITY_FLAGS if var == feature]
        for analysis, frame in [
            ("original_including_flagged", df),
            ("flagged_excluded_sensitivity", df[~df["sample_id"].isin(flagged_ids)]),
        ]:
            fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
            for ax, tone in zip(axes, TONES):
                part = frame[frame["pr_tone_group"].eq(tone)]
                ax.scatter(part[feature], part[TARGET], s=18, alpha=.5, color=colors[tone])
                add_trend(ax, part[feature], part[TARGET], colors[tone])
                ax.set(title=f"{tone} (n={len(part)})", xlabel=feature, ylabel=TARGET)
                ax.legend(loc="best", fontsize=8)
            note = "Original values retained" if analysis.startswith("original") else f"Sensitivity: excluded {', '.join(flagged_ids) or 'none'}"
            fig.suptitle(f"{feature} vs CD — {note}")
            fig.tight_layout(); fig.savefig(FIGURES / f"scatter_{feature}_{analysis}.png", dpi=160); plt.close(fig)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True); FIGURES.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    required = {"sample_id", "lot_id", "tool_id", "pr_tone", TARGET, *FEATURES}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if len(df) != 805:
        raise ValueError(f"Expected audited 805 rows, found {len(df)}")
    df["pr_tone_group"] = tone_label(df["pr_tone"])
    unexpected = set(df["pr_tone_group"].unique()).difference({*TONES, "MISSING"})
    if unexpected:
        raise ValueError(f"Unexpected pr_tone values: {unexpected}")
    save_hypotheses(); save_flag_log(df); summaries(df); correlations(df)
    distribution_figures(df); scatter_figures(df)
    print(f"EDA complete: {len(df)} train rows; holdout not read; outputs={OUTPUT}")


if __name__ == "__main__":
    main()
