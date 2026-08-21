"""Reproducible Streamlit interface for Photo STEP 2-5 analyses."""

from pathlib import Path
import html
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


def apply_portfolio_theme() -> None:
    st.markdown("""
    <style>
    :root {
        --navy-950: #071a2b;
        --navy-900: #0b2740;
        --navy-800: #123b5d;
        --navy-700: #1d557d;
        --blue-100: #e6f0f7;
        --paper: #f3f6f9;
        --card: #ffffff;
        --ink: #132536;
        --muted: #5f7180;
        --gold: #c99a45;
        --line: #d7e1e8;
    }
    .stApp { background: linear-gradient(180deg, #dce8f1 0, var(--paper) 26rem); color: var(--ink); }
    [data-testid="stAppViewContainer"] > .main { background: transparent; }
    .block-container { max-width: 1180px; padding-top: 2.2rem; padding-bottom: 5rem; }
    h1, h2, h3 { color: var(--navy-900) !important; letter-spacing: -0.025em; }
    h1 { font-weight: 850 !important; }
    p, li, label, [data-testid="stCaptionContainer"] { color: var(--ink); }
    [data-testid="stMetric"] {
        background: rgba(255,255,255,.94); border: 1px solid var(--line);
        border-top: 4px solid var(--navy-700); border-radius: 12px;
        padding: 1rem 1.1rem; box-shadow: 0 8px 22px rgba(7,26,43,.07);
    }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    [data-testid="stMetricValue"] { color: var(--navy-900); }
    [data-testid="stFileUploader"] section, [data-testid="stDataFrame"] {
        border-color: var(--line); border-radius: 12px;
    }
    div[data-baseweb="tab-list"] { gap: .4rem; }
    button[data-baseweb="tab"] { background: #e6eef4; border-radius: 9px 9px 0 0; }
    button[data-baseweb="tab"][aria-selected="true"] { background: white; color: var(--navy-800); }
    .portfolio-hero {
        padding: 2.1rem 2.3rem; margin: 0 0 1.35rem;
        border-radius: 18px; color: white;
        background: linear-gradient(125deg, var(--navy-950), var(--navy-800));
        box-shadow: 0 18px 42px rgba(7,26,43,.22);
    }
    .portfolio-hero .eyebrow { color: #8ecbe4; font-size: .76rem; font-weight: 800; letter-spacing: .15em; }
    .portfolio-hero h1 { color: white !important; margin: .35rem 0 .65rem; font-size: clamp(2rem,4vw,3.25rem); }
    .portfolio-hero p { color: #dbe8f0; margin: 0; max-width: 820px; }
    .guide-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:.8rem; margin:1rem 0 1.8rem; }
    .guide-card { background:rgba(255,255,255,.95); border:1px solid var(--line); border-radius:12px; padding:1rem; box-shadow:0 8px 20px rgba(7,26,43,.06); }
    .guide-card b { display:block; color:var(--navy-800); margin-bottom:.35rem; }
    .guide-card span { display:block; color:var(--muted); font-size:.86rem; line-height:1.55; }
    .guide-card.problem { border-top:4px solid #bb624f; }
    .guide-card.hypothesis { border-top:4px solid var(--gold); }
    .guide-card.alternative { border-top:4px solid #607f96; }
    .guide-card.decision { border-top:4px solid #368175; }
    .section-guide { background:#fff; border-left:5px solid var(--navy-700); border-radius:0 12px 12px 0; padding:1rem 1.15rem; margin:.4rem 0 1rem; box-shadow:0 6px 18px rgba(7,26,43,.05); }
    .section-guide strong { color:var(--navy-800); }
    .section-guide span { color:var(--muted); }
    .interpret-card { background:#f8fbfd; border:1px solid var(--line); border-radius:12px; padding:1rem 1.15rem; margin:.8rem 0 1rem; }
    .interpret-card .label { color:var(--gold); font-size:.76rem; font-weight:850; letter-spacing:.08em; }
    .interpret-card h4 { color:var(--navy-900); margin:.25rem 0 .45rem; font-size:1.02rem; }
    .interpret-card p { color:var(--muted); margin:0; line-height:1.65; }
    .direction-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:.8rem; margin:1rem 0; }
    .direction-card { background:#fff; border:1px solid var(--line); border-radius:12px; padding:1rem; }
    .direction-card b { color:var(--navy-800); display:block; margin-bottom:.3rem; }
    .direction-card span { color:var(--muted); font-size:.85rem; line-height:1.55; }
    @media(max-width:800px) { .guide-grid { grid-template-columns:1fr 1fr; } .portfolio-hero { padding:1.5rem; } }
    @media(max-width:800px) { .direction-grid { grid-template-columns:1fr; } }
    @media(max-width:520px) { .guide-grid { grid-template-columns:1fr; } }
    </style>
    """, unsafe_allow_html=True)


