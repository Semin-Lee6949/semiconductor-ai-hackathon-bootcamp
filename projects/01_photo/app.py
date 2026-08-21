"""Reproducible Streamlit interface for Photo STEP 2-5 analyses."""

from pathlib import Path
import os
import sys

PROJECT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT / "outputs" / ".matplotlib-cache"))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.linear_model import LinearRegression


SCRIPTS = PROJECT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from baseline_regression import (  # noqa: E402
    CONTINUOUS,
    FLAGGED_SAMPLE_IDS,
    MODEL_FEATURES,
    TARGET,
    TrainOnlyFeatureBuilder,
    clean_category,
    detect_suspected_input_errors,
)
from model_validation import (  # noqa: E402
    data_quality_sensitivity,
    fit_and_score,
    lot_group_validation,
    repeated_split,
    repeated_validation,
)


DEFAULT_DATA = PROJECT / "data" / "A" / "train.csv"
BLIND_REQUIRED_COLUMNS = {"sample_id", "tool_id", "pr_tone", "normalized_dose_pct"}
REQUIRED_COLUMNS = {
    "sample_id", "lot_id", "tool_id", "pr_tone", "normalized_dose_pct",
    "focus_um", "coat_thickness_nm", "softbake_temp_c", "peb_temp_c",
    "develop_time_s", "developer_concentration_pct", TARGET,
}
NUMERIC_COLUMNS = [
    "normalized_dose_pct", "focus_um", "coat_thickness_nm", "softbake_temp_c",
    "peb_temp_c", "develop_time_s", "developer_concentration_pct", TARGET,
]
MODEL2 = MODEL_FEATURES["Model 2"]
PREDICTION_COLUMN = "predicted_resist_line_cd_nm"


@st.cache_data(show_spinner=False)
def load_default_data() -> pd.DataFrame:
    return pd.read_csv(DEFAULT_DATA)


@st.cache_data(show_spinner=False)
def prepare_analysis_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, int, dict]:
    frame = raw.copy()
    invalid_numeric = {}
    for column in NUMERIC_COLUMNS:
        before = frame[column].notna()
        converted = pd.to_numeric(frame[column], errors="coerce")
        invalid_numeric[column] = int((before & converted.isna()).sum())
        frame[column] = converted
    duplicate_mask = frame.duplicated(keep="first")
    frame = frame.loc[~duplicate_mask].copy().reset_index(drop=True)
    frame["pr_tone_group"] = clean_category(frame["pr_tone"])
    frame["tool_id_group"] = clean_category(frame["tool_id"])
    return frame, int(duplicate_mask.sum()), invalid_numeric


@st.cache_data(show_spinner=False)
def prepare_blind_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, int, dict]:
    """Prepare every uploaded row for prediction without deleting duplicates."""
    frame = raw.copy()
    invalid_numeric = {}
    for column in NUMERIC_COLUMNS:
        if column not in frame:
            continue
        before = frame[column].notna()
        converted = pd.to_numeric(frame[column], errors="coerce")
        invalid_numeric[column] = int((before & converted.isna()).sum())
        frame[column] = converted
    duplicate_count = int(frame.duplicated(keep="first").sum())
    frame["pr_tone_group"] = clean_category(frame["pr_tone"])
    frame["tool_id_group"] = clean_category(frame["tool_id"])
    return frame, duplicate_count, invalid_numeric


@st.cache_data(show_spinner=False)
def blind_predictions(frame: pd.DataFrame) -> np.ndarray:
    """Fit the fixed Model 2 on A/train only and predict all blind rows."""
    train_raw = load_default_data()
    train, _, _ = prepare_analysis_data(train_raw)
    train = train[train[TARGET].notna()].copy()
    builder = TrainOnlyFeatureBuilder().fit(train)
    train_x = builder.transform(train)[MODEL2]
    model = LinearRegression().fit(train_x, train[TARGET])

    prediction_frame = frame.copy()
    for column in CONTINUOUS:
        if column not in prediction_frame:
            prediction_frame[column] = np.nan
    prediction_x = builder.transform(prediction_frame)[MODEL2]
    return model.predict(prediction_x)


