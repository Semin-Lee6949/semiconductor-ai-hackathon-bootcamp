"""Build the offline Photo CD portfolio report from verified STEP 2-5 outputs."""

from __future__ import annotations

import base64
import html
from html.parser import HTMLParser
from pathlib import Path
import re

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
OUTPUTS = PROJECT / "outputs"
REPORT = PROJECT / "report" / "index.html"


class ReportParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.images: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(str(values["id"]))
        if tag == "img":
            self.images.append(str(values.get("src", "")))


def image_uri(relative: str) -> str:
    path = OUTPUTS / relative
    mime = "image/svg+xml" if path.suffix.lower() == ".svg" else "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def metric(frame: pd.DataFrame, **filters: str) -> pd.Series:
    selected = frame
    for column, value in filters.items():
        selected = selected[selected[column].eq(value)]
    if len(selected) != 1:
        raise ValueError(f"Expected one metric row for {filters}, found {len(selected)}")
    return selected.iloc[0]


def build() -> str:
    audit = pd.read_csv(OUTPUTS / "data_audit/data_audit_summary.csv")
    missing = pd.read_csv(OUTPUTS / "data_audit/missing_summary.csv")
    duplicates = pd.read_csv(OUTPUTS / "data_audit/duplicate_summary.csv")
    groups = pd.read_csv(OUTPUTS / "data_audit/group_counts.csv")
    flagged = pd.read_csv(OUTPUTS / "eda/excluded_or_flagged_rows.csv")
    corr = pd.read_csv(OUTPUTS / "eda/correlation_by_pr_tone.csv")
    models = pd.read_csv(OUTPUTS / "modeling/model_comparison.csv")
    coefs = pd.read_csv(OUTPUTS / "modeling/coefficient_table.csv")
    repeated = pd.read_csv(OUTPUTS / "validation/repeated_validation.csv")
    repeated_summary = pd.read_csv(OUTPUTS / "validation/repeated_validation_summary.csv")
    lot_summary = pd.read_csv(OUTPUTS / "validation/lot_group_validation_summary.csv")
    quality = pd.read_csv(OUTPUTS / "validation/data_quality_sensitivity_summary.csv")
    thickness = pd.read_csv(OUTPUTS / "validation/thickness_comparison.csv")

    rows = int(metric(audit, section="dataset", item="rows")["value"])
    columns = int(metric(audit, section="dataset", item="columns")["value"])
    missing_total = int(missing["missing_count"].sum())
    duplicate_extra = int(metric(duplicates, check="exact_full_row")["extra_rows"])
    tool_rows = groups[(groups.group_type == "tool_id") & (groups.pr_tone == "ALL")]
    tool_cards = "".join(
        f'<div><strong>{html.escape(r.group_value)}</strong><span>{int(r["count"]):,}행 · {r.pct_of_dataset:.1f}%</span></div>'
        for _, r in tool_rows.iterrows()
    )
    tone_counts = {
        r["item"]: int(r["value"])
        for _, r in audit[audit.section.eq("pr_tone_distribution")].iterrows()
    }

    model_rows = models[(models.analysis == "original_including_flagged") & (models.split == "Validation")]
    m2 = metric(model_rows, model="Model 2")
    model_table = "".join(
        f'<tr class="{"selected" if r.model == "Model 2" else ""}"><td>{r.model}</td><td>{int(r.n_features)}</td>'
        f'<td>{r.r2:.3f}</td><td>{r.rmse_nm:.3f}</td><td>{r.mae_nm:.3f}</td></tr>'
        for _, r in model_rows.iterrows()
    )
    m2_coefs = coefs[(coefs.analysis == "original_including_flagged") & (coefs.model == "Model 2")]
    pos_coef = float(metric(m2_coefs, term="derived_dose_slope_POSITIVE")["coefficient"])
    neg_coef = float(metric(m2_coefs, term="derived_dose_slope_NEGATIVE")["coefficient"])
    t02 = float(metric(m2_coefs, term="tool_id_T02")["coefficient"])
    t03 = float(metric(m2_coefs, term="tool_id_T03")["coefficient"])

    rep_r2 = metric(repeated_summary, model="Model 2", metric="validation_r2")
    lot_r2 = metric(lot_summary, scope="pooled_out_of_fold", metric="validation_r2")
    rep_m2 = repeated[repeated.model.eq("Model 2")]
    pos_stable = int((rep_m2.positive_dose_slope_nm_per_pct_point < 0).sum())
    neg_stable = int((rep_m2.negative_dose_slope_nm_per_pct_point > 0).sum())
    quality_a = metric(quality, condition="A_including_flagged", metric="validation_r2")
    quality_b = metric(quality, condition="B_excluding_5_flagged_rows", metric="validation_r2")
    thickness_delta = float(thickness.delta_r2_thickness_minus_model2.mean())

    dose_corr = corr[(corr.variable == "normalized_dose_pct") & (corr.analysis == "flagged_excluded_sensitivity")]
    pos_corr = float(metric(dose_corr, pr_tone="POSITIVE")["pearson_r"])
    neg_corr = float(metric(dose_corr, pr_tone="NEGATIVE")["pearson_r"])

    assert (rows, columns, duplicate_extra, len(flagged)) == (805, 24, 5, 5)
    assert round(float(m2.r2), 3) == .679 and round(float(m2.rmse_nm), 3) == 1.661
    assert round(float(m2.mae_nm), 3) == 1.140
    assert round(float(rep_r2["mean"]), 3) == .458 and round(float(rep_r2["std"]), 3) == .210
    assert round(float(lot_r2["mean"]), 3) == .507
    assert (pos_stable, neg_stable) == (30, 30)
    assert round(float(quality_b["mean"]), 3) == .633 and round(float(quality_b["std"]), 3) == .086

    images = {name: image_uri(path) for name, path in {
        "audit": "data_audit/figures/tool_and_pr_tone_counts.svg",
        "dose": "eda/figures/scatter_normalized_dose_pct_flagged_excluded_sensitivity.png",
        "tool": "eda/figures/cd_distribution_by_tool_and_pr_tone.png",
        "models": "modeling/figures/model_performance.png",
        "repeat": "validation/figures/repeated_validation_performance.png",
        "slopes": "validation/figures/repeated_dose_slopes.png",
        "lot": "validation/figures/lot_group_validation_performance.png",
        "residual": "validation/figures/residual_mean_by_lot.png",
    }.items()}

    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Photo 공정 CD 분석 포트폴리오</title>