def section_guide(title: str, message: str) -> None:
    st.markdown(
        f'<div class="section-guide"><strong>{title}</strong><br><span>{message}</span></div>',
        unsafe_allow_html=True,
    )


def interpretation_card(title: str, message: str, label: str = "CURRENT DATA INTERPRETATION") -> None:
    st.markdown(
        f'<div class="interpret-card"><div class="label">{html.escape(label)}</div>'
        f'<h4>{html.escape(title)}</h4><p>{html.escape(message)}</p></div>',
        unsafe_allow_html=True,
    )


def tone_correlation(frame: pd.DataFrame, feature: str, tone: str) -> tuple[int, float]:
    pair = frame.loc[frame["pr_tone_group"].eq(tone), [feature, TARGET]].dropna()
    if len(pair) < 2 or pair[feature].nunique() < 2:
        return len(pair), np.nan
    return len(pair), float(pair[feature].corr(pair[TARGET]))


def correlation_direction(value: float) -> str:
    if np.isnan(value):
        return "판단할 유효 표본이 부족합니다"
    if abs(value) < 0.2:
        return "뚜렷한 선형 방향이 약합니다"
    return "증가할수록 CD가 감소하는 경향" if value < 0 else "증가할수록 CD가 증가하는 경향"


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
    section_guide(
        "먼저 확인할 문제 신호",
        "결측·중복·입력 단위 오류와 PR tone/Tool 편중은 예측값을 흔들 수 있습니다. 후보를 자동 삭제하지 않고 원자료 확인 대상으로 표시합니다.",
    )
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
    section_guide(
        "이 숫자는 무엇인가요?",
        "A/train에서 이미 고정한 관계를 새 행에 적용한 예상 CD입니다. 실제 정답이 없으므로 좋은 예측인지 평가한 점수는 아닙니다.",
    )
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
apply_portfolio_theme()
st.markdown("""
<div class="portfolio-hero">
  <div class="eyebrow">PHOTO PROCESS · EXPLAINABLE AI WORKFLOW</div>
  <h1>Photo 공정 CD 분석</h1>
  <p>데이터 품질을 먼저 의심하고, PR tone별 가설을 분리한 뒤, 단순 모델의 성능과 관계 방향이 반복해서 유지되는지 확인합니다.</p>
</div>
<div class="guide-grid">
  <div class="guide-card problem"><b>⚠ 이게 문제일 수 있어요</b><span>CD 편차가 dose뿐 아니라 Tool 편중, Lot 차이, 입력 오류 때문에 커져 보일 수 있습니다.</span></div>
  <div class="guide-card hypothesis"><b>◆ 핵심 가설</b><span>Normalized dose와 CD의 관계 방향은 Positive/Negative PR에서 다를 가능성이 있습니다.</span></div>
  <div class="guide-card alternative"><b>↔ 이런 것도 영향을 줄 수 있어요</b><span>Focus의 비선형 반응, Tool condition, calibration, 누락된 recipe 조건을 대안 설명으로 검토합니다.</span></div>
  <div class="guide-card decision"><b>✓ 그래서 이렇게 판단해요</b><span>단일 R²보다 반복검증·Lot 검증·데이터 품질 민감도를 함께 보고 다음 확인 순서를 정합니다.</span></div>
</div>
""", unsafe_allow_html=True)
st.caption("STEP 2~5를 재현하는 해석 가능한 분석 앱 · 관찰적 관계이며 인과관계 추정 아님")

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
section_guide(
    "왜 품질부터 보나요?",
    "몇 개의 소수점·단위 오류 후보만으로도 Validation 성능과 안정성이 크게 달라질 수 있습니다. 낮은 점수를 보고 복잡한 AI를 추가하기 전에 입력을 먼저 확인합니다.",
)
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
section_guide(
    "여기서 묻는 질문",
    "오류 의심값을 포함하거나 검토용으로 제외했을 때 결론이 얼마나 달라질까요? 성능 개선은 오류 확정이 아니라 민감하다는 신호입니다.",
)
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
st.markdown("""
<div class="guide-grid">
  <div class="guide-card hypothesis"><b>H1 · Dose × PR tone</b><span>tone별 dose–CD 방향이 다르게 관찰될 가능성을 확인합니다. 두 tone을 한 관계로 합치지 않습니다.</span></div>
  <div class="guide-card hypothesis"><b>H2 · Focus</b><span>선형 상관이 약해도 0 주변의 비선형·비대칭 관계일 가능성을 남겨둡니다.</span></div>
  <div class="guide-card alternative"><b>대안 · Tool / Lot</b><span>관찰된 CD 차이가 Tool 구성이나 Lot별 조건 차이에서 나타났을 가능성을 함께 봅니다.</span></div>
  <div class="guide-card problem"><b>반증 · 입력 오류</b><span>특정 극단값을 제외했을 때만 관계가 보인다면 원자료 확인 전에는 강한 결론을 보류합니다.</span></div>
</div>
""", unsafe_allow_html=True)
eda_tabs = st.tabs(["Dose vs CD", "Focus vs CD", "Tool별 CD", "PR tone별 CD"])
with eda_tabs[0]:
    st.pyplot(scatter_by_tone(data, "normalized_dose_pct"), width="stretch")
    pos_n, pos_r = tone_correlation(data, "normalized_dose_pct", "POSITIVE")
    neg_n, neg_r = tone_correlation(data, "normalized_dose_pct", "NEGATIVE")
    interpretation_card(
        "PR tone을 합치지 말고 방향을 따로 읽어야 합니다",
        f"Positive는 n={pos_n}, Pearson r={pos_r:+.3f}로 {correlation_direction(pos_r)}입니다. "
        f"Negative는 n={neg_n}, r={neg_r:+.3f}로 {correlation_direction(neg_r)}입니다. "
        "두 방향 차이는 관찰적 관계이며 dose 변경의 인과효과를 뜻하지 않습니다.",
    )
