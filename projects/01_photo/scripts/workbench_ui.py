"""Tabbed Streamlit UI for the Photo Process Analysis Workbench."""

from pathlib import Path
import html

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.linear_model import LinearRegression

from baseline_regression import CONTINUOUS, TARGET, TrainOnlyFeatureBuilder, clean_category, detect_suspected_input_errors
from custom_model import ALLOWED_INPUTS, CATEGORICAL_INPUTS, DEFAULT_INPUTS, NUMERIC_INPUTS, explain_term, fit_custom_model, fit_fixed_model2
from model_validation import MODEL2, data_quality_sensitivity, lot_group_validation, repeated_validation


PREDICTION = "predicted_resist_line_cd_nm"
BLIND_REQUIRED = {"sample_id", "pr_tone", "tool_id", "normalized_dose_pct"}
TABS = ["1 · Data Audit", "2 · Variable Lab & EDA", "3 · Model Lab", "4 · What-if Simulator", "5 · Validation", "6 · Blind Prediction", "7 · Limitations"]


def theme():
    st.markdown("""<style>
    :root{--navy:#0b2740;--navy2:#174d72;--paper:#f3f6f9;--ink:#132536;--muted:#607382;--gold:#c99a45;--line:#d7e1e8}
    html,body,[class*="css"]{color:var(--ink)}.stApp,[data-testid="stAppViewContainer"]{background:linear-gradient(180deg,#dbe8f1 0,var(--paper) 28rem)!important;color:var(--ink)!important}.block-container{max-width:1220px;padding-top:2rem;padding-bottom:5rem}h1,h2,h3,p,label{color:var(--ink)!important}h1,h2,h3{color:var(--navy)!important}
    .hero{padding:2rem 2.2rem;border-radius:18px;background:linear-gradient(125deg,#071a2b,var(--navy2));box-shadow:0 18px 42px #071a2b38;margin-bottom:1rem}.hero small{color:#8ecbe4;font-weight:800;letter-spacing:.14em}.hero h1{color:#fff!important;margin:.35rem 0}.hero p{color:#dce9f0;margin:0}
    .flow{display:grid;grid-template-columns:repeat(5,1fr);gap:.55rem;margin:1rem 0 1.5rem}.flow div,.fish div{background:#fff;border:1px solid var(--line);border-radius:10px;padding:.75rem;text-align:center;color:var(--navy);font-weight:750;font-size:.82rem}
    [data-testid="stMetric"]{background:#fff!important;border:1px solid var(--line);border-top:4px solid var(--navy2);border-radius:12px;padding:1rem;box-shadow:0 8px 20px #0b274012}[data-testid="stMetricLabel"],[data-testid="stMetricValue"]{color:var(--navy)!important}.guide,.note{background:#fff;border-left:5px solid var(--navy2);border-radius:0 12px 12px 0;padding:1rem;margin:.5rem 0 1rem}.guide b,.note b{color:var(--navy2)}.guide span,.note span{color:var(--muted)}
    .fish{display:grid;grid-template-columns:repeat(5,1fr);gap:.65rem}.fish div{border-top:4px solid var(--gold);text-align:left}.fish span{display:block;color:var(--muted);font-size:.76rem;line-height:1.5;margin-top:.3rem}
    .cd{background:linear-gradient(130deg,#071a2b,var(--navy2));border-radius:16px;padding:1.4rem;color:#fff;text-align:center;margin:1rem 0}.cd span{color:#9ed7ea}.cd strong{display:block;font-size:2.7rem}.cd small{color:#dce9f0}
    .question-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.7rem;margin:1rem 0}.question-card{background:#fff;border:1px solid var(--line);border-radius:13px;padding:1rem;box-shadow:0 8px 22px #0b27400c}.question-card b{display:block;color:var(--navy2);margin-bottom:.35rem}.question-card span{color:var(--muted);font-size:.84rem;line-height:1.55}.question-card:nth-child(1){border-top:4px solid #b85f4b}.question-card:nth-child(2){border-top:4px solid var(--gold)}.question-card:nth-child(3){border-top:4px solid #398072}
    .score{background:linear-gradient(140deg,#fff,#eef5f8);border:1px solid var(--line);border-radius:14px;padding:1.1rem;text-align:center}.score span{color:var(--muted);font-size:.78rem}.score strong{display:block;color:var(--navy);font-size:2rem}.score small{color:var(--muted)}
    .schema-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:.75rem}.schema-card{background:linear-gradient(145deg,#fff,#f7fafc);border:1px solid var(--line);border-radius:13px;padding:1rem}.schema-card b{color:var(--navy);display:flex;justify-content:space-between;align-items:center}.schema-card b em{font-style:normal;background:#e5eef4;color:var(--navy2);border-radius:99px;padding:.15rem .55rem;font-size:.72rem}.schema-card p{margin:.65rem 0 0!important;line-height:1.9}.column-pill{display:inline-block;background:#edf3f6;border:1px solid #d8e4ea;color:#294b62;border-radius:7px;padding:.2rem .48rem;margin:.12rem;font-size:.75rem;font-family:ui-monospace,SFMono-Regular,Consolas,monospace}.schema-card.leak{border-left:4px solid #b85f4b}.schema-card.target{border-left:4px solid #398072}
    .cd-scheme{background:#fff;border:1px solid var(--line);border-radius:16px;padding:1.3rem;box-shadow:0 10px 28px #0b274012}.cd-scheme-title{color:var(--navy);font-weight:850;margin-bottom:1rem}.wafer-row{display:grid;grid-template-columns:95px 1fr 100px;gap:1rem;align-items:center;margin:.9rem 0}.wafer-label{color:var(--muted);font-weight:750}.wafer-window{height:58px;background:repeating-linear-gradient(135deg,#edf3f6,#edf3f6 8px,#e5edf1 8px,#e5edf1 16px);border-radius:9px;display:flex;align-items:center;justify-content:center;overflow:hidden}.cd-line{height:38px;border-radius:5px;transition:width .7s cubic-bezier(.2,.8,.2,1);box-shadow:0 4px 12px #0b274030}.cd-line.ref{background:#8ba1b0}.cd-line.pred{background:linear-gradient(90deg,#174d72,#36a0bd)}.wafer-value{font-weight:900;color:var(--navy);text-align:right}.delta-pill{display:inline-block;background:#e5eef4;color:var(--navy2);border-radius:99px;padding:.35rem .75rem;font-weight:800;margin-top:.35rem}
    div[data-baseweb="tab-list"]{gap:.2rem}button[data-baseweb="tab"]{background:#e5eef4!important;color:var(--navy)!important;border-radius:8px 8px 0 0}button[data-baseweb="tab"][aria-selected="true"]{background:#fff!important}.stDataFrame{background:#fff;border-radius:10px}@media(max-width:850px){.flow,.fish,.question-grid,.schema-grid{grid-template-columns:1fr 1fr}}@media(max-width:520px){.flow,.fish,.question-grid,.schema-grid{grid-template-columns:1fr}.wafer-row{grid-template-columns:75px 1fr}.wafer-value{grid-column:2}}
    </style>""", unsafe_allow_html=True)


