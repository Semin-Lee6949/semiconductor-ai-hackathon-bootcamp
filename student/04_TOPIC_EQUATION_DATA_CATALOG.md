# 반도체 AI 팀 탐구 가이드

이 문서는 정답지가 아니다. 팀이 **질문 → 가설 → 반박 → 데이터 검증 → 가설 수정**을 반복하도록 돕는 진행 카드다.

## 답을 얻기 전에 지킬 규칙

1. 처음 15분은 AI에게 수식·모델·결론을 묻지 않는다.
2. 각자 최초 가설을 한 문장으로 적은 뒤 공개한다.
3. A 또는 B 데이터 중 배정받은 하나만 사용한다. 두 버전의 차이는 공개하지 않는다.
4. `train.csv` 805행으로 가설을 만들고, 정답 없는 `holdout_features.csv` 200행으로 검증한다.
5. 수식을 찾으면 출처, 단위, 성립 가정, 적용할 수 없는 조건을 함께 기록한다.
6. 상관관계에는 반드시 대안 설명을 한 개 이상 붙인다.
7. 실제 Fab 데이터·내부 Spec·장비 로그·고객정보는 사용하지 않는다.

- [전체 데이터 스키마](../datasets/schema.json)

## 4인 티키타카 진행법

한 라운드는 12분이며, 매 라운드가 끝나면 역할을 바꾼다.

1. **문제 제기자:** 누가 이 결과를 보고 어떤 결정을 하는가?
2. **물리 담당:** 단위·경계조건·성립 가정은 무엇인가?
3. **데이터 회의론자:** 같은 패턴을 만드는 다른 원인은 무엇인가?
4. **검증 담당:** 어떤 결과가 나오면 이 가설을 버릴 것인가?

AI에는 다음처럼 요청한다.

> 우리의 가설을 대신 완성하지 마라. 빠진 가정, 반례, 필요한 추가 데이터에 관한 질문을 한 번에 하나씩 하라.

## 힌트 사용 순서

- **힌트 0:** 데이터 사전만 읽고 변수 역할을 팀이 분류한다.
- **힌트 1:** 아래 대학 교과 범위를 나눠 조사한다.
- **힌트 2:** 어떤 물리량 사이의 관계를 찾아야 하는지만 확인한다.
- **힌트 3:** 강의노트·교재·논문 원문에서 식을 직접 찾아 단위와 가정을 검증한다.
- **교수 힌트:** 두 번의 가설 수정 후에도 막힌 팀만 요청한다.

---

## 01. Photo PR 공정 — 기본

- **미션:** 어떤 조건을 다음 DOE 후보로 고를지 결정할 도구를 만든다.
- **교과 탐색:** 반도체 노광, 광학, PR 재료화학, 공학통계·DOE.
- **찾을 관계:** 파장·NA·패턴 크기, 초점 여유, PR 깊이 방향의 광 세기.
- **반박 질문:** CD만 맞으면 좋은 조건인가? PR 종류가 달라도 같은 관계인가?
- **증거:** 최초 가설과 수정본, 조건별 오차, 실패 사례, 다음 DOE 3개.
- **데이터:** [A train](../datasets/student/01_photo/A/train.csv) · [A holdout](../datasets/student/01_photo/A/holdout_features.csv) · [B train](../datasets/student/01_photo/B/train.csv) · [B holdout](../datasets/student/01_photo/B/holdout_features.csv)

## 02. Overlay 보정 — 기본

- **미션:** Global 보정과 Local 확인이 필요한 Field를 구분한다.
- **교과 탐색:** 정렬계측, 선형대수, 회귀·SPC, 공간 시각화.
- **찾을 관계:** 좌표계의 이동·회전·확대, 보정 후 잔차의 정의.
- **반박 질문:** 잔차가 크면 항상 Local 공정 문제인가? 계측 품질은 어떻게 분리하는가?
- **증거:** 보정 전후 비교, Wafer map, 반례 Field, 추가 계측 제안.
- **데이터:** [A train](../datasets/student/02_overlay/A/train.csv) · [A holdout](../datasets/student/02_overlay/A/holdout_features.csv) · [B train](../datasets/student/02_overlay/B/train.csv) · [B holdout](../datasets/student/02_overlay/B/holdout_features.csv)