with eda_tabs[1]:
    st.pyplot(scatter_by_tone(data, "focus_um", quadratic=True), width="stretch")
    pos_focus_n, pos_focus_r = tone_correlation(data, "focus_um", "POSITIVE")
    neg_focus_n, neg_focus_r = tone_correlation(data, "focus_um", "NEGATIVE")
    interpretation_card(
        "선형 상관이 약해도 Focus 영향이 없다고 단정하지 않습니다",
        f"Positive는 n={pos_focus_n}, r={pos_focus_r:+.3f}, Negative는 n={neg_focus_n}, r={neg_focus_r:+.3f}입니다. "
        "현재 범위의 직선 관계는 약할 수 있지만 최적 focus 주변의 곡률·비대칭, dose 및 Tool과의 상호작용 가능성은 별도 DOE로 확인해야 합니다.",
    )
with eda_tabs[2]:
    st.pyplot(grouped_cd_plot(data, "tool_id_group", "CD by Tool"), width="stretch")
    tool_summary = data.groupby("tool_id_group")[TARGET].agg(["count", "mean"]).dropna().sort_values("mean")
    if len(tool_summary):
        low_tool, high_tool = str(tool_summary.index[0]), str(tool_summary.index[-1])
        low_mean, high_mean = float(tool_summary.iloc[0]["mean"]), float(tool_summary.iloc[-1]["mean"])
        interpretation_card(
            "Tool별 CD level 차이는 중요한 대안 설명입니다",
            f"현재 데이터의 평균 CD는 {low_tool} {low_mean:.2f} nm에서 {high_tool} {high_mean:.2f} nm 범위입니다. "
            "이는 Tool 자체 효과의 증명이 아니며 calibration, condition, Lot·recipe 배치 차이가 함께 반영됐을 가능성이 있습니다.",
        )