def guide(title, text):
    st.markdown(f'<div class="guide"><b>{title}</b><br><span>{text}</span></div>', unsafe_allow_html=True)


def cd_scheme(reference, prediction):
    low, high = 35.0, 65.0
    width = lambda value: float(np.clip(18 + 76 * (value - low) / (high - low), 18, 94))
    delta = prediction - reference
    direction = "CD가 넓어지는 예측" if delta > .05 else "CD가 좁아지는 예측" if delta < -.05 else "기준과 유사한 예측"
    st.markdown(f'''<div class="cd-scheme"><div class="cd-scheme-title">CD Line-width Visual · 모델 기반 상대 비교</div>
    <div class="wafer-row"><div class="wafer-label">기준 조건</div><div class="wafer-window"><div class="cd-line ref" style="width:{width(reference):.1f}%"></div></div><div class="wafer-value">{reference:.2f} nm</div></div>
    <div class="wafer-row"><div class="wafer-label">선택 조건</div><div class="wafer-window"><div class="cd-line pred" style="width:{width(prediction):.1f}%"></div></div><div class="wafer-value">{prediction:.2f} nm</div></div>
    <div class="delta-pill">{direction} · ΔCD {delta:+.2f} nm</div></div>''', unsafe_allow_html=True)


def prepare(raw, remove_duplicates):
    frame, invalid = raw.copy(), {}
    for column in set(NUMERIC_INPUTS + [TARGET]):
        if column in frame:
            before = frame[column].notna(); frame[column] = pd.to_numeric(frame[column], errors="coerce")
            invalid[column] = int((before & frame[column].isna()).sum())
    duplicates = int(frame.duplicated(keep="first").sum())
    if remove_duplicates: frame = frame.loc[~frame.duplicated(keep="first")].copy()
    if "pr_tone" in frame: frame["pr_tone_group"] = clean_category(frame["pr_tone"])
    if "tool_id" in frame: frame["tool_id_group"] = clean_category(frame["tool_id"])
    return frame.reset_index(drop=True), duplicates, invalid