## 03. Dry Etch Endpoint — 중급

- **미션:** 종료 시점과 과식각 위험을 함께 판단하는 규칙을 설계한다.
- **교과 탐색:** 플라즈마 공정, 표면반응·물질전달, OES, 시계열·변화점.
- **찾을 관계:** 깊이와 시간, Target과 Mask 속도, Endpoint 이후 추가시간.
- **반박 질문:** OES 변화가 공정 종료 때문이라는 증거는 무엇인가? Chamber age가 교란하는가?
- **증거:** 기준 규칙, 오탐·미탐·지연, 실패 Run, 추가 센서 제안.
- **데이터:** [A train](../datasets/student/03_dry_etch/A/train.csv) · [A holdout](../datasets/student/03_dry_etch/A/holdout_features.csv) · [B train](../datasets/student/03_dry_etch/B/train.csv) · [B holdout](../datasets/student/03_dry_etch/B/holdout_features.csv)

## 04. HAR Etch Profile — 고급

- **미션:** 단면 품질 조건을 만족하는 공정 영역을 찾는다.
- **교과 탐색:** 플라즈마 식각, 미세구조 수송, Passivation, 단면계측.
- **찾을 관계:** 깊이와 입구 폭, 종횡비·패턴밀도와 속도, 깊이 방향 CD.
- **반박 질문:** 속도 저하가 종횡비 때문인가, 패턴밀도 때문인가? 측정 위치가 결론을 바꾸는가?
- **증거:** Profile 제약, 경쟁 가설, 실패 모드, 다음 단면 DOE.
- **데이터:** [A train](../datasets/student/04_har_etch/A/train.csv) · [A holdout](../datasets/student/04_har_etch/A/holdout_features.csv) · [B train](../datasets/student/04_har_etch/B/train.csv) · [B holdout](../datasets/student/04_har_etch/B/holdout_features.csv)

## 05. CMP 최적화 — 기본

- **미션:** 제거율과 품질 손실을 함께 보는 Recipe 후보를 고른다.
- **교과 탐색:** Tribology, 유체역학, 표면화학, 다목적 최적화.
- **찾을 관계:** 압력·상대속도와 제거율, Pad age·Pattern density의 영향.
- **반박 질문:** 제거율이 높으면 좋은 Recipe인가? 한 Tool에서만 성립하는가?
- **증거:** 단일 KPI 기준과 비교, 비지배 후보, 조건별 실패, 다음 실험.
- **데이터:** [A train](../datasets/student/05_cmp/A/train.csv) · [A holdout](../datasets/student/05_cmp/A/holdout_features.csv) · [B train](../datasets/student/05_cmp/B/train.csv) · [B holdout](../datasets/student/05_cmp/B/holdout_features.csv)

## 06. 증착 Run-to-Run APC — 중급

- **미션:** Drift를 감지하고 다음 Run 보정 여부를 판단한다.
- **교과 탐색:** ALD/CVD, 표면반응속도론, 열·물질전달, 공정제어.
- **찾을 관계:** 온도와 반응속도, Cycle과 두께, 이전 오차와 다음 보정.
- **반박 질문:** Drift인가 계측 이상인가? 보정이 오히려 진동을 만드는 조건은 무엇인가?
- **증거:** 기준 보정과 비교, 과보정 사례, 적용 금지 조건, 추가 계측.
- **데이터:** [A train](../datasets/student/06_deposition_apc/A/train.csv) · [A holdout](../datasets/student/06_deposition_apc/A/holdout_features.csv) · [B train](../datasets/student/06_deposition_apc/B/train.csv) · [B holdout](../datasets/student/06_deposition_apc/B/holdout_features.csv)

## 07. 설비 FDC — 중급