with eda_tabs[3]:
    st.pyplot(grouped_cd_plot(data, "pr_tone_group", "CD by PR tone"), width="stretch")
    tone_summary = data.groupby("pr_tone_group")[TARGET].agg(["count", "mean"]).dropna()
    tone_parts = [f"{tone}: n={int(row['count'])}, 평균 {row['mean']:.2f} nm" for tone, row in tone_summary.iterrows()]
    interpretation_card(
        "Tone 평균만으로 공정 반응을 설명할 수는 없습니다",
        "; ".join(tone_parts) + ". 평균이 비슷해도 dose에 대한 방향과 분포 폭이 다를 수 있으므로 tone별 산점도와 상호작용 계수를 함께 봅니다.",
    )
st.caption("관계선은 시각적 경향이며 원인이나 공정 효과를 확정하지 않습니다. PR tone 결측은 MISSING으로 유지하되 Positive/Negative 관계선에는 포함하지 않습니다.")

st.subheader("전체 데이터 해석과 방향성")
tool_direction = "Tool별 평균 차이가 보여 보정·원자료 확인이 필요합니다" if len(tool_summary) > 1 else "Tool 종류가 부족해 비교가 어렵습니다"
focus_direction = "Focus의 단순 선형 방향은 약해 비선형 가능성을 남깁니다"
quality_direction = f"입력 오류 후보 {len(flagged_ids)}행이 있어 포함/제외 민감도를 함께 봅니다" if flagged_ids else "정의된 입력 오류 후보는 발견되지 않았습니다"
st.markdown(f"""
<div class="direction-grid">
  <div class="direction-card"><b>Dose 방향</b><span>Positive: {html.escape(correlation_direction(pos_r))}<br>Negative: {html.escape(correlation_direction(neg_r))}</span></div>
  <div class="direction-card"><b>대안 설명</b><span>{html.escape(tool_direction)}<br>{html.escape(focus_direction)}</span></div>
  <div class="direction-card"><b>판단 신뢰도</b><span>{html.escape(quality_direction)}<br>단일 그래프보다 반복검증과 Lot 검증을 우선합니다.</span></div>
</div>
""", unsafe_allow_html=True)
section_guide(
    "종합 판단",
    "현재 데이터에서는 tone별 dose 방향을 핵심 신호로 보되, Tool level 차이와 입력 오류 민감성을 함께 고려해야 합니다. 다음 행동은 원자료·Tool 상태 확인과 tone별 통제 DOE이며, 현재 그래프만으로 공정 원인을 확정하지 않습니다.",
)

st.header("4. 기준모델: Model 2")
section_guide(
    "왜 Model 2인가요?",
    "Dose, PR tone, dose×tone, Tool만 사용한 해석 가능한 기준입니다. 변수를 더 많이 넣은 모델이 Validation을 개선하지 않아 단순한 구조를 유지했습니다.",
)
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
section_guide(
    "점수가 흔들려도 방향은 유지될 수 있어요",
    "예측 R²의 안정성과 dose–CD 방향의 안정성은 서로 다른 질문입니다. 반복 분할과 unseen-Lot 검증으로 둘을 따로 확인합니다.",
)
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