def audit(raw, data, duplicates, invalid):
    flags = detect_suspected_input_errors(data)
    cols = st.columns(5)
    for box, (label, value) in zip(cols, [("행", len(raw)), ("열", raw.shape[1]), ("결측 셀", int(raw.isna().sum().sum())), ("완전 중복 추가행", duplicates), ("입력 오류 후보 행", flags["sample_id"].nunique() if not flags.empty else 0)]): box.metric(label, f"{value:,}")
    identifier = [x for x in ["sample_id", "lot_id", "wafer_id", "tool_id", "pr_tone"] if x in raw]
    process = [x for x in ALLOWED_INPUTS if x in raw and x not in identifier]
    target = [TARGET] if TARGET in raw else []
    leakage_names = ["cdu_3sigma_nm", "ler_nm", "scum_probability", "pattern_collapse_probability", "defect_probability", "spec_pass"]
    leakage = [x for x in leakage_names if x in raw]
    assigned = set(identifier + process + target + leakage); other = [x for x in raw if x not in assigned]
    groups = [("식별·그룹 정보", identifier, ""), ("공정 입력 후보", process, ""), ("예측 Target", target, "target"), ("CD 이후 결과 · Input 금지", leakage, "leak"), ("기타 측정·메타데이터", other, "")]
    cards = []
    for title, columns, css in groups:
        if not columns: continue
        pills = "".join(f'<span class="column-pill">{html.escape(column)}</span>' for column in columns)
        cards.append(f'<div class="schema-card {css}"><b>{title}<em>{len(columns)}개</em></b><p>{pills}</p></div>')
    st.subheader("컬럼 역할 지도")
    st.caption("모델에 넣을 수 있는 공정 입력과 Target Leakage 위험 컬럼을 역할별로 구분했습니다.")
    st.markdown(f'<div class="schema-grid">{"".join(cards)}</div>', unsafe_allow_html=True)
    with st.expander("데이터 타입·결측 상세 보기", expanded=False):
        schema = pd.DataFrame({"컬럼": raw.columns, "데이터 타입": raw.dtypes.astype(str).values, "결측 수": raw.isna().sum().values, "고유값 수": raw.nunique(dropna=False).values})
        st.dataframe(schema, width="stretch", hide_index=True)
    left, right = st.columns(2)
    with left:
        missing = raw.isna().sum().rename("missing_count").to_frame(); missing["missing_pct"] = 100 * missing.missing_count / max(len(raw), 1)
        st.subheader("결측"); st.dataframe(missing, width="stretch")
        if "pr_tone" in raw: st.subheader("PR tone 분포"); st.dataframe(clean_category(raw.pr_tone).value_counts().rename("count"), width="stretch")
    with right:
        if "tool_id" in raw: st.subheader("Tool 분포"); st.dataframe(clean_category(raw.tool_id).value_counts().rename("count"), width="stretch")
        st.subheader("숫자 형식 검사")
        failed = {column: count for column, count in invalid.items() if count > 0}
        if failed:
            st.warning("숫자형 공정 컬럼에 숫자로 읽을 수 없는 문자열이 있습니다. 원본 값 확인이 필요합니다.")
            st.dataframe(pd.Series(failed, name="숫자 변환 실패 행 수").rename_axis("컬럼").to_frame(), width="stretch")
        else:
            st.success("숫자형 컬럼의 형식 변환 실패가 없습니다.")
    st.subheader("입력/단위 오류 검토 후보"); st.caption("후보를 자동 수정·삭제하지 않습니다.")
    if not flags.empty:
        reason_ko = {
            "below 50%; decimal-place/unit entry suspect": "50% 미만으로 관측되어 소수점 위치 또는 단위 입력 오류가 의심됩니다.",
            "absolute focus above 0.5 um; decimal-place entry suspect": "Focus 절댓값이 0.5 µm를 넘어 소수점 위치 입력 오류 가능성이 있습니다.",
            "below 50 nm; about one tenth of observed operating cluster": "50 nm 미만이며 일반 관측 범위의 약 1/10 수준이라 단위 또는 소수점 오류 가능성이 있습니다.",
            "below 50 C physical review bound": "50°C 미만으로 공정 검토 하한보다 낮아 원자료 확인이 필요합니다.",
            "above 5%; far outside observed operating cluster": "5%를 초과해 일반 관측 범위에서 크게 벗어나 단위 또는 입력 오류 가능성이 있습니다.",
        }
        display_flags = flags.rename(columns={"row_index": "행 번호", "sample_id": "샘플 ID", "variable": "검토 변수", "value": "입력값"}).copy()
        display_flags["검토 이유"] = flags["reason"].map(reason_ko).fillna(flags["reason"])
        display_flags["권장 조치"] = "자동 삭제하지 않고 원본 기록·단위·소수점 위치를 담당자가 확인합니다."
        st.dataframe(display_flags[["행 번호", "샘플 ID", "검토 변수", "입력값", "검토 이유", "권장 조치"]], width="stretch", hide_index=True)
    else:
        st.success("현재 기준에서 입력·단위 오류 검토 후보가 없습니다.")
    return flags


