# 반도체 AI 프로젝트 주제·수식·데이터 카탈로그

이 문서는 10개 프로젝트 중 하나를 고른 뒤 **문제 → 전공 원리 → 데이터 → 검증 → 엔지니어의 결정**으로 연결하기 위한 출발점이다.

## 공통 사용 원칙

1. A 또는 B 데이터 중 배정받은 버전 하나만 사용한다. 두 버전은 스키마는 같지만 숨은 상호작용과 편향이 다르다.
2. `train.csv`는 805행, `holdout_features.csv`는 200행이다. Holdout 정답은 공개하지 않는다.
3. 아래 수식은 정답이 아니라 **검증할 물리·통계 가설**이다. 적용 가정, 단위, 재료와 장비 조건을 확인한다.
4. 상관관계를 인과관계로 쓰지 않는다. 대안 설명과 추가 DOE를 함께 제시한다.
5. 실제 Fab 데이터, 내부 Spec, 장비 로그, 고객정보는 사용하지 않는다.

- [전체 데이터 스키마](../datasets/schema.json)

## 01. Photo PR 공정 — 기본

- **목적:** PR tone·Dose·Focus·열처리·현상 조건 중 다음 DOE 후보를 선택한다.
- **방향:** CD뿐 아니라 CDU·LER·Scum·Collapse 위험을 함께 보고, Dose×Focus 및 두께×PEB 상호작용을 검증한다.
- **교과:** 반도체 공정개론, 광학, 고분자·재료화학, 공학통계·DOE.
- **수식 후보:** `CD ≈ k₁λ/NA`, `DOF ≈ k₂λ/NA²`, `I(z)=I₀exp(-αz)`.
- **완료 기준:** 목표 CD와 위험 한도를 만족하는 후보 3개, Holdout 성능, 추가 DOE 축을 제시한다.
- **다운로드:** [A train](../datasets/student/01_photo/A/train.csv) · [A holdout](../datasets/student/01_photo/A/holdout_features.csv) · [B train](../datasets/student/01_photo/B/train.csv) · [B holdout](../datasets/student/01_photo/B/holdout_features.csv)

## 02. Overlay 보정 — 기본

- **목적:** Global 보정계수와 우선 확인할 Local field를 분리한다.
- **방향:** Translation·Rotation·Magnification 모델을 먼저 적합하고 잔차 Hot Spot을 찾는다.
- **교과:** 노광·정렬계측, 선형대수, 회귀·SPC, 공간 데이터 시각화.
- **수식 후보:** `Δx=Tₓ+Mₓx-Ry`, `Δy=Tᵧ+Rx+Mᵧy`, `r=측정값-예측값`.
- **완료 기준:** 보정 전후 residual·합격률과 Local 조사 대상 Field 3곳을 제시한다.
- **다운로드:** [A train](../datasets/student/02_overlay/A/train.csv) · [A holdout](../datasets/student/02_overlay/A/holdout_features.csv) · [B train](../datasets/student/02_overlay/B/train.csv) · [B holdout](../datasets/student/02_overlay/B/holdout_features.csv)

## 03. Dry Etch Endpoint — 중급

- **목적:** Endpoint 종료 시점과 과식각 위험을 함께 판단한다.
- **방향:** OES ratio·slope와 RF·압력·Gas·Chamber age를 결합해 종료 규칙을 검증한다.
- **교과:** 플라즈마 공정, 표면반응·물질전달, OES 계측, 시계열·변화점 탐지.
- **수식 후보:** `Retch≈Δdepth/Δt`, `Selectivity=Rtarget/Rmask`, `Over-etch=(t-tEP)/tEP`.
- **완료 기준:** 오탐·미탐·지연을 함께 평가한 안전한 종료 규칙을 제시한다.
- **다운로드:** [A train](../datasets/student/03_dry_etch/A/train.csv) · [A holdout](../datasets/student/03_dry_etch/A/holdout_features.csv) · [B train](../datasets/student/03_dry_etch/B/train.csv) · [B holdout](../datasets/student/03_dry_etch/B/holdout_features.csv)