def render_blind_prediction(raw: pd.DataFrame) -> None:
    st.info("Blind Prediction Mode · Target CD가 없는 파일로 인식했습니다.")
    st.warning("""이 파일에는 실제 CD 정답이 없으므로 예측만 생성합니다.
실제 예측 성능은 정답 데이터가 제공된 후 평가할 수 있습니다.""")
    st.caption("모델 구조·변수·전처리 기준은 Holdout으로 수정하지 않으며, 기존 A/train 데이터에서만 학습합니다.")

    data, duplicate_count, invalid_numeric = prepare_blind_data(raw)
    flags = input_error_candidates(data)
    unexpected_tones = sorted(set(data["pr_tone_group"]) - {"POSITIVE", "NEGATIVE", "MISSING"})
    unexpected_tools = sorted(set(data["tool_id_group"]) - {"T01", "T02", "T03"})

    st.header("1. Blind Holdout Data Quality")
    metric_cols = st.columns(5)
    metric_cols[0].metric("행", f"{len(raw):,}")
    metric_cols[1].metric("열", f"{raw.shape[1]:,}")
    metric_cols[2].metric("결측 셀", f"{int(raw.isna().sum().sum()):,}")
    metric_cols[3].metric("완전 중복 추가행", f"{duplicate_count:,}")
    metric_cols[4].metric("입력 오류 후보 행", f"{flags['sample_id'].nunique() if not flags.empty else 0:,}")

    left, right = st.columns(2)
    with left:
        st.subheader("결측값")
        missing = raw.isna().sum().rename("missing_count").to_frame()
        missing["missing_pct"] = 100 * missing["missing_count"] / len(raw)
        st.dataframe(missing, width="stretch")
        st.subheader("PR tone 분포")
        st.dataframe(data["pr_tone_group"].value_counts(dropna=False).rename("count"), width="stretch")
    with right:
        st.subheader("Tool 분포")
        st.dataframe(data["tool_id_group"].value_counts(dropna=False).rename("count"), width="stretch")
        st.subheader("숫자 변환 실패")
        st.dataframe(pd.Series(invalid_numeric, name="invalid_non_numeric_count").to_frame(), width="stretch")

    st.subheader("입력/단위 오류 검토 후보")
    st.caption("검토 후보는 자동 수정하거나 예측에서 삭제하지 않습니다.")
    st.dataframe(flags if not flags.empty else pd.DataFrame({"결과": ["후보 없음"]}), width="stretch")

    if unexpected_tones or unexpected_tools:
        st.error(f"Model 2가 학습하지 않은 범주가 있어 예측을 중단합니다. PR tone={unexpected_tones}, Tool={unexpected_tools}.")
        return

    prediction = blind_predictions(data)
    if len(prediction) != len(raw):
        raise AssertionError("Every blind Holdout row must receive exactly one prediction")
    result = raw.copy()
    result[PREDICTION_COLUMN] = prediction

    st.header("2. Blind Holdout Prediction")
    st.dataframe(result[["sample_id", PREDICTION_COLUMN]], width="stretch", hide_index=True)
    st.download_button(
        "전체 prediction CSV 다운로드",
        data=result.to_csv(index=False).encode("utf-8-sig"),
        file_name="photo_holdout_predictions.csv",
        mime="text/csv",
    )
    st.caption(f"A/train으로 고정한 Model 2가 Holdout {len(result):,}행 모두에 예측을 생성했습니다. 성능 지표는 계산하지 않습니다.")


@st.cache_data(show_spinner=False)
def fixed_split_results(data: pd.DataFrame, flagged_ids: tuple[str, ...]):
    conditions = {
        "오류 의심값 포함": data,
        "오류 의심값 제외": data[~data["sample_id"].astype(str).isin(flagged_ids)].copy(),
    }
    rows = []
    detail = {}
    for label, frame in conditions.items():
        train, validation = repeated_split(frame, 42)
        result, prediction = fit_and_score(train, validation, MODEL2)
        rows.append({"조건": label, "전체 행": len(frame), "Train": len(train), "Validation": len(validation), **result})
        detail[label] = (train, validation, result, prediction)
    return pd.DataFrame(rows), detail


@st.cache_data(show_spinner=False)
def current_validation_results(data: pd.DataFrame, flagged_ids: tuple[str, ...]):
    repeated, repeated_summary, _ = repeated_validation(data)
    quality_detail, quality_summary = data_quality_sensitivity(data, flagged_ids)
    n_lots = data["lot_id"].nunique()
    lot = lot_group_validation(data, n_splits=min(8, n_lots))[0] if n_lots >= 2 else pd.DataFrame()
    return repeated, repeated_summary, quality_detail, quality_summary, lot


def input_error_candidates(frame: pd.DataFrame) -> pd.DataFrame:
    return detect_suspected_input_errors(frame)