def numeric_eda(data, variable, focus_squared):
    left, right = st.columns(2)
    with left:
        fig, ax = plt.subplots(figsize=(6, 4)); ax.hist(data[variable].dropna(), bins=25, color="#245f87", edgecolor="white"); ax.set(title=f"Distribution · {variable}", xlabel=variable); fig.tight_layout(); st.pyplot(fig, width="stretch")
    with right:
        fig, ax = plt.subplots(figsize=(6, 4)); rows = []
        for tone, color in [("POSITIVE", "#c15c4a"), ("NEGATIVE", "#286f99")]:
            part = data[data.pr_tone_group.eq(tone)][[variable, TARGET]].dropna().sort_values(variable); rows.append({"PR tone": tone, "n": len(part), "Pearson r": part[variable].corr(part[TARGET]) if len(part) > 1 else np.nan})
            ax.scatter(part[variable], part[TARGET], s=16, alpha=.42, color=color, label=tone)
            degree = 2 if focus_squared and variable == "focus_um" else 1
            if len(part) > degree + 1 and part[variable].nunique() > degree:
                coef = np.polyfit(part[variable], part[TARGET], degree); grid = np.linspace(part[variable].min(), part[variable].max(), 100); ax.plot(grid, np.polyval(coef, grid), color=color, lw=2)
        ax.set(title=f"{variable} vs CD", xlabel=variable, ylabel=TARGET); ax.legend(); fig.tight_layout(); st.pyplot(fig, width="stretch")
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    if variable == "focus_um": guide("Focus 해석", "선형 상관이 약해도 관계 없음으로 단정하지 않습니다. Focus²와 DOE로 비선형 가능성을 확인합니다.")
    if variable == "normalized_dose_pct": guide("Dose 해석", "Positive/Negative를 섞지 않고 방향을 따로 봅니다. 관찰적 관계이며 인과효과가 아닙니다.")