## 04. HAR Etch Profile — 고급

- **목적:** Depth·Top/Bottom CD·Sidewall·Bowing을 만족하는 공정창을 찾는다.
- **방향:** Aspect ratio와 Pattern density에 따른 ARDE·Microloading을 경험식으로 검증한다.
- **교과:** 플라즈마 식각, 미세구조 수송, 표면반응·Passivation, 단면계측·다목적 최적화.
- **수식 후보:** `AR=depth/opening CD`, `R=R₀f(AR, pattern density)`.
- **완료 기준:** Profile 제약 영역, 실패 모드별 민감인자, 다음 단면 DOE 3개를 제시한다.
- **다운로드:** [A train](../datasets/student/04_har_etch/A/train.csv) · [A holdout](../datasets/student/04_har_etch/A/holdout_features.csv) · [B train](../datasets/student/04_har_etch/B/train.csv) · [B holdout](../datasets/student/04_har_etch/B/holdout_features.csv)

## 05. CMP 최적화 — 기본

- **목적:** 제거율과 WIWNU·Dishing·Erosion을 균형 있게 보는 Recipe를 선택한다.
- **방향:** Preston 관계를 기준으로 Pad age·Pattern density의 조건부 오차와 Pareto 후보를 찾는다.
- **교과:** Tribology, 유체역학, 표면화학, 반응표면법·다목적 최적화.
- **수식 후보:** `RR=kₚPV`, Pareto 비지배 조건.
- **완료 기준:** 현재 Recipe보다 나은 후보와 Tool·Pad age별 Holdout 강건성을 제시한다.
- **다운로드:** [A train](../datasets/student/05_cmp/A/train.csv) · [A holdout](../datasets/student/05_cmp/A/holdout_features.csv) · [B train](../datasets/student/05_cmp/B/train.csv) · [B holdout](../datasets/student/05_cmp/B/holdout_features.csv)

## 06. 증착 Run-to-Run APC — 중급

- **목적:** 두께 Drift를 감지하고 다음 Run의 Cycle 보정량을 선택한다.
- **방향:** Chamber age·정비 후 시간에 따른 Drift와 두께·균일도·저항 proxy를 함께 본다.
- **교과:** ALD/CVD, 표면반응속도론, 열·물질전달, EWMA·Run-to-Run 제어.
- **수식 후보:** `k=Aexp(-Eₐ/kBT)`, `thickness≈cycles×GPC`, `uₖ₊₁=uₖ+K(y*-yₖ)`.
- **완료 기준:** Drift에서 오차를 줄이는 보정기와 과보정·적용 금지 조건을 제시한다.
- **다운로드:** [A train](../datasets/student/06_deposition_apc/A/train.csv) · [A holdout](../datasets/student/06_deposition_apc/A/holdout_features.csv) · [B train](../datasets/student/06_deposition_apc/B/train.csv) · [B holdout](../datasets/student/06_deposition_apc/B/holdout_features.csv)

## 07. 설비 FDC — 중급

- **목적:** 이상 유형과 수율 손실 위험으로 점검할 센서·조건의 우선순위를 정한다.
- **방향:** 단변량 Control chart와 다변량 이상탐지를 비교하고 Recall·False alarm·지연을 함께 본다.
- **교과:** 센서계측, SPC, 다변량통계·시계열, 신뢰성·FDC 운영.
- **수식 후보:** `z=(x-μ)/σ`, `EWMAₜ=λxₜ+(1-λ)EWMAₜ₋₁`, `D²=(x-μ)ᵀΣ⁻¹(x-μ)`.
- **완료 기준:** 기준 경보보다 나은지 검증하고, 경보마다 점검 변수와 오탐 위험을 표시한다.
- **다운로드:** [A train](../datasets/student/07_fdc/A/train.csv) · [A holdout](../datasets/student/07_fdc/A/holdout_features.csv) · [B train](../datasets/student/07_fdc/B/train.csv) · [B holdout](../datasets/student/07_fdc/B/holdout_features.csv)