<style>
:root{{--ink:#142536;--muted:#5c6c79;--line:#d8e0e6;--paper:#f4f7f8;--navy:#163b59;--blue:#2374a8;--cyan:#dceff4;--orange:#d97735;--red:#b64b42;--white:#fff}}
*{{box-sizing:border-box}} html{{scroll-behavior:smooth}} body{{margin:0;background:var(--paper);color:var(--ink);font-family:"Pretendard","Noto Sans KR","Malgun Gothic",Arial,sans-serif;line-height:1.68}}
.hero{{background:linear-gradient(125deg,#102b40,#1c5678);color:white;padding:76px 24px 64px}} .wrap{{max-width:1120px;margin:auto}} .eyebrow{{font-size:.78rem;letter-spacing:.16em;text-transform:uppercase;font-weight:800;color:#92d3e4}} h1{{font-size:clamp(2.1rem,5vw,4rem);line-height:1.14;margin:.35rem 0 1rem}} .lead{{max-width:780px;font-size:1.08rem;color:#d8e7ed}} .meta{{display:flex;gap:12px;flex-wrap:wrap;margin-top:24px}} .meta span{{border:1px solid #ffffff44;border-radius:999px;padding:6px 12px;font-size:.82rem}}
nav{{position:sticky;top:0;z-index:5;background:#ffffffee;backdrop-filter:blur(10px);border-bottom:1px solid var(--line);overflow:auto;white-space:nowrap}} nav .wrap{{display:flex;gap:22px;padding:12px 18px}} nav a{{color:var(--navy);text-decoration:none;font-size:.82rem;font-weight:700}}
main{{padding:36px 20px 80px}} section{{background:white;border:1px solid var(--line);border-radius:16px;padding:clamp(24px,5vw,52px);margin:22px auto;box-shadow:0 7px 22px #17364d0b}} h2{{font-size:clamp(1.55rem,3vw,2.25rem);margin:0 0 8px;color:var(--navy)}} h3{{margin:1.5rem 0 .45rem;color:var(--navy)}} .section-kicker{{color:var(--orange);font-weight:800;font-size:.78rem;letter-spacing:.1em}} .section-intro{{color:var(--muted);max-width:800px;margin-top:0}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:24px 0}} .card{{border:1px solid var(--line);border-top:4px solid var(--blue);padding:18px;border-radius:10px;background:#fbfdfe}} .card strong{{display:block;font-size:1.8rem;line-height:1.2;color:var(--navy)}} .card span{{font-size:.78rem;color:var(--muted)}} .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:start}} .panel{{border:1px solid var(--line);border-radius:12px;padding:20px;background:#fbfcfd}} .panel h3{{margin-top:0}} .decision{{border-left:5px solid var(--orange);background:#fff7ef;padding:18px 20px;margin:22px 0;border-radius:0 10px 10px 0}} .finding{{border-left:5px solid var(--blue);background:#eff8fb;padding:18px 20px;border-radius:0 10px 10px 0}} .warning{{border-left-color:var(--red);background:#fff3f1}} .figure{{margin:24px 0}} .figure img{{width:100%;display:block;border:1px solid var(--line);border-radius:10px;background:white}} figcaption{{font-size:.78rem;color:var(--muted);margin-top:8px}}
table{{width:100%;border-collapse:collapse;font-size:.9rem;margin:18px 0}} th,td{{padding:10px 12px;border-bottom:1px solid var(--line);text-align:right}} th:first-child,td:first-child{{text-align:left}} th{{background:#edf3f6;color:var(--navy)}} tr.selected{{background:#eaf6f8;font-weight:800}} ul{{padding-left:1.2rem}} .flow{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:22px 0}} .flow div{{padding:16px;border-radius:9px;background:#edf4f7;font-size:.88rem}} .flow b{{display:block;color:var(--blue)}} .compare{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:22px 0}} .barbox{{padding:20px;border:1px solid var(--line);border-radius:12px}} .bar{{height:14px;background:#e5eaed;border-radius:8px;overflow:hidden;margin:10px 0}} .bar i{{display:block;height:100%;background:var(--red)}} .bar.good i{{background:#287f78}} .barbox strong{{font-size:1.55rem}} .two-roles{{display:grid;grid-template-columns:1fr 1fr;gap:0;border:1px solid var(--line);border-radius:14px;overflow:hidden}} .two-roles>div{{padding:26px}} .two-roles>div:first-child{{background:#edf4f7}} .two-roles>div:last-child{{background:#fff6eb}} .tag{{display:inline-block;border-radius:999px;background:#e8f2f6;padding:3px 9px;font-size:.74rem;font-weight:700;color:var(--navy)}} footer{{text-align:center;color:var(--muted);font-size:.78rem;padding:20px}}
@media(max-width:800px){{.cards,.flow{{grid-template-columns:repeat(2,1fr)}} .grid2,.compare,.two-roles{{grid-template-columns:1fr}} nav{{display:none}}}} @media(max-width:480px){{.cards,.flow{{grid-template-columns:1fr}} section{{padding:22px 18px}}}}
@media print{{nav{{display:none}} body{{background:white}} section{{break-inside:avoid;box-shadow:none}}}}
</style></head><body>
<header class="hero"><div class="wrap"><div class="eyebrow">Semiconductor Process AI Portfolio · Photo</div><h1>Photo 공정 CD 분석</h1><p class="lead">단일 점수보다 관계의 재현성과 데이터 품질을 먼저 확인한, 해석 가능한 CD 분석 사례. 교육용 합성 데이터에서 관찰된 연관성을 공정 가설과 분리해 보고한다.</p><div class="meta"><span>A/train · Holdout 미사용</span><span>805 rows × 24 columns</span><span>Interpretable Linear Model</span><span>Offline Single-file Report</span></div></div></header>
<nav><div class="wrap"><a href="#summary">Summary</a><a href="#problem">Problem</a><a href="#audit">Audit</a><a href="#eda">EDA</a><a href="#model">Model</a><a href="#validation">Validation</a><a href="#quality">Data Quality</a><a href="#engineering">Engineering</a><a href="#roles">AI vs Human</a><a href="#limits">Limits & DOE</a></div></nav>
<main class="wrap">
<section id="summary"><div class="section-kicker">01 · EXECUTIVE SUMMARY</div><h2>성능의 최고점보다, 무엇이 반복해서 유지되는가</h2><p class="section-intro">Photo 공정 엔지니어가 다음 DOE의 우선 조건을 좁힐 수 있도록 normalized dose, PR tone, Tool과 resist line CD의 관찰적 관계를 분석했다.</p>
<div class="cards"><div class="card"><strong>{rows}</strong><span>Train rows · 24 columns</span></div><div class="card"><strong>{float(rep_r2['mean']):.3f}</strong><span>30회 평균 Validation R²</span></div><div class="card"><strong>{float(lot_r2['mean']):.3f}</strong><span>Unseen-Lot pooled OOF R²</span></div><div class="card"><strong>30 / 30</strong><span>각 tone의 dose 방향 재현</span></div></div>
<div class="finding"><b>핵심 발견.</b> Positive PR에서는 dose 증가와 CD 감소, Negative PR에서는 dose 증가와 CD 증가가 함께 관찰됐고, 이 방향은 30회 반복 분할에서도 각각 30/30 유지됐다. Tool은 기준 T01 대비 CD 수준 차이를 보였다.</div>
<div class="decision"><b>최종 판단.</b> 단일 분할의 R² 0.679를 최종 성능으로 과장하지 않는다. 예측성능은 분할과 Lot에 따라 흔들렸지만 핵심 방향은 안정적이었다. 오류 의심 5행을 제외했을 때 평균 R²와 변동성이 크게 개선됐으므로, 복잡한 모델보다 원자료 입력·단위 확인을 먼저 수행한다.</div></section>

<section id="problem"><div class="section-kicker">02 · PROBLEM DEFINITION</div><h2>다음 DOE에서 무엇을 먼저 확인할 것인가</h2><div class="grid2"><div><h3>사용자와 결정</h3><p><b>실제 사용자:</b> Photo 공정 엔지니어</p><p><b>지원 결정:</b> PR tone과 Dose·Focus·PEB·현상조건 중 어떤 조합을 다음 DOE에서 우선 검증할지 좁힌다.</p><p><b>주 KPI:</b> resist_line_cd_nm. CDU, LER, Scum, Collapse, Defect, PASS/FAIL은 보조 품질지표이며 모델 입력에는 사용하지 않았다.</p></div><div><h3>왜 CD인가</h3><p>CD는 패턴 치수의 직접 지표이며 공정 조건 변화에 대한 민감도를 보여준다. 분석 목표는 “원인 확정”이 아니라, 관찰된 방향과 불안정 구간을 찾아 다음 검증 비용을 줄이는 것이다.</p><div class="tag">Coat → Softbake → Exposure → PEB → Develop → CD measurement</div></div></div>
<div class="flow"><div><b>1 · Audit</b>스키마·결측·중복·단위·편중 점검</div><div><b>2 · Hypothesis</b>tone별 방향과 대안 설명 사전 기록</div><div><b>3 · Compare</b>평균 baseline과 선형 Model 1~3 비교</div><div><b>4 · Challenge</b>반복 분할·Unseen Lot·오류 민감도 검증</div></div></section>

<section id="audit"><div class="section-kicker">03 · DATA AUDIT</div><h2>삭제보다 추적 가능한 검토</h2><div class="cards"><div class="card"><strong>{rows} × {columns}</strong><span>원본 구조</span></div><div class="card"><strong>{missing_total}</strong><span>총 결측 셀 · target 결측 0</span></div><div class="card"><strong>{duplicate_extra}</strong><span>완전 중복 추가행</span></div><div class="card"><strong>{len(flagged)}</strong><span>입력·단위 오류 의심행</span></div></div>
<div class="grid2"><div class="panel"><h3>PR tone 분포</h3><p>Positive {tone_counts['POSITIVE']:,}행 · Negative {tone_counts['NEGATIVE']:,}행 · Missing {tone_counts['MISSING']:,}행. tone 결측은 별도 MISSING 범주로 보존하고 물리적 tone 해석에서는 제외했다.</p><h3>Tool 편중</h3>{tool_cards}<p class="section-intro">T01이 59.1%로 가장 많아, 전체 관계가 Tool 구성에 의해 왜곡될 가능성을 대안 설명으로 유지했다.</p></div><figure class="figure"><img src="{images['audit']}" alt="Tool과 PR tone 표본 수"><figcaption>STEP 2 원본 산출물. 표본 구성은 균등하지 않다.</figcaption></figure></div>
<div class="decision warning"><b>인간 판단.</b> IQR 플래그 256건은 삭제 목록이 아니라 검토 목록이다. 그중 명백한 소수점·단위 입력 오류 후보 5행도 기본 분석에는 유지하고, 별도 민감도 분석에서만 제외했다. 완전 중복의 추가 복제 5행만 Train/Validation 누수를 막기 위해 제거했다.</div></section>

<section id="eda"><div class="section-kicker">04 · HYPOTHESIS & EDA</div><h2>사전 가설과 실제 관찰을 분리</h2><div class="grid2"><div class="panel"><h3>분석 전 가설</h3><p>Dose, Focus, PEB, 현상조건이 CD와 관련될 수 있다. 방향은 PR chemistry, retained pattern 정의, Tool·Lot 구성과 공정창에 따라 달라질 수 있다고 기록했다.</p></div><div class="panel"><h3>실제 관찰</h3><p>오류 후보를 해당 변수에서만 제외한 민감도 EDA에서 dose–CD Pearson r은 Positive {pos_corr:.3f}, Negative +{neg_corr:.3f}였다. 두 tone을 하나의 선으로 합치지 않았다.</p></div></div>
<figure class="figure"><img src="{images['dose']}" alt="PR tone별 normalized dose와 CD 산점도"><figcaption>핵심 EDA: Positive와 Negative를 분리한 quadratic visual guide. 추세선은 시각적 요약이며 인과효과가 아니다.</figcaption></figure>
<div class="finding"><b>약한 선형 상관 ≠ 관계 없음.</b> Focus의 Pearson r은 Positive -0.026, Negative 원본 -0.030으로 작았지만, focus는 0 주변의 비선형·비대칭 반응일 수 있어 “영향 없음”으로 단정하지 않았다. 2차 시각 가이드와 Model 3의 focus² 항을 반례 점검으로 사용했다.</div>
<figure class="figure"><img src="{images['tool']}" alt="Tool과 PR tone별 CD 분포"><figcaption>Tool별 CD level 차이가 관찰된다. Tool condition/calibration 또는 Tool과 함께 변한 다른 조건이 대안 설명이다.</figcaption></figure></section>

<section id="model"><div class="section-kicker">05 · BASELINE MODEL</div><h2>Model 2: 가장 단순한 유효 기준</h2><p class="section-intro">동일한 tone×Tool 층화 70/30 분할(seed 42)에서 평균 baseline과 해석 가능한 선형모델을 비교했다. 결측 대체값과 dose 중심값은 Train에서만 계산했다.</p>
<table><thead><tr><th>모델</th><th>특성 수</th><th>Validation R²</th><th>RMSE (nm)</th><th>MAE (nm)</th></tr></thead><tbody>{model_table}</tbody></table>
<div class="grid2"><div><h3>선택 특성</h3><ul><li>normalized_dose_pct</li><li>pr_tone 및 dose × pr_tone</li><li>tool_id</li></ul><p>Model 2는 <b>R² {m2.r2:.3f}, RMSE {m2.rmse_nm:.3f} nm, MAE {m2.mae_nm:.3f} nm</b>였다.</p></div><div><h3>조건부 계수</h3><ul><li>Positive dose slope: {pos_coef:.3f} nm/%p</li><li>Negative dose slope: +{neg_coef:.3f} nm/%p</li><li>T02 vs T01: +{t02:.3f} nm</li><li>T03 vs T01: +{t03:.3f} nm</li></ul><p class="section-intro">계수는 관찰 데이터의 조건부 연관이며 recipe 변경 효과가 아니다.</p></div></div>
<figure class="figure"><img src="{images['models']}" alt="Model 0부터 3까지 성능 비교"><figcaption>Model 3의 전체 변수 확장은 단일 Validation R²를 0.661로 낮췄다. 복잡성 추가가 자동으로 일반화 성능을 높이지 않았다.</figcaption></figure></section>

<section id="validation"><div class="section-kicker">06 · VALIDATION & FAILURE ANALYSIS</div><h2>점수의 흔들림과 방향의 안정성은 다른 질문이다</h2><div class="cards"><div class="card"><strong>{float(rep_r2['mean']):.3f}</strong><span>30회 평균 R²</span></div><div class="card"><strong>{float(rep_r2['std']):.3f}</strong><span>30회 R² 표준편차</span></div><div class="card"><strong>{float(lot_r2['mean']):.3f}</strong><span>Lot pooled OOF R²</span></div><div class="card"><strong>{pos_stable}/{pos_stable} · {neg_stable}/{neg_stable}</strong><span>Positive 음수 · Negative 양수</span></div></div>
<div class="finding"><b>검증 결론.</b> 예측성능 자체는 분할에 따라 흔들렸지만, 핵심 관계 방향은 반복 검증에서 안정적이었다. 이는 “높은 예측 정확도”와 “관찰된 방향의 재현성”을 구분해야 함을 보여준다.</div>
<div class="grid2"><figure class="figure"><img src="{images['repeat']}" alt="30회 반복검증 성능"><figcaption>30개 고정 seed의 Validation 분포. Model 2 R² 범위 {rep_r2['min']:.3f}~{rep_r2['max']:.3f}.</figcaption></figure><figure class="figure"><img src="{images['slopes']}" alt="반복검증 dose slope"><figcaption>모든 분할에서 Positive slope &lt; 0, Negative slope &gt; 0.</figcaption></figure></div>
<figure class="figure"><img src="{images['lot']}" alt="Lot Group Validation 성능"><figcaption>40개 Lot을 8 fold로 완전히 분리. fold R²는 -0.483~0.746으로 넓지만 pooled OOF R²는 {float(lot_r2['mean']):.3f}.</figcaption></figure>
<figure class="figure"><img src="{images['residual']}" alt="Lot별 평균 잔차"><figcaption>일부 Lot 평균 잔차가 ±0.5 nm를 넘는다. 미관측 Lot에 대한 구조적 차이 또는 극단값 영향은 추가 확인 대상이다.</figcaption></figure></section>

<section id="quality"><div class="section-kicker">07 · DATA QUALITY IMPACT</div><h2>낮은 점수에 모델을 더하기 전에 입력을 의심했다</h2><div class="compare"><div class="barbox"><span>오류 의심값 포함</span><br><strong>R² {float(quality_a['mean']):.3f} ± {float(quality_a['std']):.3f}</strong><div class="bar"><i style="width:{100*float(quality_a['mean']):.1f}%"></i></div><small>30회 반복검증</small></div><div class="barbox"><span>오류 의심 5행 제외</span><br><strong>R² {float(quality_b['mean']):.3f} ± {float(quality_b['std']):.3f}</strong><div class="bar good"><i style="width:{100*float(quality_b['mean']):.1f}%"></i></div><small>민감도 분석 · 삭제 확정 아님</small></div></div>
<div class="decision"><b>판단 순서.</b> “성능이 낮으니 복잡한 AI 모델을 추가한다”가 아니라 “먼저 데이터 품질 문제를 원자료에서 확인한다.” 제외 결과의 개선은 해당 행이 오류라는 증명이 아니라, 모델이 그 값들에 민감하다는 증거다.</div><p>Coat thickness 1개 추가는 반복검증 평균 R²를 {thickness_delta:+.3f}만큼 소폭 바꿨으나 변동성을 해결하지 못했다. 전체 변수 Model 3도 단일 Validation에서 Model 2보다 낮았다. 따라서 Random Forest로 즉시 이동하지 않았다.</p></section>

<section id="engineering"><div class="section-kicker">08 · ENGINEERING DISCUSSION</div><h2>데이터 관찰과 공정 가설 사이에 경계선 긋기</h2><div class="grid2"><div class="panel"><h3>확인된 데이터 관찰</h3><ul><li>tone별 dose–CD 방향이 반대이며 반복 분할에서도 유지됐다.</li><li>Tool별 CD level 차이가 관찰됐다.</li><li>입력 오류 의심값 포함 여부에 성능과 안정성이 민감했다.</li></ul></div><div class="panel"><h3>가능한 공정 해석 · 미검증 가설</h3><ul><li>PR tone 차이에 따른 dose response 가능성</li><li>Tool condition 또는 calibration 차이 가능성</li><li>Tool과 함께 변한 Lot·recipe 조건의 교란 가능성</li></ul></div></div><div class="decision warning"><b>해석 경계.</b> 이 방향은 교육용 합성 데이터의 특정 공정창에서 관찰된 결과다. 실제 Photo recipe의 일반 법칙으로 확장하지 않으며, 인과관계는 통제 DOE와 계측·recipe 확인 전에는 확정할 수 없다.</div></section>

<section id="roles"><div class="section-kicker">09 · WHAT AI DID / WHAT I DECIDED</div><h2>자동화와 엔지니어링 판단을 분리</h2><div class="two-roles"><div><h3>AI가 수행한 일</h3><ul><li>Python 분석 코드 작성</li><li>스키마·결측·중복·편중 반복 계산</li><li>그래프 생성</li><li>선형회귀와 Validation 실행</li><li>결과 CSV 정리 및 재현성 검사</li></ul></div><div><h3>사람이 판단한 일</h3><ul><li>Positive/Negative를 분리해 해석</li><li>이상치를 자동 삭제하지 않음</li><li>Tool 편중을 대안 설명으로 유지</li><li>단일 R²를 과신하지 않고 반복·Lot 검증</li><li>Random Forest로 바로 넘어가지 않음</li><li>데이터 품질 확인을 최우선 조치로 선택</li></ul></div></div><p class="section-intro">AI는 계산과 초안 생성을 가속했지만, 무엇을 믿고 보류할지, 어떤 검증을 추가할지는 사람이 결정했다.</p></section>

<section id="limits"><div class="section-kicker">10 · LIMITATIONS</div><h2>결론이 성립하는 범위</h2><div class="grid2"><div><ul><li>관찰 데이터이므로 인과관계 확정 불가</li><li>입력 오류 후보 존재</li><li>일부 극단값에서 모델 불안정</li><li>특정 합성 데이터셋에서 얻은 결과</li></ul></div><div><ul><li>실제 recipe 일반 법칙으로 확장 불가</li><li>Random Forest 등 복잡한 모델은 의도적으로 미사용</li><li>Holdout 최종 평가는 아직 미수행</li><li>PASS/FAIL 판정 기준은 확인되지 않음</li></ul></div></div></section>

<section id="doe"><div class="section-kicker">11 · NEXT ACTION / DOE</div><h2>다음 확인은 모델보다 현장 증거에 가깝게</h2><ol><li><b>원자료 확인:</b> 5개 오류 의심행의 장비 로그, 단위, 소수점, 전송 이력을 확인하고 정정 여부를 감사 로그에 남긴다.</li><li><b>계측·Tool 점검:</b> T01/T02/T03의 calibration, chamber/track condition, 계측기 offset과 Lot 배치를 분리해 확인한다.</li><li><b>Tone별 통제 DOE:</b> Positive/Negative를 분리하고 Tool을 block으로 둔 뒤, 현재 공정창 내 dose 수준을 반복 배치한다. Focus는 0 주변 대칭 수준을 포함해 비선형 가능성을 점검한다.</li><li><b>반증 기준 사전 정의:</b> tone별 slope 부호가 반복/Tool에서 뒤집히는지, Tool 보정 후 차이가 남는지, 극단값 없이도 재현되는지를 미리 판정 기준으로 둔다.</li><li><b>최종 Holdout:</b> 분석·모델 선택을 고정한 뒤에만 holdout을 1회 평가한다. 현재 보고서에는 holdout 성능을 주장하지 않는다.</li></ol><div class="finding"><b>DOE 제안은 다음 검증 순서다.</b> 현재 데이터가 위 메커니즘이나 recipe 효과를 증명했다는 뜻은 아니다.</div></section>
</main><footer>Generated from projects/01_photo STEP 2–5 outputs · No external assets · Holdout not evaluated</footer></body></html>'''


def main() -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    report = build()
    REPORT.write_text(report, encoding="utf-8")
    parser = ReportParser()
    parser.feed(report)
    expected = {"summary", "problem", "audit", "eda", "model", "validation",
                "quality", "engineering", "roles", "limits", "doe"}
    if not expected.issubset(parser.ids):
        raise AssertionError(f"Missing report sections: {sorted(expected - parser.ids)}")
    if len(parser.images) != 8 or not all(src.startswith("data:image/") for src in parser.images):
        raise AssertionError("Every report image must be an embedded data URI")
    for src in parser.images:
        base64.b64decode(src.split(",", 1)[1], validate=True)
    if re.search(r'<(?:script|link)[^>]+(?:src|href)=["\']https?://', report, re.I):
        raise AssertionError("External script or stylesheet dependency found")
    if re.search(r"(?:sk-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{20,})", report):
        raise AssertionError("Possible API secret found in report")
    required_text = ["0.679", "1.661", "1.140", "0.458", "0.210", "0.507",
                     "0.633", "0.086", "30 / 30", "Holdout 최종 평가는 아직 미수행"]
    if not all(value in report for value in required_text):
        raise AssertionError("A required verified result is missing from the report")
    print(f"Wrote and validated {REPORT} ({REPORT.stat().st_size:,} bytes, "
          f"{len(expected)} sections, {len(parser.images)} embedded images)")


if __name__ == "__main__":
    main()
