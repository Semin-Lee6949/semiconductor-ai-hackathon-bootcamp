"""Tabbed Streamlit UI for the Photo Process Analysis Workbench."""

from pathlib import Path
import html

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.linear_model import LinearRegression

from baseline_regression import CONTINUOUS, TARGET, TrainOnlyFeatureBuilder, clean_category, detect_suspected_input_errors
from custom_model import ALLOWED_INPUTS, CATEGORICAL_INPUTS, DEFAULT_INPUTS, NUMERIC_INPUTS, explain_term, fit_custom_model, fit_fixed_model2, fit_logistic_model
from model_validation import MODEL2, data_quality_sensitivity, lot_group_validation, repeated_validation


PREDICTION = "predicted_resist_line_cd_nm"
BLIND_REQUIRED = {"sample_id", "pr_tone", "tool_id", "normalized_dose_pct"}
TABS = ["1 · Engineering Summary", "2 · Data Audit", "3 · Variable Lab & EDA", "4 · Model Lab", "5 · What-if Simulator", "6 · Validation", "7 · Blind Prediction", "8 · Final Engineering Report"]
PARAMETER_GUIDE = {
    "normalized_dose_pct": ("Normalized Dose", "%", "기준 노광량 대비 실제 노광량의 상대 비율", "PR tone별로 CD 반응 방향과 민감도가 달라지는지 확인합니다.", "같은 Tool·재료에서도 dose 조정에 따라 CD가 일관된 방향으로 움직이는가?"),
    "focus_um": ("Focus Offset", "µm", "기준 초점 위치에서 벗어난 정도", "최적 초점 주변에서는 직선보다 곡률이나 대칭성이 더 중요할 수 있습니다.", "0 근처에서 CD가 안정적인가, 양·음 방향의 비대칭 또는 공정창 축소가 있는가?"),
    "coat_thickness_nm": ("PR Coat Thickness", "nm", "노광 전 도포된 PR 막의 두께", "흡광·현상 거동 및 공정조건 구성과 함께 CD 차이가 나타날 가능성을 검토합니다.", "두께 자체 신호인가, 특정 PR lot·coater·recipe와 함께 움직인 대안 설명인가?"),
    "softbake_temp_c": ("Softbake Temperature", "°C", "노광 전 PR 용매 제거를 위한 Bake 온도", "PR 상태와 감도 차이를 설명할 후보지만 recipe·시간과 함께 확인해야 합니다.", "온도 차이가 독립적으로 존재하는가, 특정 Tool·Lot에 묶여 있는가?"),
    "peb_temp_c": ("Post-Exposure Bake", "°C", "노광 후 반응 확산을 진행시키는 Bake 온도", "노광 반응과 현상 전 profile 형성에 관련된 조건인지 탐색합니다.", "PEB 변화 범위가 충분한가, dose와 함께 바뀌어 계수 해석이 섞이지 않는가?"),
    "develop_time_s": ("Develop Time", "s", "노광된 PR을 현상액에 반응시키는 시간", "현상 부족·과현상 가능성과 CD 분포 변화를 검토합니다.", "시간 변화에 따라 CD가 단조롭게 움직이는가, tone·농도별 반응이 다른가?"),
    "developer_concentration_pct": ("Developer Concentration", "%", "현상액의 농도", "현상 속도와 함께 변하는 조건이므로 시간과의 결합을 확인합니다.", "농도와 develop time이 동시에 조정되어 개별 효과를 구분하기 어려운가?"),
    "pr_tone": ("PR Tone", "category", "Positive/Negative Photoresist 유형", "같은 dose 증가라도 관찰되는 CD 방향이 달라질 수 있어 반드시 분리합니다.", "두 tone을 합친 평균이 서로 반대인 반응을 가리고 있지 않은가?"),
    "tool_id": ("Tool ID", "category", "공정에 사용된 설비 식별자", "설비 condition·calibration·Lot 배치 차이의 대안 설명을 확인합니다.", "Tool 평균 차이가 설비 자체인지, 투입 Lot·recipe 차이인지 추가 로그로 구분할 수 있는가?"),
    TARGET: ("Resist Line CD", "nm", "현상 후 PR line의 Critical Dimension", "이번 분석에서 예측하려는 Target이며 값의 변화와 안정성을 함께 봅니다.", "평균뿐 아니라 분포·극단값·Lot/Tool별 오차가 허용 가능한가?"),
}


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
    .parameter-card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:1.05rem;margin:.55rem 0;box-shadow:0 7px 18px #0b27400b}.parameter-head{display:flex;justify-content:space-between;gap:1rem;align-items:center}.parameter-head b{color:var(--navy);font-size:1rem}.parameter-head em{font-style:normal;color:var(--navy2);background:#e5eef4;border-radius:99px;padding:.18rem .6rem;font-size:.72rem}.parameter-code{color:var(--muted);font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:.76rem}.parameter-grid{display:grid;grid-template-columns:1fr 1fr;gap:.7rem;margin-top:.75rem}.parameter-grid div{background:#f7fafc;border-radius:9px;padding:.7rem}.parameter-grid strong{display:block;color:var(--navy2);font-size:.76rem;margin-bottom:.25rem}.parameter-grid span{color:var(--muted);font-size:.8rem;line-height:1.5}
    .finding{background:#fff;border:1px solid var(--line);border-left:5px solid var(--navy2);border-radius:0 12px 12px 0;padding:.9rem 1rem;margin:.55rem 0}.finding b{color:var(--navy)}.finding span{display:block;color:var(--muted);font-size:.84rem;margin-top:.25rem}.decision{background:linear-gradient(135deg,#071a2b,#174d72);color:#fff;border-radius:14px;padding:1rem 1.15rem;margin:.65rem 0}.decision b{color:#9ed7ea}.decision span{display:block;color:#e0edf3;font-size:.86rem;line-height:1.55;margin-top:.25rem}.cannot{background:#fff7f2;border:1px solid #e8c8b8;border-left:5px solid #b85f4b;border-radius:0 12px 12px 0;padding:1rem;color:#744334}
    .engineer{background:linear-gradient(145deg,#f7fbfd,#fff);border:1px solid #cbdde7;border-radius:14px;padding:1rem 1.1rem;margin:1rem 0;box-shadow:0 8px 22px #0b27400d}.engineer-head{color:var(--navy);font-weight:900;margin-bottom:.65rem}.engineer-grid{display:grid;grid-template-columns:1fr 1fr;gap:.65rem}.engineer-grid div{background:#fff;border:1px solid var(--line);border-radius:9px;padding:.72rem}.engineer-grid b{display:block;color:var(--navy2);font-size:.76rem;margin-bottom:.25rem}.engineer-grid span{color:var(--muted);font-size:.81rem;line-height:1.5}.engineer-limit{margin-top:.65rem;color:#835647;font-size:.76rem}
    .report-flow{display:grid;grid-template-columns:repeat(6,1fr);gap:.45rem;margin:1rem 0}.report-flow div{background:#fff;border:1px solid var(--line);border-top:4px solid var(--navy2);border-radius:10px;padding:.7rem;text-align:center;color:var(--navy);font-size:.76rem;font-weight:850}.report-section{background:#fff;border:1px solid var(--line);border-radius:15px;padding:1.15rem;margin:.8rem 0;box-shadow:0 8px 24px #0b27400c}.report-section h4{margin:0 0 .6rem;color:var(--navy)}.report-section p,.report-section li{color:var(--muted);line-height:1.65}.risk-card{background:#fff7f2;border:1px solid #e6c8ba;border-radius:12px;padding:.9rem;margin:.55rem 0}.risk-card b{color:#874c3b}.risk-card span{display:block;color:#735f58;font-size:.83rem;line-height:1.55;margin-top:.25rem}
    .cd-scheme{background:#fff;border:1px solid var(--line);border-radius:16px;padding:1.3rem;box-shadow:0 10px 28px #0b274012}.cd-scheme-title{color:var(--navy);font-weight:850;margin-bottom:1rem}.wafer-row{display:grid;grid-template-columns:95px 1fr 100px;gap:1rem;align-items:center;margin:.9rem 0}.wafer-label{color:var(--muted);font-weight:750}.wafer-window{height:58px;background:repeating-linear-gradient(135deg,#edf3f6,#edf3f6 8px,#e5edf1 8px,#e5edf1 16px);border-radius:9px;display:flex;align-items:center;justify-content:center;overflow:hidden}.cd-line{height:38px;border-radius:5px;transition:width .7s cubic-bezier(.2,.8,.2,1);box-shadow:0 4px 12px #0b274030}.cd-line.ref{background:#8ba1b0}.cd-line.pred{background:linear-gradient(90deg,#174d72,#36a0bd)}.wafer-value{font-weight:900;color:var(--navy);text-align:right}.delta-pill{display:inline-block;background:#e5eef4;color:var(--navy2);border-radius:99px;padding:.35rem .75rem;font-weight:800;margin-top:.35rem}
    div[data-baseweb="tab-list"]{gap:.2rem}button[data-baseweb="tab"]{background:#e5eef4!important;color:var(--navy)!important;border-radius:8px 8px 0 0}button[data-baseweb="tab"][aria-selected="true"]{background:#fff!important}.stDataFrame{background:#fff;border-radius:10px}@media(max-width:850px){.flow,.fish,.question-grid,.schema-grid,.report-flow{grid-template-columns:1fr 1fr}}@media(max-width:520px){.flow,.fish,.question-grid,.schema-grid,.parameter-grid,.engineer-grid,.report-flow{grid-template-columns:1fr}.wafer-row{grid-template-columns:75px 1fr}.wafer-value{grid-column:2}}
    </style>""", unsafe_allow_html=True)


def guide(title, text):
    st.markdown(f'<div class="guide"><b>{title}</b><br><span>{text}</span></div>', unsafe_allow_html=True)


def engineer_note(observation, thinking, action, limit):
    st.markdown(f'''<div class="engineer"><div class="engineer-head">🎓 1타 엔지니어의 데이터 읽기</div><div class="engineer-grid">
    <div><b>① 데이터에서 보이는 것</b><span>{html.escape(observation)}</span></div><div><b>② 이렇게 생각합니다</b><span>{html.escape(thinking)}</span></div>
    <div style="grid-column:1/-1"><b>③ 다음 관리·검증 Action</b><span>{html.escape(action)}</span></div></div><div class="engineer-limit">주의 · {html.escape(limit)}</div></div>''', unsafe_allow_html=True)


def cd_scheme(reference, prediction):
    low, high = 35.0, 65.0
    width = lambda value: float(np.clip(18 + 76 * (value - low) / (high - low), 18, 94))
    delta = prediction - reference
    direction = "CD가 넓어지는 예측" if delta > .05 else "CD가 좁아지는 예측" if delta < -.05 else "기준과 유사한 예측"
    st.markdown(f'''<div class="cd-scheme"><div class="cd-scheme-title">CD Line-width Visual · 모델 기반 상대 비교</div>
    <div class="wafer-row"><div class="wafer-label">기준 조건</div><div class="wafer-window"><div class="cd-line ref" style="width:{width(reference):.1f}%"></div></div><div class="wafer-value">{reference:.2f} nm</div></div>
    <div class="wafer-row"><div class="wafer-label">선택 조건</div><div class="wafer-window"><div class="cd-line pred" style="width:{width(prediction):.1f}%"></div></div><div class="wafer-value">{prediction:.2f} nm</div></div>
    <div class="delta-pill">{direction} · ΔCD {delta:+.2f} nm</div></div>''', unsafe_allow_html=True)


def parameter_card(column):
    name, unit, meaning, reason, question = PARAMETER_GUIDE[column]
    st.markdown(f'''<div class="parameter-card"><div class="parameter-head"><div><b>{html.escape(name)}</b><div class="parameter-code">{html.escape(column)}</div></div><em>{html.escape(unit)}</em></div>
    <div class="parameter-grid"><div><strong>이 파라미터는?</strong><span>{html.escape(meaning)}</span></div><div><strong>왜 CD와 함께 보나요?</strong><span>{html.escape(reason)}</span></div><div style="grid-column:1/-1"><strong>엔지니어의 다음 질문</strong><span>{html.escape(question)}</span></div></div></div>''', unsafe_allow_html=True)


def correlation_thoughts(data, variables, tone, corr):
    notes = []
    off_diagonal = corr.where(~np.eye(len(corr), dtype=bool)).abs().stack()
    if not off_diagonal.empty:
        first, second = off_diagonal.idxmax(); strength = corr.loc[first, second]
        notes.append(f"현재 선택에서 가장 큰 절대 선형 상관은 {first}–{second}의 r={strength:+.3f}입니다. 두 변수가 함께 조정되는 조건인지 확인하면 계수 해석 오류를 줄일 수 있습니다.")
    if "normalized_dose_pct" in variables:
        pos = data.loc[data.pr_tone_group.eq("POSITIVE"), "normalized_dose_pct"].corr(data.loc[data.pr_tone_group.eq("POSITIVE"), TARGET])
        neg = data.loc[data.pr_tone_group.eq("NEGATIVE"), "normalized_dose_pct"].corr(data.loc[data.pr_tone_group.eq("NEGATIVE"), TARGET])
        notes.append(f"Dose–CD Pearson r은 Positive {pos:+.3f}, Negative {neg:+.3f}입니다. 방향이 다르므로 전체 상관 하나보다 tone별 그래프와 interaction 검증을 우선합니다.")
    if "focus_um" in variables:
        notes.append("Focus는 Pearson r이 작아도 최적점 주변의 곡률이 남을 수 있습니다. Focus² 시각화와 중심 주변 DOE 없이 '영향 없음'으로 결론 내리지 않습니다.")
    notes.append(f"현재 행렬 범위는 {tone}입니다. 상관이 크면 원인 확정이 아니라 공정조건 연동·Tool/Lot 편중·다중공선성을 먼저 의심합니다.")
    return notes


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
    if "pr_tone" in raw and "tool_id" in raw:
        fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
        for ax, column, title, color in [(axes[0], "pr_tone", "Sample count by PR tone", "#286f99"), (axes[1], "tool_id", "Sample count by Tool", "#c99a45")]:
            counts = clean_category(raw[column]).value_counts(); ax.bar(counts.index.astype(str), counts.values, color=color); ax.set(title=title, ylabel="Count"); ax.grid(axis="y", alpha=.2)
            for index, value in enumerate(counts.values): ax.text(index, value, f"{value:,}", ha="center", va="bottom", fontsize=8)
        fig.tight_layout(); st.pyplot(fig, width="stretch")
    st.subheader("입력/단위 오류 검토 후보"); st.caption("후보를 자동 수정·삭제하지 않습니다.")
    if not flags.empty:
        reason_ko = {
            "below 50%; decimal-place/unit entry suspect": "50% 미만으로 관측되어 소수점 위치 또는 단위 입력 오류가 의심됩니다.",
            "absolute focus above 0.5 um; decimal-place entry suspect": "Focus 절댓값이 0.5 µm를 넘어 소수점 위치 입력 오류 가능성이 있습니다.",
            "below 50 nm; about one tenth of observed operating cluster": "50 nm 미만이며 일반 관측 범위의 약 1/10 수준이라 단위 또는 소수점 오류 가능성이 있습니다.",
            "below 50 C physical review bound": "50°C 미만으로 공정 검토 하한보다 낮아 원자료 확인이 필요합니다.",
            "above 5%; far outside observed operating cluster": "5%를 초과해 일반 관측 범위에서 크게 벗어나 단위 또는 입력 오류 가능성이 있습니다.",
        }
        action_ko = {
            "below 50%; decimal-place/unit entry suspect": "설비 exposure log와 원본 recipe에서 normalized dose 단위와 소수점 위치를 대조합니다.",
            "absolute focus above 0.5 um; decimal-place entry suspect": "Focus setpoint·metrology log와 비교해 µm 단위 및 소수점 위치를 확인합니다.",
            "below 50 nm; about one tenth of observed operating cluster": "Coater thickness 원자료와 측정 단위를 확인하고 nm/10 배율 입력 여부를 검토합니다.",
            "below 50 C physical review bound": "Track recipe와 장비 온도 이력에서 실제 Softbake 설정값을 확인합니다.",
            "above 5%; far outside observed operating cluster": "Chemical 공급 기록과 희석비를 확인해 농도 단위 및 입력 배율을 대조합니다.",
        }
        why_ko = {
            "below 50%; decimal-place/unit entry suspect": "Dose 축이 10배 왜곡되면 tone별 기울기와 Validation 결과가 크게 달라질 수 있기 때문입니다.",
            "absolute focus above 0.5 um; decimal-place entry suspect": "한 개의 극단 Focus가 산점도 축과 비선형 관계 판단을 왜곡할 수 있기 때문입니다.",
            "below 50 nm; about one tenth of observed operating cluster": "두께 단위 오류를 실제 박막 변화로 해석하면 잘못된 공정 가설을 만들 수 있기 때문입니다.",
            "below 50 C physical review bound": "비현실적인 Bake 값은 회귀계수와 What-if 범위를 불안정하게 만들 수 있기 때문입니다.",
            "above 5%; far outside observed operating cluster": "농도 극단값 하나가 계수와 예측 오차에 과도한 영향력을 가질 수 있기 때문입니다.",
        }
        display_flags = flags.rename(columns={"row_index": "행 번호", "sample_id": "샘플 ID", "variable": "검토 변수", "value": "입력값"}).copy()
        display_flags["검토 이유"] = flags["reason"].map(reason_ko).fillna(flags["reason"])
        display_flags["권장 조치"] = flags["reason"].map(action_ko).fillna("원본 기록·단위·소수점 위치를 담당자가 확인합니다.")
        display_flags["왜 필요한가"] = flags["reason"].map(why_ko).fillna("입력 오류가 분석 결과에 미치는 영향을 원자료 확인 전에는 구분할 수 없기 때문입니다.")
        st.dataframe(display_flags[["행 번호", "샘플 ID", "검토 변수", "입력값", "검토 이유", "권장 조치", "왜 필요한가"]], width="stretch", hide_index=True)
        st.caption("검토 후보는 자동 삭제·보정하지 않습니다. 원자료 확인 후 수정 여부와 근거를 별도 로그로 남겨야 합니다.")
    else:
        st.success("현재 기준에서 입력·단위 오류 검토 후보가 없습니다.")
    missing_total = int(raw.isna().sum().sum()); tool_counts = clean_category(raw.tool_id).value_counts() if "tool_id" in raw else pd.Series(dtype=float)
    imbalance = float(tool_counts.max() / tool_counts.min()) if len(tool_counts) > 1 and tool_counts.min() else 1.0
    engineer_note(
        f"결측 {missing_total:,}셀, 완전 중복 추가행 {duplicates:,}개, 입력 오류 검토 후보 {flags['sample_id'].nunique() if not flags.empty else 0}행이며 Tool 최대/최소 표본 비는 {imbalance:.2f}배입니다.",
        "결측·입력 오류는 모델이 자동으로 해결할 문제가 아니라 원자료와 단위를 확인할 신호입니다. Tool 표본 편중이 크면 전체 평균이 특정 Tool 조건을 더 많이 반영할 수 있습니다.",
        "오류 후보 원본 로그 확인 → 중복 생성 경로 확인 → tone×Tool 표본표 확인 → 부족한 조합의 추가 수집 순서로 관리합니다.",
        "후보 표시는 오류 확정이나 삭제 근거가 아니며, 표본수 차이는 Tool 효과의 증명이 아닙니다.",
    )
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
    row_map = {row["PR tone"]: row for row in rows}; pos_r = row_map.get("POSITIVE", {}).get("Pearson r", np.nan); neg_r = row_map.get("NEGATIVE", {}).get("Pearson r", np.nan)
    if variable == "normalized_dose_pct":
        observation = f"Dose–CD Pearson r은 Positive {pos_r:+.3f}, Negative {neg_r:+.3f}로 관찰됩니다."
        thinking = "tone별 방향이 다르면 두 PR을 합친 기울기는 공정 반응을 가릴 수 있습니다. interaction과 반복검증을 함께 봅니다."
        action = "tone별 dose 구간을 나누고 Tool을 block으로 둔 반복 DOE에서 평균 CD와 산포를 동시에 비교합니다."
    elif variable == "focus_um":
        observation = f"Focus–CD 선형 r은 Positive {pos_r:+.3f}, Negative {neg_r:+.3f}입니다. 화면의 곡선 가이드도 함께 확인합니다."
        thinking = "선형 r이 작아도 최적 focus 주변의 U자형·비대칭 공정창 가능성이 남습니다."
        action = "0 주변 focus level을 대칭적으로 배치하고 tone·Tool별 CD 평균과 산포를 비교하는 DOE를 설계합니다."
    else:
        observation = f"{variable}–CD Pearson r은 Positive {pos_r:+.3f}, Negative {neg_r:+.3f}입니다."
        thinking = "tone별 값이 다르거나 범위가 좁으면 단순 상관만으로 해당 조건의 중요도를 판단하기 어렵습니다."
        action = f"{variable}의 실제 변경 범위와 tone·Tool·Lot 동시 변화를 확인하고, 필요하면 한 조건씩 통제해 재검증합니다."
    engineer_note(observation, thinking, action, "Pearson r과 시각적 추세는 선형 연관이며 인과효과나 최적 recipe를 뜻하지 않습니다.")


def categorical_eda(data, variable):
    group = "pr_tone_group" if variable == "pr_tone" else "tool_id_group"; summary = data.groupby(group)[TARGET].agg(["count", "mean", "std"]).reset_index()
    labels = summary[group].astype(str).tolist(); values = [data.loc[data[group].astype(str).eq(label), TARGET].dropna() for label in labels]
    fig, ax = plt.subplots(figsize=(8, 4)); ax.boxplot(values, tick_labels=labels, showfliers=True); ax.set(title=f"CD by {variable}", ylabel=TARGET); fig.tight_layout(); st.pyplot(fig, width="stretch"); st.dataframe(summary, width="stretch", hide_index=True)
    guide("그룹 해석", "평균 차이는 원인 증명이 아닙니다. Lot 배치, recipe 연동, calibration을 함께 확인합니다.")
    spread = data.groupby(group)[TARGET].std().dropna(); widest = str(spread.idxmax()) if len(spread) else "판단 불가"; widest_std = float(spread.max()) if len(spread) else np.nan
    mean_gap = float(summary["mean"].max() - summary["mean"].min()) if len(summary) > 1 else 0.0
    if variable == "tool_id":
        thinking = f"{widest}의 산포가 가장 크다면 chamber/track condition, calibration, maintenance 시점 또는 투입 Lot 구성이 다른지 먼저 의심합니다."
        action = f"{widest}에서 tone×dose를 맞춘 뒤 CD 산포를 재비교하고 calibration·PM·Lot 로그를 시간순으로 겹쳐 확인합니다."
    else:
        thinking = "PR tone 평균만 보면 dose에 대한 반대 방향과 분포 내부 구조를 놓칠 수 있습니다."
        action = "tone별 dose scatter, slope, IQR과 Tool 구성을 함께 확인하고 tone별 Process Window를 별도로 검토합니다."
    engineer_note(f"그룹 평균 CD 최대 차이는 {mean_gap:.3f} nm이고 {widest}의 표준편차가 {widest_std:.3f} nm로 가장 큽니다.", thinking, action, "Box plot의 산포 차이는 표본수·극단값·Lot 구성 영향을 포함하며 설비 또는 재료의 인과효과를 확정하지 않습니다.")


def correlation_matrix(data, variables, tone):
    columns = [column for column in variables if column in NUMERIC_INPUTS and column in data] + [TARGET]
    columns = list(dict.fromkeys(columns))
    frame = data if tone == "전체" else data[data["pr_tone_group"].eq(tone)]
    corr = frame[columns].corr(method="pearson")
    fig_size = max(5.5, len(columns) * 1.05)
    fig, ax = plt.subplots(figsize=(fig_size, fig_size * .78))
    image = ax.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(len(columns)), labels=columns, rotation=38, ha="right")
    ax.set_yticks(range(len(columns)), labels=columns)
    for row in range(len(columns)):
        for column in range(len(columns)):
            value = corr.iloc[row, column]
            ax.text(column, row, "—" if pd.isna(value) else f"{value:.2f}", ha="center", va="center", color="white" if pd.notna(value) and abs(value) > .55 else "#132536", fontsize=8)
    tone_label = "ALL" if tone == "전체" else tone
    ax.set_title(f"Pearson Correlation Matrix · {tone_label} · n={len(frame):,}")
    fig.colorbar(image, ax=ax, fraction=.04, pad=.03, label="Pearson r")
    fig.tight_layout()
    return fig, corr


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


def engineering_summary(data, baseline, flags, quality_summary, custom):
    st.header("Engineering Summary · 결과에서 다음 검증으로")
    guide("이 화면의 목적", "결론을 먼저 읽고, 아래 탭에서 근거 → 모델 실험 → What-if → 검증 순서로 직접 확인합니다.")
    tone = data[data.pr_tone_group.isin(["POSITIVE", "NEGATIVE"])].groupby("pr_tone_group")[TARGET].agg(["count", "mean", "std", "min", "max"])
    tone["IQR"] = data[data.pr_tone_group.isin(["POSITIVE", "NEGATIVE"])].groupby("pr_tone_group")[TARGET].quantile(.75) - data[data.pr_tone_group.isin(["POSITIVE", "NEGATIVE"])].groupby("pr_tone_group")[TARGET].quantile(.25)
    tone["Range"] = tone["max"] - tone["min"]
    tone = tone.rename(columns={"count": "Sample 수", "mean": "Mean CD (nm)", "std": "CD Std (nm)", "IQR": "CD IQR (nm)", "Range": "CD Range (nm)"})
    st.subheader("1 · PR tone별 CD 변동성")
    st.dataframe(tone[["Sample 수", "Mean CD (nm)", "CD Std (nm)", "CD IQR (nm)", "CD Range (nm)"]].style.format({"Sample 수": "{:.0f}", "Mean CD (nm)": "{:.3f}", "CD Std (nm)": "{:.3f}", "CD IQR (nm)": "{:.3f}", "CD Range (nm)": "{:.3f}"}), width="stretch")
    if {"POSITIVE", "NEGATIVE"}.issubset(tone.index) and min(tone.loc["POSITIVE", "Sample 수"], tone.loc["NEGATIVE", "Sample 수"]) >= 2:
        pos_std, neg_std = tone.loc["POSITIVE", "CD Std (nm)"], tone.loc["NEGATIVE", "CD Std (nm)"]
        larger, smaller = ("POSITIVE", "NEGATIVE") if pos_std >= neg_std else ("NEGATIVE", "POSITIVE")
        ratio = max(pos_std, neg_std) / max(min(pos_std, neg_std), 1e-12)
        st.info(f"기술통계상 {larger}의 CD 표준편차가 {smaller}보다 {ratio:.2f}배({(ratio-1)*100:.1f}% 높음)입니다. 표본수·극단값·Lot/Tool 구성을 고려한 검정 전에는 모집단 변동성 차이로 단정하지 않습니다.")

    coef = baseline.coefficients.set_index("term")["coefficient"]
    positive_slope = float(coef["dose_centered"]); negative_slope = positive_slope + float(coef.get("dose_x_pr_tone_NEGATIVE", 0))
    st.subheader("2 · Dose Sensitivity · Model 2")
    dose_cols = st.columns(2)
    dose_cols[0].metric("Positive · Dose +1 %p", f"{positive_slope:+.3f} nm CD")
    dose_cols[1].metric("Negative · Dose +1 %p", f"{negative_slope:+.3f} nm CD")
    st.warning("모델 기반 관계이며 실제 recipe 변경의 인과효과를 의미하지 않습니다.")

    st.subheader("3 · Tool Effect")
    tool = data.groupby("tool_id_group")[TARGET].agg(["count", "mean"]).rename(columns={"count": "Sample 수", "mean": "Mean CD (nm)"})
    tool["Model effect vs T01 (nm)"] = [0.0 if item == "T01" else float(coef.get(f"tool_id_{item}", np.nan)) for item in tool.index]
    st.dataframe(tool.style.format({"Sample 수": "{:.0f}", "Mean CD (nm)": "{:.3f}", "Model effect vs T01 (nm)": "{:+.3f}"}), width="stretch")
    if len(tool) > 1: st.info("Tool별 CD level과 Model 기준 차이가 관찰됩니다. Tool·calibration·Lot 배치는 Dose 반응과 별도로 관리해야 할 교란 후보이며 Tool 자체의 인과효과로 확정하지 않습니다.")

    st.subheader("4 · Key Findings")
    findings = [
        ("관찰 1 · Tone별 Dose 방향", f"Model 2에서 Positive {positive_slope:+.3f} nm/%p, Negative {negative_slope:+.3f} nm/%p로 방향이 다르게 나타납니다."),
        ("관찰 2 · Tool별 CD level", f"Tool 평균 CD 범위는 {tool['Mean CD (nm)'].min():.2f}~{tool['Mean CD (nm)'].max():.2f} nm입니다. 구성 차이를 함께 확인해야 합니다."),
    ]
    r2_rows = quality_summary[quality_summary.metric.eq("validation_r2")]
    if len(r2_rows) >= 2:
        values = dict(zip(r2_rows.condition, r2_rows["mean"])); included = values.get("A_including_flagged"); excluded = values.get("B_excluding_5_flagged_rows")
        if included is not None and excluded is not None: findings.append(("관찰 3 · 데이터 품질 민감도", f"오류 후보 포함/검토 제외 반복 R² 평균은 {included:.3f}/{excluded:.3f}입니다. 제외가 정답이라는 뜻이 아니라 원자료 확인이 우선이라는 신호입니다."))
    if custom:
        delta = custom.metrics["validation_r2"] - baseline.metrics["validation_r2"]
        findings.append(("현재 Custom Model", f"{len(custom.inputs)}개 Input의 Validation R²는 {custom.metrics['validation_r2']:.3f}이며 Model 2 대비 {delta:+.3f}입니다. 변수 수보다 Validation 추가가치를 기준으로 판단합니다."))
    else: findings.append(("관찰 4 · 모델 복잡도", "Custom Model을 Build하면 Model 2 대비 Validation 추가가치가 이곳에 자동 반영됩니다. 변수 증가는 성능 개선을 보장하지 않습니다."))
    for title, message in findings: st.markdown(f'<div class="finding"><b>{title}</b><span>{message}</span></div>', unsafe_allow_html=True)

    st.subheader("5 · Engineering Decision · 다음에 검증할 것")
    decisions = [
        ("Tone별 Process Window", "Positive/Negative PR을 묶지 않고 tone별 Dose Process Window를 별도로 검토합니다."),
        ("평균과 변동성 동시 평가", "Dose 조건별 Mean CD뿐 아니라 Std·IQR·Range와 극단값을 함께 비교합니다."),
        ("Tool baseline 확인", "같은 tone·dose 구간에서 Tool별 baseline CD, calibration, Lot 구성을 대조합니다."),
        ("Tone × Dose DOE", "필요하면 Tool을 block으로 둔 반복 DOE로 안정적인 후보 영역을 검증합니다. 현재 데이터만으로 최적값을 확정하지 않습니다."),
    ]
    for title, message in decisions: st.markdown(f'<div class="decision"><b>{title}</b><span>{message}</span></div>', unsafe_allow_html=True)
    st.subheader("6 · What We Cannot Conclude")
    st.markdown('<div class="cannot"><b>현재 화면으로 확정할 수 없는 것</b><br>• 상관·회귀 결과는 인과관계가 아닙니다.<br>• 최적 Dose와 Recipe는 현재 데이터만으로 확정할 수 없습니다.<br>• 합성·특정 데이터셋의 방향을 실제 Fab 일반법칙으로 확대하지 않습니다.<br>• 학습 범위 밖 외삽 예측은 신뢰도가 낮습니다.</div>', unsafe_allow_html=True)
    st.subheader("7 · 근거를 확인하는 순서")
    st.markdown("**Engineering Summary → Variable Lab & EDA → Model Lab → What-if Simulator → Validation**")
    st.caption("요약에서 발견한 질문을 EDA로 확인하고, Custom Model로 비교한 뒤, What-if를 탐색하고 반복·Lot 검증에서 안정성을 확인하세요.")


def final_engineering_report(raw, data, duplicates, flags, baseline, quality_summary, repeated, lots, custom, classifier):
    st.header("Final Engineering Report · 판단과 검증 계획")
    guide("보고서 읽는 순서", "현황을 숫자로 고정한 뒤, 확실한 관찰과 미확정 가설을 분리하고, 예상 문제상황마다 확인 방법과 완료 기준을 연결합니다.")
    st.markdown('<div class="report-flow"><div>1 · 문제</div><div>2 · 데이터 신뢰도</div><div>3 · 관찰 신호</div><div>4 · 대안 설명</div><div>5 · 검증</div><div>6 · Action</div></div>', unsafe_allow_html=True)

    n_raw, n_analysis = len(raw), len(data); flagged_n = flags.sample_id.nunique() if not flags.empty else 0
    missing_cells = int(raw.isna().sum().sum()); flagged_pct = 100 * flagged_n / max(n_analysis, 1); duplicate_pct = 100 * duplicates / max(n_raw, 1)
    tone = data[data.pr_tone_group.isin(["POSITIVE", "NEGATIVE"])].groupby("pr_tone_group")[TARGET].agg(["count", "mean", "std"])
    pos_n, neg_n = int(tone.loc["POSITIVE", "count"]), int(tone.loc["NEGATIVE", "count"])
    pos_share, neg_share = 100 * pos_n / n_analysis, 100 * neg_n / n_analysis
    std_ratio = float(tone.loc["NEGATIVE", "std"] / tone.loc["POSITIVE", "std"])
    coef = baseline.coefficients.set_index("term")["coefficient"]
    pos_slope = float(coef["dose_centered"]); neg_slope = pos_slope + float(coef.get("dose_x_pr_tone_NEGATIVE", 0))
    tool = data.groupby("tool_id_group")[TARGET].agg(["count", "mean", "std"]); tool_gap = float(tool["mean"].max() - tool["mean"].min()); widest_tool = str(tool["std"].idxmax())
    m2 = repeated[repeated.model.eq("Model 2")]; repeated_mean = float(m2.validation_r2.mean()); repeated_std = float(m2.validation_r2.std(ddof=1)); pos_ok = int((m2.positive_dose_slope_nm_per_pct_point < 0).sum()); neg_ok = int((m2.negative_dose_slope_nm_per_pct_point > 0).sum())
    q = quality_summary[quality_summary.metric.eq("validation_r2")].set_index("condition"); q_inc=float(q.loc["A_including_flagged","mean"]); q_exc=float(q.loc["B_excluding_5_flagged_rows","mean"]); q_inc_std=float(q.loc["A_including_flagged","std"]); q_exc_std=float(q.loc["B_excluding_5_flagged_rows","std"])
    stability_reduction = 100 * (q_inc_std - q_exc_std) / max(q_inc_std, 1e-12)
    worst = lots.loc[lots.validation_r2.idxmin()]

    st.subheader("1 · 현황 요약")
    overview = pd.DataFrame([
        ["원본 → 분석 행", f"{n_raw:,} → {n_analysis:,}", f"완전 중복 추가행 {duplicates}개({duplicate_pct:.2f}%) 제거; 원본 파일은 보존"],
        ["데이터 품질", f"결측 {missing_cells:,}셀 · 오류 후보 {flagged_n}행({flagged_pct:.2f}%)", "후보는 포함한 채 주 분석, 제외 조건은 민감도 비교만 수행"],
        ["PR tone 구성", f"Positive {pos_n}행({pos_share:.1f}%) · Negative {neg_n}행({neg_share:.1f}%)", "MISSING/Target 결측 때문에 합계가 분석 행과 다를 수 있음"],
        ["기준 Model 2", f"R² {baseline.metrics['validation_r2']:.3f} · RMSE {baseline.metrics['validation_rmse_nm']:.3f} nm · MAE {baseline.metrics['validation_mae_nm']:.3f} nm", "단일 고정 분할 결과; 최종 성능으로 과장하지 않음"],
    ], columns=["항목", "현재 숫자", "판단 기준"])
    st.dataframe(overview, width="stretch", hide_index=True)
    engineer_note(f"원본 {n_raw}행 중 중복 {duplicates}행과 오류 후보 {flagged_n}행이 확인됐고, tone 구성은 Positive {pos_share:.1f}%와 Negative {neg_share:.1f}%입니다.", "분석 숫자를 보기 전에 표본 구성과 입력 신뢰도를 고정해야 모델 성능과 공정 차이를 잘못 해석하지 않습니다.", "오류 후보 원자료와 tone×Tool 표본 구성을 먼저 승인한 뒤 모델 결과를 검토합니다.", "오류 후보는 자동 삭제 근거가 아니며 현재 통계는 관찰 데이터 요약입니다.")

    st.subheader("2 · 숫자로 확인된 핵심 관찰")
    evidence = pd.DataFrame([
        ["Dose 방향", f"Positive {pos_slope:+.3f} nm/%p · Negative {neg_slope:+.3f} nm/%p", f"반복 방향 {pos_ok}/30, {neg_ok}/30", "tone별 DOE 우선순위 신호"],
        ["CD 산포", f"Positive σ={tone.loc['POSITIVE','std']:.3f} · Negative σ={tone.loc['NEGATIVE','std']:.3f} nm", f"Negative/Positive={std_ratio:.2f}배 ({(std_ratio-1)*100:+.1f}%)", "모집단 차이 확정 전 구성·극단값 검토"],
        ["Tool level", f"Tool 평균 최대 차이 {tool_gap:.3f} nm", f"최대 산포 Tool={widest_tool}, σ={tool.loc[widest_tool,'std']:.3f} nm", "Dose와 별도 교란 후보"],
        ["반복 성능", f"30회 R² {repeated_mean:.3f} ± {repeated_std:.3f}", f"단일 R² {baseline.metrics['validation_r2']:.3f}", "평균과 흔들림을 함께 승인"],
        ["데이터 품질 민감도", f"후보 포함/제외 R² {q_inc:.3f}/{q_exc:.3f}", f"R² std {q_inc_std:.3f}/{q_exc_std:.3f} ({stability_reduction:.1f}% 감소)", "삭제보다 원자료 확인 우선"],
    ], columns=["관찰", "결과", "비교 숫자", "엔지니어 판단"])
    st.dataframe(evidence, width="stretch", hide_index=True)

    st.subheader("3 · 확실한 것과 아직 확신하지 못한 것")
    st.markdown(f'''<div class="report-section"><h4>현재 데이터에서 반복 확인된 신호</h4><ul>
    <li>Model 2의 dose 방향은 Positive 음(-) {pos_ok}/30회, Negative 양(+) {neg_ok}/30회 유지됐습니다.</li>
    <li>Tool 평균 CD 최대 차이는 {tool_gap:.3f} nm이며, {widest_tool}의 기술통계 산포가 가장 큽니다.</li>
    <li>오류 후보 포함/제외에 따라 반복 R² 평균이 {q_inc:.3f}에서 {q_exc:.3f}으로 달라져 데이터 품질 민감성이 확인됩니다.</li></ul></div>''', unsafe_allow_html=True)
    st.markdown(f'''<div class="report-section"><h4>아직 확신할 수 없는 것 · 이렇게 확인합니다</h4><ul>
    <li><b>최적 Dose:</b> 현재 slope만으로 결정하지 않고 tone별 Dose level 반복 DOE에서 CD 평균·σ·IQR·결함을 함께 확인합니다.</li>
    <li><b>Tool 원인:</b> {widest_tool} 산포가 Tool 자체 때문인지 calibration·PM·Lot 구성 때문인지 동일 tone×dose 조건과 시간 로그로 분리합니다.</li>
    <li><b>입력 오류:</b> 후보 {flagged_n}행을 삭제하지 않고 설비·recipe 원본과 단위를 대조한 뒤 근거가 있을 때만 버전 관리된 보정본을 만듭니다.</li>
    <li><b>일반화 성능:</b> 30회 R² 표준편차 {repeated_std:.3f}와 worst Lot fold R² {worst.validation_r2:.3f}을 고려해 unseen Lot에서 재확인합니다.</li></ul></div>''', unsafe_allow_html=True)

    st.subheader("4 · 예상 문제상황과 개선 방법")
    risks = [
        ("Tone 혼합으로 방향 상쇄", f"Positive {pos_slope:+.3f}, Negative {neg_slope:+.3f} nm/%p를 한 기울기로 합치면 잘못된 recipe 판단 가능", "tone별 모델·관리도·Process Window 분리"),
        ("입력 오류로 모델 불안정", f"오류 후보 제외 시 R² std가 {stability_reduction:.1f}% 감소", "원자료 검증, 단위 validation rule, 입력 범위 경고와 변경 로그"),
        ("Tool baseline drift/편중", f"Tool 평균 gap {tool_gap:.3f} nm, 최대 산포 {widest_tool}", "동일 조건 Tool matching, calibration/PM 전후 trend, Lot-balanced sampling"),
        ("극단 Lot에서 성능 저하", f"worst fold R² {worst.validation_r2:.3f}, RMSE {worst.validation_rmse_nm:.3f} nm", "큰 잔차 sample과 validation Lot의 재료·장비·recipe metadata 추적"),
        ("What-if 외삽 오판", "학습 min/max 밖 조건은 데이터 근거가 없음", "관측 범위 안에서 후보를 좁히고 범위 밖은 DOE로 새 데이터 확보"),
    ]
    if classifier: risks.append(("PASS/FAIL 분류력 부족", f"Logistic AUC {classifier.metrics['validation_roc_auc']:.3f}, Accuracy {classifier.metrics['validation_accuracy']:.3f} vs majority {classifier.metrics['majority_baseline_accuracy']:.3f}", "기준모델을 넘기 전 배포 금지; label·불균형·누락 변수를 재검토"))
    for title, signal, improvement in risks: st.markdown(f'<div class="risk-card"><b>{html.escape(title)}</b><span>예상 신호 · {html.escape(signal)}<br>개선 방법 · {html.escape(improvement)}</span></div>', unsafe_allow_html=True)

    st.subheader("5 · 우선순위 Action Plan")
    actions = pd.DataFrame([
        ["P0", "입력 오류 후보 원자료 확인", f"{flagged_n}행의 값·단위·소수점·설비 로그 일치", "수정 근거와 원본/보정 버전 기록"],
        ["P1", "Tool baseline 및 산포 확인", f"{widest_tool} 포함 Tool별 동일 tone×dose 비교", "Tool별 mean/σ와 calibration·PM·Lot 설명 가능"],
        ["P1", "Tone×Dose DOE", "tone별 최소 3수준 dose와 반복, Tool block", "방향 재현 + 후보 영역의 CD 평균·산포 동시 충족"],
        ["P2", "Focus 비선형 DOE", "0 주변 대칭 level과 반복", "곡률·비대칭 및 tone/Tool interaction 판단"],
        ["P3", "최종 Holdout 평가", "모델·변수·전처리 동결 후 정답 공개", "R²/RMSE/MAE와 실패 Lot 기록; 재튜닝 금지"],
    ], columns=["우선순위", "Action", "확인 방법", "완료 기준"])
    st.dataframe(actions, width="stretch", hide_index=True)

    custom_text = "Custom Model 미생성"
    if custom: custom_text = f"{custom.name} Validation R² {custom.metrics['validation_r2']:.3f} (Model 2 대비 {custom.metrics['validation_r2']-baseline.metrics['validation_r2']:+.3f})"
    final_text = f"""Photo Process Analysis Workbench 최종 요약
- 분석 데이터: {n_analysis}/{n_raw}행, 입력 오류 후보 {flagged_n}행({flagged_pct:.2f}%)
- Model 2: Validation R² {baseline.metrics['validation_r2']:.3f}, RMSE {baseline.metrics['validation_rmse_nm']:.3f} nm, MAE {baseline.metrics['validation_mae_nm']:.3f} nm
- 반복 검증: R² {repeated_mean:.3f} ± {repeated_std:.3f}
- Dose slope: Positive {pos_slope:+.3f}, Negative {neg_slope:+.3f} nm/%p; 방향 반복 {pos_ok}/30, {neg_ok}/30
- Tool 평균 CD gap: {tool_gap:.3f} nm; 최대 산포 Tool {widest_tool}
- 품질 민감도: 오류 후보 포함/제외 R² {q_inc:.3f}/{q_exc:.3f}
- Custom: {custom_text}
- 인간 판단: 최적 recipe를 확정하지 않고 입력 검증 → Tool matching → tone별 Dose DOE → Focus DOE → 동결 Holdout 순으로 확인한다.
"""
    st.download_button("현재 결과 요약 TXT 다운로드", final_text.encode("utf-8-sig"), "photo_engineering_summary.txt", "text/plain")
    st.markdown('<div class="cannot"><b>최종 결론의 경계</b><br>이 보고서는 현재 관찰 데이터에서 다음 검증 순서를 정합니다. 최적 Recipe, 인과효과, 실제 Fab 일반법칙 또는 품질 보증을 확정하지 않습니다.</div>', unsafe_allow_html=True)


def run(project: Path):
    st.set_page_config(page_title="Photo Process Analysis Workbench", page_icon="🔬", layout="wide")
    theme(); default_path = project / "data" / "A" / "train.csv"
    st.markdown("""<div class="hero"><small>PHOTO PROCESS · DECISION WORKBENCH</small><h1>Photo Process Analysis Workbench</h1><p>결론을 먼저 읽고 근거·모델·시뮬레이션·검증으로 내려가 판단을 확인합니다.</p></div><div class="flow"><div>1 · SUMMARY</div><div>2 · EVIDENCE</div><div>3 · MODEL</div><div>4 · SIMULATE</div><div>5 · VALIDATE</div></div>""", unsafe_allow_html=True)
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
    with tabs[1]:
        st.header("Data Audit"); guide("분석 전 확인", "Schema·단위·결측·중복·입력 오류·편중을 먼저 봅니다."); flags = audit(raw, data, duplicates, invalid)
        if not blind: st.markdown("""<div class="fish"><div><b>Machine</b><span>Tool·calibration</span></div><div><b>Material</b><span>PR tone·lot</span></div><div><b>Method</b><span>Dose·Focus·Bake·Develop</span></div><div><b>Man</b><span>작업자/교대조 추가 수집</span></div><div><b>Environment</b><span>Field·시간·온습도</span></div></div>""", unsafe_allow_html=True)
    if blind:
        with tabs[0]: st.info("Blind Holdout에는 실제 CD가 없어 Engineering Summary를 생성하지 않습니다. Blind Prediction에서 고정 Model 2 예측만 제공합니다.")
        for i in [2, 3, 4, 5]:
            with tabs[i]: st.info("Blind Holdout에서는 Variable/Model/Simulator/Validation을 실행하지 않습니다.")
        with tabs[6]:
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
                    prediction_std = float(result[PREDICTION].std()); prediction_min = float(result[PREDICTION].min()); prediction_max = float(result[PREDICTION].max())
                    engineer_note(f"200행 예측 범위는 {prediction_min:.2f}~{prediction_max:.2f} nm, 예측 표준편차는 {prediction_std:.2f} nm입니다.", "예측 분포는 Holdout 조건 다양성을 보여주지만 실제 오차나 품질 수준을 뜻하지 않습니다. 정답 CD가 없기 때문입니다.", "예측 파일과 모델 버전을 고정해 저장하고, 정답 공개 후 sample_id로 결합해 최초 1회 최종 평가합니다.", "Holdout 예측을 보고 변수·모델·전처리를 다시 선택하면 평가 누수가 발생합니다.")
        with tabs[7]: st.warning("Holdout으로 모델 구조·변수·전처리를 수정하지 않습니다.")
        return
    required = {"sample_id", "pr_tone", "tool_id", TARGET}
    if required.difference(data): st.error(f"필수 컬럼 부족: {sorted(required.difference(data))}"); return
    data = data[data[TARGET].notna()].copy(); available = [x for x in ALLOWED_INPUTS if x in data]
    baseline = fit_fixed_model2(data)
    flagged_ids = set(flags.sample_id.astype(str)) if not flags.empty else set()
    quality_detail, quality_summary = data_quality_sensitivity(data, flagged_ids)
    latest_custom = st.session_state.get("custom_model")
    with tabs[0]: engineering_summary(data, baseline, flags, quality_summary, latest_custom)
    with tabs[2]:
        st.header("Variable Lab & Automatic EDA"); st.selectbox("Target", [TARGET]); selected = st.multiselect("공정 Input", available, default=[x for x in DEFAULT_INPUTS if x in available], key="selected_inputs")
        interaction = st.checkbox("Dose × PR tone interaction", True, disabled=not {"normalized_dose_pct", "pr_tone"}.issubset(selected)); focus2 = st.checkbox("Focus² visual guide", True, disabled="focus_um" not in selected)
        st.caption("CD 이후 결과(CDU, LER, scum/collapse/defect probability, spec_pass)는 Input에서 제외합니다."); st.warning("상관관계는 인과관계를 의미하지 않습니다.")
        with st.expander("선택 파라미터 공정 해설 · 무엇을 의미하고 무엇을 질문해야 하나요?", expanded=True):
            parameter_card(TARGET)
            for column in selected: parameter_card(column)
        numeric_selected = [column for column in selected if column in NUMERIC_INPUTS]
        st.subheader("선택 변수 상관계수 행렬")
        if numeric_selected:
            matrix_tone = st.radio("상관행렬 데이터 범위", ["전체", "POSITIVE", "NEGATIVE"], horizontal=True, key="correlation_tone")
            corr_figure, corr_table = correlation_matrix(data, numeric_selected, matrix_tone)
            left, right = st.columns([1.45, 1])
            with left: st.pyplot(corr_figure, width="stretch")
            with right:
                st.dataframe(corr_table.style.format("{:.3f}"), width="stretch")
                guide("왜 확인하나요?", "Input끼리 강하게 함께 움직이면 개별 회귀계수 해석이 불안정할 수 있습니다. 전체 상관이 tone별 상관과 다르면 그룹 혼합 가능성도 확인해야 합니다.")
                st.markdown("**이 데이터에서 엔지니어가 이어갈 생각**")
                for note in correlation_thoughts(data, numeric_selected, matrix_tone, corr_table): st.markdown(f"- {note}")
            st.caption("Pearson r은 선형 동행 정도입니다. 비선형 관계·교란·인과효과를 증명하지 않습니다.")
        else:
            st.info("숫자형 공정 Input을 하나 이상 선택하면 Target CD를 포함한 상관계수 행렬이 생성됩니다.")
        eda_tabs = st.tabs(selected) if selected else []
        for variable, tab in zip(selected, eda_tabs):
            with tab: numeric_eda(data, variable, focus2) if variable in NUMERIC_INPUTS else categorical_eda(data, variable)
    with tabs[3]:
        st.header("Model Lab · 교육용 회귀와 분류")
        guide("문제 유형을 먼저 구분하세요", "CD는 연속값이므로 Linear/Ridge Regression으로 예측합니다. Logistic Regression은 연속 CD가 아니라 PASS/FAIL 확률을 예측하는 별도 분류 모델입니다.")
        regression_tab, logistic_tab, learning_tab = st.tabs(["CD Regression", "PASS/FAIL Logistic", "모델 선택 가이드"])
        with regression_tab:
            st.markdown("**Target: resist_line_cd_nm · 연속값 예측**")
            regression_kind = st.radio("회귀 모델", ["Linear Regression", "Ridge Regression"], horizontal=True, key="regression_kind")
            model_selected = st.multiselect("회귀 Input 변수", available, default=[x for x in DEFAULT_INPUTS if x in available], key="regression_inputs")
            model_interaction = st.checkbox("회귀 모델에 Dose × PR tone interaction 포함", True, disabled=not {"normalized_dose_pct", "pr_tone"}.issubset(model_selected), key="regression_interaction")
            ridge_alpha = st.number_input("Ridge alpha · 규제 강도", min_value=0.01, max_value=100.0, value=1.0, step=.1, disabled=regression_kind != "Ridge Regression")
            signature = (tuple(model_selected), bool(model_interaction), TARGET, regression_kind, float(ridge_alpha))
            if st.button("Build CD Regression", type="primary", disabled=not model_selected):
                try:
                    st.session_state.custom_model = fit_custom_model(data, model_selected, model_interaction, model_kind=regression_kind, ridge_alpha=ridge_alpha)
                    st.session_state.custom_signature = signature; st.rerun()
                except Exception as exc: st.error(str(exc))
            custom = st.session_state.get("custom_model") if st.session_state.get("custom_signature") == signature else None
            if custom:
                scores = st.columns(4); scores[0].metric("Train R²", f"{custom.metrics['train_r2']:.3f}"); scores[1].metric("Validation R²", f"{custom.metrics['validation_r2']:.3f}"); scores[2].metric("RMSE", f"{custom.metrics['validation_rmse_nm']:.3f} nm"); scores[3].metric("MAE", f"{custom.metrics['validation_mae_nm']:.3f} nm")
                table = pd.DataFrame([{"Metric": label, custom.name: custom.metrics[key], "Model 2": baseline.metrics[key]} for key, label in [("validation_r2", "Validation R²"), ("validation_rmse_nm", "RMSE"), ("validation_mae_nm", "MAE")]]); st.dataframe(table, width="stretch", hide_index=True)
                if len(custom.inputs) > len(baseline.inputs) and custom.metrics["validation_r2"] <= baseline.metrics["validation_r2"]: st.warning("변수 증가가 일반화 성능 개선으로 이어지지 않았습니다.")
                coef = custom.coefficients.copy(); coef["교육용 해석"] = coef.term.map(explain_term); st.dataframe(coef, width="stretch", hide_index=True)
                st.caption("Ridge 계수는 Train 표준화 후의 조건부 계수입니다. 두 모델 모두 인과효과를 의미하지 않습니다.")
                delta_r2 = custom.metrics["validation_r2"] - baseline.metrics["validation_r2"]
                engineer_note(f"{custom.name}의 Validation R²는 {custom.metrics['validation_r2']:.3f}, Model 2 대비 {delta_r2:+.3f}입니다.", "Train 점수가 아니라 unseen Validation 추가가치가 모델 채택 기준입니다. Ridge는 상관된 변수의 계수를 줄일 수 있지만 자동으로 성능을 높이지 않습니다.", "R²·RMSE·MAE를 Model 2와 함께 비교하고, 개선이 작거나 불안정하면 단순 Model 2를 유지합니다.", "한 번의 Validation 차이는 우연한 분할 영향이 있으므로 반복·Lot 검증 전에는 우열을 확정하지 않습니다.")
            else: st.info("변수와 회귀 종류를 선택한 뒤 Build CD Regression을 눌러주세요.")
        with logistic_tab:
            st.markdown("**Target: spec_pass · PASS=1 / FAIL=0 분류**")
            st.info("Logistic Regression은 예측 CD가 아니라 PASS 확률을 출력합니다. spec_pass는 Input으로 사용하지 않습니다.")
            logistic_inputs = st.multiselect("분류 Input 변수", available, default=[x for x in DEFAULT_INPUTS if x in available], key="logistic_inputs")
            logistic_interaction = st.checkbox("분류 모델에 Dose × PR tone interaction 포함", True, disabled=not {"normalized_dose_pct", "pr_tone"}.issubset(logistic_inputs), key="logistic_interaction")
            logistic_signature = (tuple(logistic_inputs), bool(logistic_interaction), "spec_pass")
            if "spec_pass" not in data: st.warning("업로드 데이터에 spec_pass가 없어 Logistic Regression을 만들 수 없습니다.")
            elif st.button("Build Logistic Classification", disabled=not logistic_inputs):
                try:
                    st.session_state.logistic_model = fit_logistic_model(data, logistic_inputs, logistic_interaction)
                    st.session_state.logistic_signature = logistic_signature; st.rerun()
                except Exception as exc: st.error(str(exc))
            classifier = st.session_state.get("logistic_model") if st.session_state.get("logistic_signature") == logistic_signature else None
            if classifier:
                scores = st.columns(5); scores[0].metric("Train Accuracy", f"{classifier.metrics['train_accuracy']:.3f}"); scores[1].metric("Validation Accuracy", f"{classifier.metrics['validation_accuracy']:.3f}"); scores[2].metric("Majority Baseline", f"{classifier.metrics['majority_baseline_accuracy']:.3f}"); scores[3].metric("Validation ROC-AUC", f"{classifier.metrics['validation_roc_auc']:.3f}"); scores[4].metric("Log Loss", f"{classifier.metrics['validation_log_loss']:.3f}")
                if classifier.metrics["validation_accuracy"] <= classifier.metrics["majority_baseline_accuracy"]: st.warning("현재 Logistic 모델의 Accuracy가 다수 클래스만 예측하는 기준보다 높지 않습니다. 공정 의사결정 모델로 채택하기 전에 변수·라벨·분할 구조를 재검토해야 합니다.")
                if classifier.metrics["validation_roc_auc"] < .6: st.warning("ROC-AUC가 0.6 미만으로 PASS/FAIL 순위 구분력이 약합니다. 모델 생성 성공과 유용한 예측 성능을 구분해야 합니다.")
                coef = classifier.coefficients.copy(); coef["교육용 해석"] = "양수면 다른 조건이 같을 때 PASS log-odds 증가와 관련, 음수면 감소와 관련"; st.dataframe(coef, width="stretch", hide_index=True)
                st.caption("Accuracy는 정답 비율, ROC-AUC는 PASS/FAIL 순위 구분력, Log Loss는 확률 예측의 틀린 확신까지 평가합니다. 계수는 인과효과가 아닙니다.")
                engineer_note(f"Validation Accuracy {classifier.metrics['validation_accuracy']:.3f}, 다수 클래스 기준 {classifier.metrics['majority_baseline_accuracy']:.3f}, ROC-AUC {classifier.metrics['validation_roc_auc']:.3f}입니다.", "모델이 실행됐다는 사실과 PASS/FAIL을 유용하게 구분한다는 사실은 다릅니다. 기준보다 낮은 Accuracy와 0.5에 가까운 AUC는 약한 분류력을 뜻합니다.", "label 정의·class imbalance·누락 공정변수를 확인하고, 기준모델을 넘지 못하면 배포하지 않습니다.", "spec_pass는 CD와 다른 분류 Target이며 이 모델의 확률을 CD 예측값으로 해석할 수 없습니다.")
        with learning_tab:
            st.markdown("""- **Linear Regression**: CD와 Input의 조건부 선형 관계를 가장 직접적으로 해석합니다. 기준 Model 2와 같은 출발점입니다.
- **Ridge Regression**: 상관된 변수가 많을 때 큰 계수를 줄여 안정화를 시도합니다. alpha가 클수록 규제가 강하지만 Validation 개선을 보장하지 않습니다.
- **Logistic Regression**: PASS/FAIL 같은 이진 결과의 확률을 예측합니다. 연속형 CD 예측에는 사용하지 않습니다.
- **엔지니어 판단**: Train 점수보다 Validation을 우선하고, 복잡한 모델은 Model 2 대비 추가가치가 있을 때만 채택합니다.""")
    with tabs[4]:
        st.header("Model-based What-if Simulator"); guide("교육용 읽는 법", "한 조건만 바꿨을 때 모델 예측 CD와 기준 대비 ΔCD를 봅니다. 실제 recipe 효과가 아니라 학습된 조건부 관계이며, Ridge를 선택했다면 표준화·규제가 적용된 Custom Model입니다."); custom = st.session_state.get("custom_model") if st.session_state.get("custom_signature") == signature else None; names = ["Model 2"] + (["Custom Model"] if custom else []); name = st.radio("사용 모델", names, horizontal=True); active = custom if name == "Custom Model" else baseline
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
            direction = "증가" if curve[-1] > curve[0] else "감소" if curve[-1] < curve[0] else "거의 변화 없음"
            engineer_note(f"다른 선택 조건을 고정한 모델에서 {sweep} 최소→최대 변화 시 예측 CD는 {curve[0]:.2f}→{curve[-1]:.2f} nm로 {direction}합니다.", "이 곡선은 현재 모델이 학습한 조건부 반응을 직관적으로 점검하는 도구입니다. PR tone을 바꾸면 방향이 달라지는지도 비교해야 합니다.", "관심 후보 조건을 좁힌 뒤 실제 wafer DOE에서 중심값·산포·결함을 함께 측정해 재검증합니다.", "한 변수 sweep은 다른 조건이 실제 공정에서 독립적으로 고정 가능하다고 보장하지 않으며 외삽은 신뢰도가 낮습니다.")
    with tabs[5]:
        st.header("Validation"); guide("지표를 어떻게 판단하나요?", "R²는 평균 예측 대비 설명력, RMSE는 큰 오차에 더 민감한 nm 오차, MAE는 전형적인 절대 nm 오차입니다. 단일 분할보다 30회 반복·Lot 검증·방향 안정성을 함께 봅니다."); cards = st.columns(3); cards[0].metric("Validation R²", f"{baseline.metrics['validation_r2']:.3f}"); cards[1].metric("RMSE", f"{baseline.metrics['validation_rmse_nm']:.3f} nm"); cards[2].metric("MAE", f"{baseline.metrics['validation_mae_nm']:.3f} nm")
        repeated, summary, _ = repeated_validation(data); lots, _ = lot_group_validation(data, min(8, data.lot_id.nunique()))
        vt = st.tabs(["30회 반복", "데이터 품질", "Lot", "Dose 방향"])
        with vt[0]:
            model2_summary = summary[summary.model.eq("Model 2")]; st.dataframe(model2_summary, width="stretch")
            r2_row = model2_summary[model2_summary.metric.eq("validation_r2")].iloc[0]
            engineer_note(f"30회 Validation R² 평균 {r2_row['mean']:.3f}, 표준편차 {r2_row['std']:.3f}입니다.", "평균 점수와 흔들림을 분리해서 봅니다. 평균이 양수여도 표준편차가 크면 새로운 데이터에서 성능 불확실성이 큽니다.", "분할별 실패 사례와 극단 오차를 확인하고, 단일 R² 대신 평균·표준편차·최솟값을 모델 승인 기준에 포함합니다.", "반복 random split도 시간·Tool·Lot 구조 누수를 완전히 제거하지는 않습니다.")
        with vt[1]:
            st.dataframe(quality_summary, width="stretch")
            r2q = quality_summary[quality_summary.metric.eq("validation_r2")]; qmap = dict(zip(r2q.condition, r2q["mean"])); inc=qmap.get("A_including_flagged",np.nan); exc=qmap.get("B_excluding_5_flagged_rows",np.nan)
            engineer_note(f"오류 후보 포함/검토 제외 반복 R² 평균은 {inc:.3f}/{exc:.3f}입니다.", "점수 상승을 삭제 정당화로 읽지 않고, 일부 입력값이 모델 안정성을 크게 움직인다는 데이터 품질 경고로 읽습니다.", "해당 5행의 설비·recipe 원본을 확인하고 수정 근거가 있을 때만 보정본을 별도 버전으로 관리합니다.", "검토 제외 결과는 민감도 분석이며 실제 오류 확정이나 최종 성능이 아닙니다.")
        with vt[2]:
            st.dataframe(lots, width="stretch")
            worst = lots.loc[lots.validation_r2.idxmin()]
            engineer_note(f"Lot holdout 중 가장 낮은 fold R²는 {worst.validation_r2:.3f}, RMSE는 {worst.validation_rmse_nm:.3f} nm입니다.", "특정 unseen Lot에서 성능이 낮다면 Lot별 재료·장비·recipe 구성 또는 극단 CD가 모델 범위를 벗어났는지 확인합니다.", f"Fold {int(worst.fold)}의 validation Lot과 큰 잔차 sample을 추적하고 Lot metadata를 추가 비교합니다.", "Fold 차이는 Lot 원인의 증명이 아니며 validation Lot 구성과 표본 수 영향을 받습니다.")
        with vt[3]:
            m2 = repeated[repeated.model.eq("Model 2")]; pos_ok=int((m2.positive_dose_slope_nm_per_pct_point<0).sum()); neg_ok=int((m2.negative_dose_slope_nm_per_pct_point>0).sum()); c1, c2 = st.columns(2); c1.metric("Positive 음(-)", f"{pos_ok}/30"); c2.metric("Negative 양(+)", f"{neg_ok}/30")
            engineer_note(f"Positive 음의 방향 {pos_ok}/30회, Negative 양의 방향 {neg_ok}/30회입니다.", "예측 점수의 크기와 dose 방향의 안정성은 다른 질문입니다. 점수가 흔들려도 방향이 반복되면 DOE 우선순위를 정하는 가설로 사용할 수 있습니다.", "tone별 dose DOE에서 방향과 산포를 재현하고 Tool block을 포함해 공정창 후보를 검증합니다.", "방향 반복은 인과효과나 최적 dose를 증명하지 않습니다.")
    with tabs[6]:
        st.info("Target CD가 없는 CSV/XLSX 업로드 시 고정 Model 2 예측과 다운로드가 활성화됩니다.")
        engineer_note("현재 분석 데이터에는 실제 CD Target이 있어 Analysis Mode로 실행 중입니다.", "Blind Holdout은 정답을 숨긴 최종 예측용이며 모델 선택이나 변수 튜닝에 사용하면 평가 누수가 발생합니다.", "모델 구조를 확정한 뒤 Holdout 예측을 저장하고, 정답 공개 후에만 최종 성능을 한 번 평가합니다.", "정답 없는 Holdout에서는 R²·RMSE·MAE를 계산할 수 없습니다.")
    with tabs[7]:
        final_engineering_report(raw, data, duplicates, flags, baseline, quality_summary, repeated, lots, st.session_state.get("custom_model"), st.session_state.get("logistic_model"))