## 08. DRAM Cell Transistor — 중급

- **목적:** Vth·Ion·Ioff·Retention·수율을 함께 만족하는 공정창을 찾는다.
- **방향:** MOS 물리 관계를 방향성 기준으로 사용하고 Monte Carlo 또는 bootstrap으로 불확실성을 표시한다.
- **교과:** MOSFET 소자, 소자공정, 통계적 변동성, 메모리 Cell·Retention.
- **수식 후보:** `Vth=VFB+2φF+√(4qεSiNAφF)/Cox`, `Cox=εox/EOT`.
- **완료 기준:** Spec yield와 Retention 위험을 함께 본 강건한 공정 후보를 제시한다.
- **다운로드:** [A train](../datasets/student/08_dram/A/train.csv) · [A holdout](../datasets/student/08_dram/A/holdout_features.csv) · [B train](../datasets/student/08_dram/B/train.csv) · [B holdout](../datasets/student/08_dram/B/holdout_features.csv)

## 09. 3D NAND Vth Window — 고급

- **목적:** P/E·Retention·Layer·State별 Read window 축소와 오류 위험을 판단한다.
- **방향:** State별 Vth 평균과 σ를 함께 보고 Read reference 조정과 공정 개선 구간을 분리한다.
- **교과:** 비휘발성 메모리, 터널링·Charge trap, 신뢰성·열화, Read reference·ECC.
- **수식 후보:** `J∝E²exp(-B/E)`, `Window≈|μᵢ-μⱼ|-c(σᵢ+σⱼ)`; Retention은 log(time)와 stretched 관계를 비교한다.
- **완료 기준:** 오류 급증 조건과 Reference 조정·추가 신뢰성 시험의 우선순위를 제시한다.
- **다운로드:** [A train](../datasets/student/09_nand/A/train.csv) · [A holdout](../datasets/student/09_nand/A/holdout_features.csv) · [B train](../datasets/student/09_nand/B/train.csv) · [B holdout](../datasets/student/09_nand/B/holdout_features.csv)

## 10. Photo–Etch–CMP Virtual Lot — 고급

- **목적:** 최종 전기특성·수율 변동에 가장 크게 기여한 공정과 다음 실험을 선택한다.
- **방향:** 공정 순서대로 변수를 정렬하고 baseline·상호작용 모델·민감도를 비교하되 인과로 과장하지 않는다.
- **교과:** 공정통합, 오차전파, 다변량 회귀·민감도, 수율공학·DOE.
- **수식 후보:** `y=fCMP(fEtch(fPhoto(x)))`, `σy²≈JΣxJᵀ`, `Final CD≈Photo CD+Etch bias+interaction`.
- **완료 기준:** 병목 후보와 대안 설명을 함께 쓰고 정보가치를 높일 추가 실험 3개를 고른다.
- **다운로드:** [A train](../datasets/student/10_virtual_lot/A/train.csv) · [A holdout](../datasets/student/10_virtual_lot/A/holdout_features.csv) · [B train](../datasets/student/10_virtual_lot/B/train.csv) · [B holdout](../datasets/student/10_virtual_lot/B/holdout_features.csv)

## 최종 제출물

- `PLAN.md`: 사용자, 결정, KPI, 하지 않을 일
- `research/SOURCES.md`: 공식 문서·논문과 확인 범위
- 데이터 감사 리포트: 스키마, 결측, 이상치, 편향, 누수
- 기준모델과 개선모델 비교
- Holdout 입력에 대한 예측 파일
- 오차 사례 3건과 대안 설명
- 다음 DOE 또는 확인할 설비·공정 조건 3개
- GitHub Pages URL과 3분 발표 자료