def target_iqr_candidates(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for tone in ["POSITIVE", "NEGATIVE", "MISSING"]:
        group = frame[frame["pr_tone_group"].eq(tone)]
        values = group[TARGET].dropna()
        if len(values) < 4:
            continue
        q1, q3 = values.quantile([.25, .75]); iqr = q3 - q1
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        for _, row in group[(group[TARGET] < low) | (group[TARGET] > high)].iterrows():
            rows.append({"sample_id": row["sample_id"], "pr_tone": tone, "variable": TARGET,
                         "value": row[TARGET], "reason": f"tone-specific IQR review range [{low:.3f}, {high:.3f}]",
                         "action": "review_only; not automatically removed"})
    return pd.DataFrame(rows)


def scatter_by_tone(frame: pd.DataFrame, feature: str, quadratic=False):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    colors = {"POSITIVE": "#E45756", "NEGATIVE": "#4C78A8"}
    for ax, tone in zip(axes, ["POSITIVE", "NEGATIVE"]):
        part = frame[frame["pr_tone_group"].eq(tone)][[feature, TARGET]].dropna().sort_values(feature)
        ax.scatter(part[feature], part[TARGET], s=18, alpha=.45, color=colors[tone])
        degree = 2 if quadratic else 1
        if len(part) >= degree + 2 and part[feature].nunique() > degree:
            coefficients = np.polyfit(part[feature], part[TARGET], degree)
            grid = np.linspace(part[feature].min(), part[feature].max(), 150)
            ax.plot(grid, np.polyval(coefficients, grid), color=colors[tone], lw=2,
                    label="visual trend (not causal)")
            ax.legend(fontsize=8)
        ax.set(title=tone, xlabel=feature, ylabel=TARGET)
    fig.tight_layout()
    return fig


def grouped_cd_plot(frame: pd.DataFrame, column: str, title: str):
    labels = sorted(frame[column].dropna().astype(str).unique())
    values = [frame.loc[frame[column].astype(str).eq(label), TARGET].dropna() for label in labels]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.boxplot(values, tick_labels=labels, showfliers=True)
    ax.set(title=title, xlabel=column, ylabel=TARGET)
    fig.tight_layout()
    return fig


st.set_page_config(page_title="Photo Process AI Analysis", page_icon="🔬", layout="wide")
st.title("Photo 공정 CD 분석")
st.caption("STEP 2~5를 재현하는 해석 가능한 분석 앱 · Model 2 · 인과관계 추정 아님")

uploaded = st.file_uploader("분석할 CSV 업로드", type=["csv"], help="업로드하지 않으면 A/train.csv 예제를 사용합니다.")
try:
    raw = pd.read_csv(uploaded) if uploaded is not None else load_default_data()
except Exception as exc:
    st.error(f"CSV를 읽을 수 없습니다: {exc}")
    st.stop()

source_label = uploaded.name if uploaded is not None else "기본 예제: projects/01_photo/data/A/train.csv"
st.info(f"현재 데이터: {source_label}")
if TARGET not in raw.columns:
    missing_blind_columns = sorted(BLIND_REQUIRED_COLUMNS.difference(raw.columns))
    if missing_blind_columns:
        st.error("Target CD가 없고 Model 2 예측에 필요한 입력 컬럼도 부족하여 분석을 중단했습니다.")
        st.write("부족한 컬럼:", missing_blind_columns)
        st.stop()
    render_blind_prediction(raw)
    st.stop()

missing_columns = sorted(REQUIRED_COLUMNS.difference(raw.columns))
if missing_columns:
    st.error("필수 컬럼이 없어 분석을 중단했습니다.")
    st.write("부족한 컬럼:", missing_columns)
    st.stop()

data, removed_duplicates, invalid_numeric = prepare_analysis_data(raw)
target_missing = int(data[TARGET].isna().sum())
model_data = data[data[TARGET].notna()].copy()
unexpected_tones = sorted(set(model_data["pr_tone_group"]) - {"POSITIVE", "NEGATIVE", "MISSING"})
unexpected_tools = sorted(set(model_data["tool_id_group"]) - {"T01", "T02", "T03"})
flags = input_error_candidates(data)
flagged_ids = tuple(sorted(flags["sample_id"].astype(str).unique())) if not flags.empty else tuple()

st.header("1. Data Quality")
metric_cols = st.columns(5)
metric_cols[0].metric("원본 행", f"{len(raw):,}")
metric_cols[1].metric("열", f"{raw.shape[1]:,}")
metric_cols[2].metric("결측 셀", f"{int(raw.isna().sum().sum()):,}")
metric_cols[3].metric("완전 중복 추가행", f"{removed_duplicates:,}")
metric_cols[4].metric("입력 오류 후보 행", f"{len(flagged_ids):,}")

left, right = st.columns(2)
with left:
    st.subheader("결측값")
    missing = raw.isna().sum().rename("missing_count").to_frame()
    missing["missing_pct"] = 100 * missing["missing_count"] / len(raw)
    st.dataframe(missing, width="stretch")
    st.subheader("PR tone 분포")
    st.dataframe(clean_category(raw["pr_tone"]).value_counts(dropna=False).rename("count"), width="stretch")
with right:
    st.subheader("Tool 분포")
    st.dataframe(clean_category(raw["tool_id"]).value_counts(dropna=False).rename("count"), width="stretch")
    st.subheader("숫자 변환 실패")
    st.dataframe(pd.Series(invalid_numeric, name="invalid_non_numeric_count").to_frame(), width="stretch")

st.subheader("이상치·입력 오류 검토 후보")
st.caption("검토 규칙은 행을 자동 수정하거나 삭제하지 않습니다. CD 후보는 tone별 IQR, 입력 후보는 STEP 2에서 확인한 넓은 물리·소수점 규칙입니다.")
candidate_tabs = st.tabs(["입력/단위 오류 후보", "CD IQR 후보"])
with candidate_tabs[0]:
    st.dataframe(flags if not flags.empty else pd.DataFrame({"결과": ["후보 없음"]}), width="stretch")
with candidate_tabs[1]:
    cd_candidates = target_iqr_candidates(data)
    st.dataframe(cd_candidates if not cd_candidates.empty else pd.DataFrame({"결과": ["후보 없음"]}), width="stretch")

if target_missing:
    st.warning(f"Target 결측 {target_missing}행은 성능 계산이 불가능하여 모델링에서만 제외됩니다. 원본 데이터는 변경하지 않습니다.")
if unexpected_tones or unexpected_tools:
    st.error(f"Model 2가 학습하지 않은 범주가 있습니다. PR tone={unexpected_tones}, Tool={unexpected_tools}. Data Quality와 EDA만 표시합니다.")
    model_ready = False
else:
    model_ready = len(model_data) >= 20 and model_data["pr_tone_group"].nunique() >= 2
    if not model_ready:
        st.error("Model 2 검증에 필요한 유효 행 또는 PR tone 종류가 부족합니다. Data Quality와 EDA만 표시합니다.")

st.header("2. 데이터 품질 민감도")
selection = st.radio("모델에 적용할 조건", ["오류 의심값 포함", "오류 의심값 제외"], horizontal=True)
if flags.empty:
    st.info("현재 데이터에는 정의된 입력/단위 오류 후보가 없어 두 조건의 데이터가 같습니다.")

if model_ready:
    sensitivity, fixed_details = fixed_split_results(model_data, flagged_ids)
    display_sensitivity = sensitivity.rename(columns={
        "validation_r2": "Validation R²", "validation_rmse_nm": "RMSE (nm)",
        "validation_mae_nm": "MAE (nm)",
        "positive_dose_slope_nm_per_pct_point": "Positive dose slope",
        "negative_dose_slope_nm_per_pct_point": "Negative dose slope",
    })
    st.dataframe(display_sensitivity, width="stretch", hide_index=True)
    if len(flagged_ids):
        st.caption("차이는 입력 오류 후보가 Train의 기울기 추정 또는 Validation의 큰 오차에 미치는 영향 때문에 발생할 수 있습니다. 자동 보정이나 인과 해석은 하지 않습니다.")

st.header("3. EDA")
eda_tabs = st.tabs(["Dose vs CD", "Focus vs CD", "Tool별 CD", "PR tone별 CD"])
with eda_tabs[0]:
    st.pyplot(scatter_by_tone(data, "normalized_dose_pct"), width="stretch")
with eda_tabs[1]:
    st.pyplot(scatter_by_tone(data, "focus_um", quadratic=True), width="stretch")
with eda_tabs[2]:
    st.pyplot(grouped_cd_plot(data, "tool_id_group", "CD by Tool"), width="stretch")
with eda_tabs[3]:
    st.pyplot(grouped_cd_plot(data, "pr_tone_group", "CD by PR tone"), width="stretch")
st.caption("관계선은 시각적 경향이며 원인이나 공정 효과를 확정하지 않습니다. PR tone 결측은 MISSING으로 유지하되 Positive/Negative 관계선에는 포함하지 않습니다.")

st.header("4. 기준모델: Model 2")
if model_ready:
    _, validation_frame, selected_result, selected_prediction = fixed_details[selection]
    cards = st.columns(3)
    cards[0].metric("Validation R²", f"{selected_result['validation_r2']:.3f}")
    cards[1].metric("RMSE", f"{selected_result['validation_rmse_nm']:.3f} nm")
    cards[2].metric("MAE", f"{selected_result['validation_mae_nm']:.3f} nm")
    pos_slope = selected_result["positive_dose_slope_nm_per_pct_point"]
    neg_slope = selected_result["negative_dose_slope_nm_per_pct_point"]
    if pos_slope < 0:
        st.success(f"Positive PR: Dose가 증가할수록 CD 감소 경향 ({pos_slope:+.3f} nm/%p)")
    else:
        st.warning(f"Positive PR: 현재 데이터에서는 예상과 다른 방향 ({pos_slope:+.3f} nm/%p)")
    if neg_slope > 0:
        st.success(f"Negative PR: Dose가 증가할수록 CD 증가 경향 ({neg_slope:+.3f} nm/%p)")
    else:
        st.warning(f"Negative PR: 현재 데이터에서는 예상과 다른 방향 ({neg_slope:+.3f} nm/%p)")
    st.caption("계수는 PR tone과 Tool을 함께 고려한 관찰적 회귀 관계이며 인과효과가 아닙니다.")

st.header("5. 검증 결과")
if model_ready:
    with st.spinner("30회 반복 분할과 Lot 검증을 계산하는 중입니다..."):
        repeated, repeated_summary, quality_detail, quality_summary, lot_results = current_validation_results(model_data, flagged_ids)
    model2_repeated = repeated[repeated["model"].eq("Model 2")]
    val_tabs = st.tabs(["30회 R²", "오류 후보 포함/제외", "Lot 검증", "Dose 방향 안정성"])
    with val_tabs[0]:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(model2_repeated["validation_r2"], bins=10, color="#4C78A8", edgecolor="white")
        ax.axvline(model2_repeated["validation_r2"].mean(), color="#E45756", ls="--", label="mean")
        ax.set(xlabel="Validation R²", ylabel="Count", title="30 repeated splits"); ax.legend()
        st.pyplot(fig, width="stretch")
        st.dataframe(repeated_summary[repeated_summary["model"].eq("Model 2")], width="stretch", hide_index=True)
    with val_tabs[1]:
        metric_rows = quality_summary[quality_summary["metric"].isin(["validation_r2", "validation_rmse_nm", "validation_mae_nm"])]
        st.dataframe(metric_rows, width="stretch", hide_index=True)
    with val_tabs[2]:
        if lot_results.empty:
            st.warning("Lot 종류가 2개 미만이라 Lot Group Validation을 실행할 수 없습니다.")
        else:
            fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
            for ax, column, label in zip(axes, ["validation_r2", "validation_rmse_nm", "validation_mae_nm"], ["R²", "RMSE", "MAE"]):
                ax.bar(lot_results["fold"].astype(str), lot_results[column]); ax.set(title=label, xlabel="Fold")
            fig.tight_layout(); st.pyplot(fig, width="stretch")
            st.dataframe(lot_results, width="stretch", hide_index=True)
    with val_tabs[3]:
        positive_ok = int((model2_repeated["positive_dose_slope_nm_per_pct_point"] < 0).sum())
        negative_ok = int((model2_repeated["negative_dose_slope_nm_per_pct_point"] > 0).sum())
        cols = st.columns(2)
        cols[0].metric("Positive 음(-) 방향", f"{positive_ok}/{len(model2_repeated)}회")
        cols[1].metric("Negative 양(+) 방향", f"{negative_ok}/{len(model2_repeated)}회")
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.boxplot([model2_repeated["positive_dose_slope_nm_per_pct_point"],
                    model2_repeated["negative_dose_slope_nm_per_pct_point"]], tick_labels=["POSITIVE", "NEGATIVE"])
        ax.axhline(0, color="black", ls="--"); ax.set(ylabel="nm CD per dose %p")
        st.pyplot(fig, width="stretch")

st.header("6. 분석 한계")
st.warning("""
- 입력 오류에 모델 성능이 민감합니다.
- 단일 관찰 데이터이므로 인과관계를 확정할 수 없습니다.
- 일부 Lot/CD 극단값에서 예측오차가 큽니다.
- Random Forest 등 복잡한 모델은 아직 사용하지 않았습니다.
- Holdout은 현재 분석에 사용하지 않았습니다.
""")
st.caption("업로드 데이터와 기본 예제는 메모리에서만 분석하며 원본 CSV를 수정하지 않습니다.")