def categorical_eda(data, variable):
    group = "pr_tone_group" if variable == "pr_tone" else "tool_id_group"; summary = data.groupby(group)[TARGET].agg(["count", "mean", "std"]).reset_index()
    labels = summary[group].astype(str).tolist(); values = [data.loc[data[group].astype(str).eq(label), TARGET].dropna() for label in labels]
    fig, ax = plt.subplots(figsize=(8, 4)); ax.boxplot(values, tick_labels=labels, showfliers=True); ax.set(title=f"CD by {variable}", ylabel=TARGET); fig.tight_layout(); st.pyplot(fig, width="stretch"); st.dataframe(summary, width="stretch", hide_index=True)
    guide("그룹 해석", "평균 차이는 원인 증명이 아닙니다. Lot 배치, recipe 연동, calibration을 함께 확인합니다.")


def scenario(values):
    frame = pd.DataFrame({key: [value] for key, value in values.items()})
    if "pr_tone" in frame: frame["pr_tone_group"] = clean_category(frame.pr_tone)
    if "tool_id" in frame: frame["tool_id_group"] = clean_category(frame.tool_id)
    for column in CONTINUOUS:
        if column not in frame: frame[column] = np.nan
    return frame


def blind_prediction(default_data, data):
    train, _, _ = prepare(default_data, True); builder = TrainOnlyFeatureBuilder().fit(train); model = LinearRegression().fit(builder.transform(train)[MODEL2], train[TARGET])
    unexpected_tones = sorted(set(data["pr_tone_group"]) - {"POSITIVE", "NEGATIVE", "MISSING"})
    unexpected_tools = sorted(set(data["tool_id_group"]) - {"T01", "T02", "T03"})
    if unexpected_tones or unexpected_tools:
        raise ValueError(f"Model 2가 학습하지 않은 범주입니다. PR tone={unexpected_tones}, Tool={unexpected_tools}")
    frame = data.copy()
    for column in CONTINUOUS:
        if column not in frame: frame[column] = np.nan
    result = data.drop(columns=["pr_tone_group", "tool_id_group"], errors="ignore").copy(); result[PREDICTION] = model.predict(builder.transform(frame)[MODEL2]); return result