- **미션:** 경보가 발생했을 때 점검할 변수의 우선순위를 정한다.
- **교과 탐색:** 센서계측, SPC, 다변량통계·시계열, 신뢰성.
- **찾을 관계:** 서로 다른 단위의 표준화, 최근 값의 가중, 변수 간 상관을 반영한 거리.
- **반박 질문:** 정상 범위를 벗어나면 고장인가? False alarm과 Miss 중 어느 비용이 큰가?
- **증거:** 기준 경보와 비교, 오탐·미탐, 점검 순서, 적용 한계.
- **데이터:** [A train](../datasets/student/07_fdc/A/train.csv) · [A holdout](../datasets/student/07_fdc/A/holdout_features.csv) · [B train](../datasets/student/07_fdc/B/train.csv) · [B holdout](../datasets/student/07_fdc/B/holdout_features.csv)

## 08. DRAM Cell Transistor — 중급

- **미션:** 여러 전기특성과 수율을 함께 만족하는 공정 영역을 찾는다.
- **교과 탐색:** MOSFET, 소자공정, 통계적 변동성, 메모리 Cell.
- **찾을 관계:** Gate·절연막·Dose와 Vth, 성능과 누설의 Trade-off, 산포와 수율.
- **반박 질문:** 평균이 같아도 수율이 달라지는가? 구조와 Bias 가정이 바뀌면 관계가 유지되는가?
- **증거:** 물리 가정, 산포, Spec 충돌, 실패 조건, 추가 소자 실험.
- **데이터:** [A train](../datasets/student/08_dram/A/train.csv) · [A holdout](../datasets/student/08_dram/A/holdout_features.csv) · [B train](../datasets/student/08_dram/B/train.csv) · [B holdout](../datasets/student/08_dram/B/holdout_features.csv)

## 09. 3D NAND Vth Window — 고급

- **미션:** Read 오류가 커지는 조건과 추가 신뢰성 시험을 고른다.
- **교과 탐색:** 비휘발성 메모리, 터널링·Charge trap, 신뢰성, ECC.
- **찾을 관계:** 전계와 터널링, State 평균·폭과 Window, Retention 시간과 분포 변화.
- **반박 질문:** 평균 이동만으로 오류를 설명할 수 있는가? Layer·온도·P/E가 서로 교란하는가?
- **증거:** 경쟁 시간모델 비교, 오류 조건, 반례 State, 추가 시험.
- **데이터:** [A train](../datasets/student/09_nand/A/train.csv) · [A holdout](../datasets/student/09_nand/A/holdout_features.csv) · [B train](../datasets/student/09_nand/B/train.csv) · [B holdout](../datasets/student/09_nand/B/holdout_features.csv)

## 10. Photo–Etch–CMP Virtual Lot — 고급

- **미션:** 최종 결과에 기여한 병목 후보와 다음 실험을 고른다.
- **교과 탐색:** 공정통합, 오차전파, 민감도분석, 수율·DOE.
- **찾을 관계:** 공정 순서의 함수 연결, 앞 공정 산포의 전달, 상호작용.
- **반박 질문:** 민감도가 크면 원인인가? 측정하지 않은 공통 원인이 있는가?
- **증거:** 병목 후보와 대안 설명, 모델 간 차이, 실패 Lot, 추가실험 3개.
- **데이터:** [A train](../datasets/student/10_virtual_lot/A/train.csv) · [A holdout](../datasets/student/10_virtual_lot/A/holdout_features.csv) · [B train](../datasets/student/10_virtual_lot/B/train.csv) · [B holdout](../datasets/student/10_virtual_lot/B/holdout_features.csv)

## 팀 제출물

정답보다 **사고가 바뀐 과정**을 평가한다.

1. 팀원별 최초 가설
2. 상대가 제기한 반박과 대안 설명
3. 수정한 가설과 수정 이유
4. 직접 찾은 수식의 원문 출처·단위·가정·적용 불가 조건
5. 데이터 감사와 기준모델
6. Holdout 예측과 실패 사례 3건
7. 추가 DOE 또는 계측 제안
8. AI가 틀린 부분과 사람이 수정한 근거