def run(project: Path):
    st.set_page_config(page_title="Photo Process Analysis Workbench", page_icon="🔬", layout="wide")
    theme(); default_path = project / "data" / "A" / "train.csv"
    st.markdown("""<div class="hero"><small>PHOTO PROCESS · HANDS-ON ANALYTICS</small><h1>Photo Process Analysis Workbench</h1><p>데이터 → 변수선택 → 탐색 → 모델 → 예측을 직접 수행합니다.</p></div><div class="flow"><div>1 · DATA</div><div>2 · VARIABLES</div><div>3 · EDA</div><div>4 · MODEL</div><div>5 · SIMULATE</div></div>""", unsafe_allow_html=True)
    uploaded = st.file_uploader("CSV 또는 Excel 업로드", type=["csv", "xlsx"])
    try:
        if uploaded is None: raw = pd.read_csv(default_path)
        elif Path(uploaded.name).suffix.lower() == ".csv": raw = pd.read_csv(uploaded)
        else: raw = pd.read_excel(uploaded, engine="openpyxl")
    except Exception as exc: st.error(f"파일을 읽을 수 없습니다: {exc}"); st.stop()
    st.info(f"현재 데이터: {uploaded.name if uploaded else '기본 예제 · A/train.csv'}")
    blind = TARGET not in raw; data, duplicates, invalid = prepare(raw, not blind)
    overview = st.columns(5)
    overview[0].metric("Rows", f"{len(raw):,}")
    overview[1].metric("Columns", f"{raw.shape[1]:,}")
    overview[2].metric("Missing cells", f"{int(raw.isna().sum().sum()):,}")
    overview[3].metric("Duplicate rows", f"{duplicates:,}")
    overview[4].metric("Mode", "Blind Prediction" if blind else "Analysis")
    if not blind:
        st.markdown("""<div class="question-grid"><div class="question-card"><b>문제 · CD 변동</b><span>어떤 공정 입력과 조건 조합이 CD 변동과 관련되어 있는지 확인합니다.</span></div><div class="question-card"><b>가설 · Tone별 Dose 반응</b><span>Positive와 Negative PR의 Dose–CD 방향이 다를 가능성을 분리해 검토합니다.</span></div><div class="question-card"><b>대안 · Tool과 데이터 품질</b><span>Tool 조건, Lot 구성, 입력 오류가 관찰 관계와 예측력을 흔들 수 있습니다.</span></div></div>""", unsafe_allow_html=True)
    tabs = st.tabs(TABS)
    with tabs[0]:
        st.header("Data Audit"); guide("분석 전 확인", "Schema·단위·결측·중복·입력 오류·편중을 먼저 봅니다."); flags = audit(raw, data, duplicates, invalid)
        if not blind: st.markdown("""<div class="fish"><div><b>Machine</b><span>Tool·calibration</span></div><div><b>Material</b><span>PR tone·lot</span></div><div><b>Method</b><span>Dose·Focus·Bake·Develop</span></div><div><b>Man</b><span>작업자/교대조 추가 수집</span></div><div><b>Environment</b><span>Field·시간·온습도</span></div></div>""", unsafe_allow_html=True)
    if blind:
        for i in [1, 2, 3, 4]:
            with tabs[i]: st.info("Blind Holdout에서는 Variable/Model/Simulator/Validation을 실행하지 않습니다.")
        with tabs[5]:
            st.header("Blind Prediction"); missing = sorted(BLIND_REQUIRED.difference(raw.columns))
            if missing: st.error(f"Model 2 입력 컬럼이 부족합니다: {missing}")
            else:
                st.warning("이 파일에는 실제 CD 정답이 없으므로 예측만 생성합니다. 실제 예측 성능은 정답 데이터가 제공된 후 평가할 수 있습니다.")
                try:
                    result = blind_prediction(pd.read_csv(default_path), data)
                except ValueError as exc:
                    st.error(str(exc)); result = None
                if result is not None:
                    st.dataframe(result[["sample_id", PREDICTION]], width="stretch", hide_index=True); st.download_button("전체 prediction CSV 다운로드", result.to_csv(index=False).encode("utf-8-sig"), "photo_holdout_predictions.csv", "text/csv"); st.success(f"{len(result):,}행 모두 예측했습니다. R²/RMSE/MAE는 계산하지 않았습니다.")
        with tabs[6]: st.warning("Holdout으로 모델 구조·변수·전처리를 수정하지 않습니다.")
        return
    required = {"sample_id", "pr_tone", "tool_id", TARGET}
    if required.difference(data): st.error(f"필수 컬럼 부족: {sorted(required.difference(data))}"); return
    data = data[data[TARGET].notna()].copy(); available = [x for x in ALLOWED_INPUTS if x in data]
    with tabs[1]:
        st.header("Variable Lab & Automatic EDA"); st.selectbox("Target", [TARGET]); selected = st.multiselect("공정 Input", available, default=[x for x in DEFAULT_INPUTS if x in available], key="selected_inputs")
        interaction = st.checkbox("Dose × PR tone interaction", True, disabled=not {"normalized_dose_pct", "pr_tone"}.issubset(selected)); focus2 = st.checkbox("Focus² visual guide", True, disabled="focus_um" not in selected)
        st.caption("CD 이후 결과(CDU, LER, scum/collapse/defect probability, spec_pass)는 Input에서 제외합니다."); st.warning("상관관계는 인과관계를 의미하지 않습니다.")
        eda_tabs = st.tabs(selected) if selected else []
        for variable, tab in zip(selected, eda_tabs):
            with tab: numeric_eda(data, variable, focus2) if variable in NUMERIC_INPUTS else categorical_eda(data, variable)
    baseline = fit_fixed_model2(data)
    with tabs[2]:
        st.header("Model Lab · Linear Regression"); guide("직접 모델을 설계해 보세요", "아래에서 공정변수를 선택하면 seed 42의 동일 Train/Validation 분할로 학습하고, 검증된 Model 2와 공정하게 비교합니다.")
        model_selected = st.multiselect("모델 Input 변수", available, default=[x for x in DEFAULT_INPUTS if x in available], key="model_inputs")
        model_interaction = st.checkbox("모델에 Dose × PR tone interaction 포함", True, disabled=not {"normalized_dose_pct", "pr_tone"}.issubset(model_selected), key="model_interaction")
        st.caption("CD 이후 측정 결과는 선택 목록에서 제외되어 Target Leakage를 방지합니다. Random Forest는 사용하지 않습니다.")
        signature = (tuple(model_selected), bool(model_interaction), TARGET)
        if st.button("Build Model", type="primary", disabled=not model_selected):
            try: st.session_state.custom_model = fit_custom_model(data, model_selected, model_interaction); st.session_state.custom_signature = signature
            except Exception as exc: st.error(str(exc))
        custom = st.session_state.get("custom_model") if st.session_state.get("custom_signature") == signature else None
        if custom:
            score_cols = st.columns(4)
            score_items = [("Train R²", custom.metrics["train_r2"]), ("Validation R²", custom.metrics["validation_r2"]), ("Validation 설명력", custom.metrics["validation_r2"] * 100), ("Model 2 Validation R²", baseline.metrics["validation_r2"])]
            for box, (label, value) in zip(score_cols, score_items):
                suffix = "%" if label == "Validation 설명력" else ""
                box.markdown(f'<div class="score"><span>{label}</span><strong>{value:.1f}{suffix}</strong><small>{"R² × 100의 표시값" if suffix else "coefficient of determination"}</small></div>', unsafe_allow_html=True)
            table = pd.DataFrame([{"Metric": label, "Custom Model": custom.metrics[key], "Model 2": baseline.metrics[key]} for key, label in [("train_r2", "Train R²"), ("validation_r2", "Validation R²"), ("validation_rmse_nm", "RMSE"), ("validation_mae_nm", "MAE")]]); st.dataframe(table, width="stretch", hide_index=True)
            if len(custom.inputs) > len(baseline.inputs) and custom.metrics["validation_r2"] <= baseline.metrics["validation_r2"]: st.warning("변수 증가가 일반화 성능 개선으로 이어지지 않았습니다.")
            if custom.metrics["train_r2"] > baseline.metrics["train_r2"] and custom.metrics["validation_r2"] < baseline.metrics["validation_r2"]: st.warning("Train 성능은 좋아졌지만 Validation 성능은 낮아져 과적합 가능성이 있습니다.")
            coef = custom.coefficients.copy(); coef["meaning"] = coef.term.map(explain_term); st.subheader("Model Interpretation"); st.dataframe(coef, width="stretch", hide_index=True); st.caption("조건부 연관이며 인과효과가 아닙니다.")
        else: st.info("변수를 선택하고 Build Model을 눌러주세요.")
    with tabs[3]:
        st.header("Model-based What-if Simulator"); custom = st.session_state.get("custom_model") if st.session_state.get("custom_signature") == signature else None; names = ["Model 2"] + (["Custom Model"] if custom else []); name = st.radio("사용 모델", names, horizontal=True); active = custom if name == "Custom Model" else baseline
        values, outside = {}, []; controls = st.columns(min(3, len(active.inputs)))
        for i, variable in enumerate(active.inputs):
            with controls[i % len(controls)]:
                if variable in NUMERIC_INPUTS:
                    low, high = active.builder.ranges[variable]; values[variable] = st.number_input(variable, value=float(active.builder.medians[variable]), step=max((high-low)/100, .01), key=f"sim_{name}_{variable}"); st.caption(f"Train range: {low:.3f} ~ {high:.3f}"); outside += [variable] if values[variable] < low or values[variable] > high else []
                else: values[variable] = st.selectbox(variable, active.builder.levels[variable], key=f"sim_{name}_{variable}")
        pred = float(active.predict(scenario(values))[0]); ref_values = {x: active.builder.medians[x] if x in NUMERIC_INPUTS else active.builder.levels[x][0] for x in active.inputs}; ref = float(active.predict(scenario(ref_values))[0])
        if outside: st.warning(f"⚠ 학습 데이터 범위를 벗어난 조건입니다. 예측 신뢰도가 낮을 수 있습니다. 범위 밖 변수: {', '.join(outside)}")
        st.markdown(f'<div class="cd"><span>Predicted CD</span><strong>{pred:.2f} nm</strong><small>기준조건 대비 ΔCD = {pred-ref:+.2f} nm</small></div>', unsafe_allow_html=True)
        cd_scheme(ref, pred)
        sweep_options = [x for x in active.inputs if x in NUMERIC_INPUTS]; st.subheader("한 변수만 변화시켜 보기")
        if sweep_options:
            sweep = st.selectbox("Sweep variable", sweep_options); low, high = active.builder.ranges[sweep]; grid = np.linspace(low, high, 60); frames = pd.concat([scenario({**values, sweep: float(v)}) for v in grid], ignore_index=True); curve = active.predict(frames)
            fig, ax = plt.subplots(figsize=(9, 4)); ax.plot(grid, curve, color="#174d72", lw=3); ax.scatter([values[sweep]], [pred], color="#c15c4a", s=75); ax.set(xlabel=sweep, ylabel="Predicted CD (nm)", title=f"One-variable sweep · {active.name}"); ax.grid(alpha=.2); fig.tight_layout(); st.pyplot(fig, width="stretch"); st.caption("모델 예측 곡선이며 실제 공정 인과효과가 아닙니다.")
    with tabs[4]:
        st.header("Validation"); cards = st.columns(3); cards[0].metric("Validation R²", f"{baseline.metrics['validation_r2']:.3f}"); cards[1].metric("RMSE", f"{baseline.metrics['validation_rmse_nm']:.3f} nm"); cards[2].metric("MAE", f"{baseline.metrics['validation_mae_nm']:.3f} nm")
        repeated, summary, _ = repeated_validation(data); quality_detail, quality_summary = data_quality_sensitivity(data, set(flags.sample_id.astype(str)) if not flags.empty else set()); lots, _ = lot_group_validation(data, min(8, data.lot_id.nunique()))
        vt = st.tabs(["30회 반복", "데이터 품질", "Lot", "Dose 방향"])
        with vt[0]: st.dataframe(summary[summary.model.eq("Model 2")], width="stretch")
        with vt[1]: st.dataframe(quality_summary, width="stretch")
        with vt[2]: st.dataframe(lots, width="stretch")
        with vt[3]: m2 = repeated[repeated.model.eq("Model 2")]; c1, c2 = st.columns(2); c1.metric("Positive 음(-)", f"{int((m2.positive_dose_slope_nm_per_pct_point<0).sum())}/30"); c2.metric("Negative 양(+)", f"{int((m2.negative_dose_slope_nm_per_pct_point>0).sum())}/30")
    with tabs[5]: st.info("Target CD가 없는 CSV/XLSX 업로드 시 고정 Model 2 예측과 다운로드가 활성화됩니다.")
    with tabs[6]: st.warning("관찰 데이터이므로 인과효과를 확정할 수 없습니다. What-if/Sweep은 모델 예측이며 Random Forest와 Holdout 튜닝은 사용하지 않습니다.")
