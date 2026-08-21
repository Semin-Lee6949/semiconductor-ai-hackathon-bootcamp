# AI 사용 기록

## 2026-08-21 — Workbench 시각 디자인 및 Model Lab 보완

- AI 작업: Streamlit 전역 테마를 밝은 네이비로 고정하고 상단 데이터 KPI, 문제·가설·대안 카드, 접이식 컬럼 스키마를 추가했다. Model Lab 안에서 공정 입력과 Dose×PR 상호작용을 직접 선택하도록 보완하고 Custom Model의 Train/Validation R², Validation 설명력(%), RMSE, MAE와 Model 2 비교를 표시했다.
- 시뮬레이션: 기준 조건과 선택 조건의 예측 CD를 선폭으로 비교하는 동적 CD line-width 스킴과 ΔCD 방향 표시를 추가했다. 기존 one-variable sweep 및 학습 범위 이탈 경고를 유지했다.
- 검증: 기본 A/train에서 Model 2 지표와 Custom Model 생성, KPI·그래프·CD 스킴 렌더링을 AppTest로 확인하고 Blind Holdout 200행 예측 경로를 재확인했다.
- 해석 제한: R² 백분율은 `R² × 100`의 가독성 표시이며 인과효과나 수율 보증 확률이 아니다. CD 시각화도 모델 기반 상대 비교다.
- 인간 판단: 복잡한 ML을 추가하지 않고 해석 가능한 Linear Regression과 기존 Model 2를 기준으로 유지했다.

## 2026-08-21 — Photo 4M1E Fishbone과 CD What-if 시뮬레이션

- AI 작업: EDA 종합 아래에 Machine·Material·Method·Man·Environment의 4M1E Fishbone UI를 추가하고, 각 가지에 현재 데이터 근거·미확인 정보·다음 점검 액션을 분리했다. Model 2의 PR tone·Tool·normalized dose를 직접 조절하는 What-if 시뮬레이터와 CD 폭 비교 그림, dose–예측 CD 곡선을 추가했다.
- 데이터 경계: Machine·Material·Method는 Tool 평균, tone별 dose 상관과 기존 EDA를 근거로 표시했다. 작업자·교대조·시간·온습도 정보는 데이터에 없으므로 Man/Environment 영향은 결론 내리지 않고 추가 수집 항목으로 표시했다.
- 모델 경계: 시뮬레이터는 A/train 전체로 고정한 기존 Model 2만 사용하고 dose 조절 범위를 A/train 1~99백분위로 제한했다. Focus·Bake·Develop·material lot은 Model 2 입력이 아니므로 예측에 반영되지 않는다고 명시했다.
- 해석 제한: 시뮬레이션 값은 관찰 데이터 기반 예측이며 recipe 변경의 인과효과, Spec 판정 또는 품질 보증값이 아니다.
- 검증: 기본 Analysis 지표 R² 0.679, RMSE 1.661 nm, MAE 1.140 nm를 유지했다. 시뮬레이터에서 dose 증가 시 Positive 예측 CD 감소와 Negative 예측 CD 증가를 확인했고, Blind Holdout 200/200행 예측도 유지했다.
- 인간 판단: Fishbone을 원인 확정표가 아닌 점검 순서 지도에 사용하고, 입력 오류 원자료 → Tool 상태 → tone별 Dose DOE → Focus DOE → 작업·환경 메타데이터 순으로 확인하기로 했다.
- AI 오류/수정: 최초 UI 테스트가 `st.info` 문구를 Markdown 목록에서만 찾아 실패했다. 요소 유형에 맞게 검증식을 수정했고 Matplotlib 한글 범례 경고는 영문 범례로 교체했다.
- 인간 수정: 현재 없음.

## 2026-08-21 — Photo 앱 네이비 테마와 가설 안내 강화

- AI 작업: `projects/01_photo/app.py`에 밝은 네이비 기반 포트폴리오 테마, 상단 문제·핵심 가설·대안 설명·판단 카드, 단계별 “왜 보는가” 안내를 추가했다.
- EDA 해석 강화: Dose, Focus, Tool, PR tone 탭마다 현재 업로드 데이터에서 계산한 표본 수·Pearson 상관·평균 CD를 사용해 그래프 읽는 법과 방향성을 표시했다. 탭 아래에는 Dose 방향, Tool/Focus 대안 설명, 입력 오류 민감도와 종합 판단을 한 화면에 정리했다.
- 설명 개선: CD 차이는 dose뿐 아니라 Tool/Lot 편중·입력 오류·Focus 비선형성 등으로 설명될 수 있음을 먼저 보여주고, EDA에서 H1/H2/대안/반증을 분리했다. Model 2 선택 이유와 예측 점수 안정성·관계 방향 안정성의 차이도 화면에 설명했다.
- 해석 제한: 모든 공정 설명을 가능성·가설·대안 설명으로 표현했으며 인과효과나 실제 recipe 일반 법칙으로 확정하지 않았다.
- 기존 로직 보존: Analysis Mode와 Blind Prediction Mode의 데이터 처리·모델·검증·예측 계산은 변경하지 않았다.
- 검증: A/train.csv 업로드 시 R² 0.679, RMSE 1.661 nm, MAE 1.140 nm가 동일했고 새 문제·가설·Model 2 안내가 렌더링됐다. A/holdout_features.csv는 Blind 안내와 200/200행 예측을 유지했으며 R²/RMSE/MAE를 표시하지 않았다.
- 인간 판단: 품질 표만 나열하지 않고 “무엇이 문제일 수 있는가 → 무엇이 가설인가 → 어떤 대안이 있는가 → 무엇을 검증해 판단하는가” 순서로 사용자를 안내하기로 결정했다.
- AI 오류/수정: 없음.
- 인간 수정: 현재 없음.

## 2026-08-21 — Photo Blind Holdout 예측 모드

- AI 작업: `projects/01_photo/app.py`에서 Target CD 유무로 Analysis Mode와 Blind Prediction Mode를 분기했다. Target이 없는 CSV는 데이터 품질을 점검한 뒤 기존 A/train 전체로 고정 Model 2를 학습하고 모든 업로드 행의 `predicted_resist_line_cd_nm`과 다운로드 CSV를 생성한다.
- 기존 로직 보존: `resist_line_cd_nm`이 있는 데이터는 기존 Data Audit, EDA, Model 2, 단일·반복·Lot Validation 경로를 그대로 사용한다. Holdout으로 모델 구조·변수·전처리 기준을 수정하지 않으며 정답이 없을 때 R², RMSE, MAE를 계산하거나 표시하지 않는다.
- 인간 판단: Blind Holdout의 중복·입력 오류 후보도 자동 삭제하지 않고 모든 원래 행에 예측을 생성하기로 결정했다. 미학습 PR tone 또는 Tool 범주는 잘못된 기준 범주로 예측하지 않고 중단하도록 했다.
- 검증: Streamlit AppTest로 A/train.csv 실제 업로드 시 기존 R² 0.679, RMSE 1.661 nm, MAE 1.140 nm가 동일함을 확인했다. A/holdout_features.csv 실제 업로드 시 Blind Mode 안내, 성능지표 미표시, 200/200행 유한 예측, 화면 표와 prediction CSV 다운로드 버튼을 확인했다.
- 보호 확인: STEP 2~5 `outputs/` 파일은 수정하지 않았고 API Key·비밀정보를 추가하지 않았다.
- AI 오류/수정: 없음.
- 인간 수정: 현재 없음.

## 최종 역할 구분

### AI가 지원한 일

- Python 분석 코드 작성과 재현 가능한 실행 절차 구성
- 스키마·결측·중복·편중·민감도에 대한 반복 계산
- EDA 및 검증 그래프 생성
- 기준 회귀모델과 Train/Validation 평가 실행
- 반복 분할, Lot Group Validation과 오류 후보 민감도 검증
- CSV 결과 정리, Streamlit 앱과 독립형 HTML 보고서 생성 지원

### 사람이 결정한 일

- Photo 공정 엔지니어의 문제와 다음 DOE 의사결정 정의
- Data Audit부터 EDA, Baseline, Validation 순으로 분석하기로 결정
- Positive/Negative PR을 분리해 해석하기로 판단
- 이상치를 원인 확인 전에 자동 삭제하지 않기로 결정
- Tool 편중과 Tool/Lot 조건을 대안 설명·교란 가능성으로 검토
- 단일 R²를 과신하지 않고 반복검증과 unseen-Lot 검증을 수행하기로 결정
- Random Forest를 바로 적용하지 않고 해석 가능한 기준모델을 유지하기로 결정
- 복잡한 모델 추가보다 입력 오류 후보와 데이터 품질 확인을 우선하기로 결정
- 최종 해석의 강도, 한계, Holdout 미평가 상태와 다음 DOE 우선순위 판단

AI가 계산과 초안 생성을 지원했지만, 분석 범위·신뢰할 결과·보류할 주장·최종 결론은 사람이 검토하고 결정한다.

## 2026-08-21 — 재사용 분석 절차 문서화

- AI 작업: 기존 Photo 분석과 보고서를 변경하지 않고 README의 저장소 구조·공통 Flow·재현법을 정리하고, 공정 공통 분석 절차 `SKILL.md`와 Photo 전용 주의사항 `projects/01_photo/SKILL_NOTES.md`를 작성했다.
- 역할 분리: AI의 코드·계산·그래프·회귀·검증·보고서 지원과 사람의 문제 정의·분석 순서·tone 분리·이상치 보존·교란 검토·반복검증·모델 복잡도·최종 해석 판단을 문서 상단에서 분리했다.
- 범위 제한: 공통 skill에는 Photo의 결과 수치나 dose–CD 방향을 넣지 않았다. 공정 전용 관찰은 `SKILL_NOTES.md`에만 두고 실제 recipe의 일반 법칙으로 확대하지 않도록 명시했다.
- 검증: 작업 전후 분석 CSV와 `report/index.html` SHA-256, 문서의 API Key 패턴과 개인 절대경로, 공통 skill의 Photo 전용 결과 포함 여부를 확인했다.
- 인간 수정: 현재 없음.

## 2026-08-21 — Photo CD 독립형 포트폴리오 보고서

- AI 작업: `projects/01_photo/PLAN.md`, `app.py`, STEP 2~5 분석 코드와 `outputs/data_audit`, `outputs/eda`, `outputs/modeling`, `outputs/validation`의 전체 파일을 대조해 독립형 HTML 보고서와 재현 가능한 빌드 스크립트를 작성했다.
- 시각화 재사용: 기존 검증 그래프 8개를 Base64 data URI로 내장해 `projects/01_photo/report/index.html` 하나만으로 오프라인 표시되도록 구성했다. 새로운 분석 결과나 Holdout 성능은 생성하지 않았다.
- AI가 지원한 일: 기존 CSV 수치 집계, 보고서 구조·문장 초안, 반응형 HTML/CSS 구현, 기존 그래프 내장, 자동 검증 코드를 작성했다.
- 인간 판단: Positive/Negative PR을 분리하고, 이상치를 자동 삭제하지 않으며, Tool 편중을 대안 설명으로 유지하고, 단일 R² 대신 반복·Lot 검증을 강조했다. Random Forest로 이동하지 않고 입력 오류 후보의 원자료 확인을 다음 우선순위로 정했다.
- 검증: 빌드 시 805×24, 중복 5행, 오류 후보 5행, Model 2 단일 분할 지표, 30회 반복 R², Lot-OOF R², tone별 slope 방향, 오류 후보 제외 민감도 수치를 원 CSV에 assertion으로 대조한다. HTML 11개 섹션, Base64 이미지 8개 디코딩, 외부 script/stylesheet 미사용, API 비밀키 패턴 미포함을 검사했다. 2회 재생성 SHA-256이 동일했고 Edge headless로 로컬 파일 실행 종료 코드 0을 확인했다.
- 해석 제한: 보고서의 회귀계수·상관·성능은 교육용 합성 관찰 데이터의 조건부 관계다. 인과효과나 실제 Photo recipe의 일반 법칙으로 표현하지 않았고, Holdout 최종 평가는 미수행으로 명시했다.
- AI 오류/수정: 최초 검증용 one-liner 두 번이 PowerShell 따옴표 파싱으로 실행 전 실패했다. 검증 로직을 빌드 스크립트 내부로 이동해 플랫폼 독립적으로 재실행했다.
- 인간 수정: 현재 없음.

## 2026-08-21 — Photo PR STEP 6 Streamlit 재현 앱

- AI 작업: STEP 2~5의 Data Quality, tone 분리 EDA, Model 2, 오류 후보 포함/제외 민감도, 30회 반복 검증과 Lot Group Validation을 CSV 업로드로 재실행하는 `projects/01_photo/app.py`를 만들었다.
- 로직 재사용: `baseline_regression.py`의 Train-only feature builder·오류 검토 규칙과 `model_validation.py`의 고정 분할·Model 2·반복/Lot 검증을 import했다. 앱 안에 회귀 전처리나 검증 계산을 다시 구현하지 않았다.
- 안전장치: 필수 컬럼 누락 시 분석을 중단하고 부족한 컬럼을 표시한다. 원본/업로드 CSV를 수정하지 않으며 완전 중복의 추가 복제만 메모리 분석본에서 제거한다. Holdout/B와 CD 이후 품질 결과를 입력으로 사용하지 않고 Random Forest도 실행하지 않는다.
- 검증: Streamlit AppTest로 기본 A/train 전체 화면, 민감도 선택, 30회 검증, Lot 검증 렌더링을 실행해 예외가 없음을 확인했다. 기본 데이터 오류 후보 5행, Model 2 seed 42 지표, STEP 5 반복 요약을 기존 CSV와 수치 비교했다.
- 기존 결과 보존: 공유 함수는 기본 인자를 기존 값으로 유지했고 STEP 4·5 스크립트를 재실행해 핵심 CSV 해시와 지표가 동일함을 확인했다.
- 해석 제한: 앱의 scatter 추세선과 Model 2 계수는 관찰적 관계이며 인과관계를 뜻하지 않는다. 입력 오류, Lot/CD 극단값, 업로드 데이터의 범주·표본 수에 따라 결과가 달라질 수 있다.
- 인간 수정: 현재 없음.

## 2026-08-21 — Photo PR STEP 5 모델 안정성 검증

- AI 작업: 기준 Model 2를 30개 고정 random_state의 tone×Tool 층화 70/30 분할에서 반복 검증하고, 40개 Lot을 8개 fold로 완전히 분리한 Group Cross Validation을 수행했다. 같은 반복 분할에서 Model 2와 coat thickness 최소 확장을 비교했다.
- 데이터 품질: STEP 4와 동일하게 완전 중복 추가 복제 5행을 분석 전에 제거했다. 감사에서 확인한 입력/단위 오류 의심 5행 포함/제외 조건을 30회 반복 비교했으며 원본 CSV는 수정하지 않았다.
- 잔차 검증: 각 행의 Lot이 학습에 포함되지 않은 out-of-fold 예측으로 PR tone, Tool, Lot, normalized-dose 5분위, focus 5분위별 residual을 집계했다. 평균 residual 절댓값 0.5 nm 이상 그룹을 검토 플래그로 기록하고 가장 큰 개별 잔차 20행도 저장했다.
- 누수 방지: `holdout_features.csv`와 B 데이터는 읽지 않았으며 Random Forest 등 추가 ML 모델은 실행하지 않았다. 각 반복/fold의 결측 대체값과 dose 중심은 Train에서만 계산했다.
- 검증: 805→800행 중복 제거, 반복 결과 60행(2모델×30 seed), Lot fold 간 lot_id 교집합 없음, Lot-OOF 예측 800개 유일성, dose slope 방향, 필수 CSV·그림 생성과 결정적 재실행을 확인했다.
- 해석 제한: 반복 분할과 Lot CV의 성능·계수는 관찰된 조건부 관계이며 인과효과가 아니다. 알려진 dose 입력 오류와 일부 CD 극단값이 R²/RMSE 및 Lot별 평균 잔차를 크게 움직일 수 있다.
- 인간 수정: 현재 없음.

## 2026-08-21 — Photo PR STEP 4 기준 회귀모델

- AI 작업: `projects/01_photo/data/A/train.csv`만 사용해 평균 baseline과 해석 가능한 선형회귀 Model 1~3을 동일한 고정 분할에서 비교했다. PR tone×Tool 비율을 보존하는 70/30 층화 분할, Train 중앙값 결측 대체, dose×tone 상호작용, Tool 보정, focus 제곱항과 공정변수 ablation을 구현했다.
- 데이터 변경: 원본 CSV는 수정하지 않았다. 완전 동일 중복 5개의 추가 복제 행만 분할 전에 제거하여 800행을 사용했고, 제거한 sample_id와 원본 행 번호를 기록했다. 입력/단위 오류 의심 5행은 주 분석에 포함하고 동일한 사전 분할에서 제외하는 민감도 분석을 추가했다.
- 누수 방지: `holdout_features.csv`와 B 데이터는 읽지 않았다. CD 이후 결과인 CDU, LER, scum/collapse/defect probability, spec_pass를 입력에서 명시적으로 금지하고 assertion으로 점검했다. Validation 값은 결측 대체값이나 중심값 계산에 사용하지 않았다.
- 검증: Python 구문 검사, 805→800행 중복 제거 assertion, Train 559/Validation 241행과 tone×Tool 비율, 결과 CSV/PNG 존재, 모델별 예측 행 수와 유한한 지표, 동일 seed 재실행 결과를 확인했다.
- AI 오류/수정: 최초 실행에서 설치된 scikit-learn 버전의 `DummyRegressor.constant_` 배열 차원 차이로 baseline 계수 저장이 중단됐다. 다차원 배열에서도 안전한 scalar 추출로 수정하고 전체 분석을 재실행했다.
- 해석 제한: 회귀계수와 성능 차이는 관찰 자료의 조건부 관계이며 인과효과가 아니다. 단일 70/30 분할, 합성 데이터, 입력 오류 의심값과 CD 극단값, 누락된 Lot/공정변수의 영향을 받을 수 있다.
- 인간 수정: 현재 없음.

## 2026-08-21 — Photo PR STEP 3 가설 설정 및 EDA

- AI 작업: 공정 지식에 기반한 사전 가설표를 먼저 코드에 고정하고, `projects/01_photo/data/A/train.csv` 805행만 사용해 PR tone별 CD 분포, 7개 공정변수 scatter/비인과적 2차 추세선, Pearson 상관, Tool별 CD 분포와 Tool 내부 상관을 생성했다.
- 데이터 분리: `holdout_features.csv`와 B 데이터는 읽지 않았고 회귀·Random Forest 등 머신러닝 모델을 실행하지 않았다. `pr_tone` 결측 11행은 `MISSING`으로 요약 분포에만 포함하고 Positive/Negative 관계 분석에서는 제외했다.
- 오류 의심값 처리: 감사 결과 중 축을 크게 왜곡하는 소수점·입력 오류 의심 5개를 원본 포함 결과에 보존했다. 해당 변수에 한해서만 별도 sensitivity 그래프·상관에서 제외했으며 sample_id, 값, 이유를 `excluded_or_flagged_rows.csv`에 기록했다. IQR 이상치와 CD 이상치는 자동 제거하지 않았다.
- 검증: 스크립트 구문·재실행, 입력 805행 assertion, tone별 행 수(523/271/11), 결과 CSV 및 PNG 생성, 원본/민감도 상관쌍 수, 주요 그래프를 원자료와 대조했다.
- AI 오류/수정: 최초 실행 환경에 pandas/matplotlib/numpy가 없어 실행이 중단되었다. 사용자 승인 후 패키지를 설치하고, 쓰기 제한 환경에서도 Matplotlib 캐시가 프로젝트 내부에 생성되도록 수정했다.
- 해석 제한: 추세선·Pearson 상관은 시각적/기술적 관계이며 원인을 뜻하지 않는다. Tool/Lot, 측정 이상치, 누락 변수와 공정조건 간 연동이 대안 설명일 수 있다.
- 인간 수정: 현재 없음.

## 2026-08-21 — Photo PR STEP 2 데이터 감사

- AI 작업: `datasets/student/01_photo/A/train.csv`을 읽기 전용으로 감사하는 `projects/01_photo/scripts/data_audit.py`를 작성하고 요약 CSV 5개와 SVG 품질 그래프 2개를 생성했다.
- 검증: 원본 행·열 수를 스키마 기대값과 비교하고, 스크립트 재실행, Python 구문 검사, 결과 파일 구조와 주요 집계를 원자료에서 재확인했다.
- AI 오류/수정: 최초 출력에서 결측 `pr_tone`의 그룹명이 빈 문자열로 표시됐다. 원본 값은 바꾸지 않고 결과 표시만 `MISSING`으로 수정했다.
- 해석 제한: 이상치 플래그는 삭제 근거가 아닌 검토 후보이다. tone별 IQR과 넓은 물리 검토 범위를 사용했으며 상관분석·회귀·머신러닝은 수행하지 않았다.
- 인간 수정: 현재 없음.

## 2026-08-21 — 공정별 프로젝트 구조 정리

- AI 작업: 10개 공정의 작업 공간을 `projects/` 아래에 만들고 각 폴더에 `PLAN.md`, `scripts/`, `outputs/`를 구성했다.
- 보존 이동: Photo PLAN, 감사 스크립트, 기존 감사 결과를 `projects/01_photo/` 아래로 이동했다.
- 미진행 공정: 02~10 공정의 PLAN은 `templates/PLAN.md`를 수정 없이 복사했으며 분석 결과는 생성하지 않았다.
- 검증: `datasets/student/` 아래 CSV 40개의 SHA-256이 작업 전후 동일한지 확인하고, Photo 감사 스크립트를 새 위치에서 재실행했다.

## 2026-08-21 — 실습용 데이터 복사본 구성

- AI 작업: 10개 공정의 `projects/[공정명]/data/A`, `data/B`를 만들고 각 원본의 `train.csv`, `holdout_features.csv`를 분리된 상태로 복사했다.
- 원본 보호: `datasets/student/` 파일은 이동·수정하지 않았으며, 복사 전후 원본과 복사본 40쌍의 SHA-256 일치를 검증했다.
- 범위 제한: A/B 또는 train/holdout을 병합하지 않았고, 분석·결과 생성·PLAN 내용 변경을 수행하지 않았다.
## 2026-08-21 — Photo Process Analysis Workbench 확장

- AI 작업: 기존 Streamlit 결과 대시보드를 CSV/XLSX 입력, Data Audit, 누수 방지 Variable Lab, 선택 변수 기반 자동 EDA, Linear Regression Custom Model, 고정 Model 2 비교, 회귀계수 해석, What-if 및 한 변수 sweep을 제공하는 7단계 워크벤치로 확장했다.
- 로직 재사용: 기존 `TrainOnlyFeatureBuilder`, 고정 seed 분할, 반복 검증, Lot 검증, 입력 오류 후보 규칙을 재사용했다. Custom Model 전처리는 Train에서만 학습하며 CD 이후 품질 결과를 선택 목록에서 제외했다.
- 안전장치: 상관·회귀·What-if 결과를 인과효과로 표현하지 않고, 학습 범위 밖 숫자 입력과 미학습 범주를 경고 또는 차단한다. Blind Holdout은 기존 A/train의 고정 Model 2로만 예측하며 성능지표와 모델 재선택을 제공하지 않는다.
- 검증: 기본 A/train의 Model 2가 R² 0.679, RMSE 1.661 nm, MAE 1.140 nm를 유지하는지 확인했다. 기본 변수 및 Thickness 추가 Custom Model, 선택 변수별 EDA 탭, dose 변경 예측, tone별 반대 dose 방향, 범위 밖 경고, 200행 Holdout 예측, XLSX 입력과 CSV 동일 지표를 테스트했다.
- 인간 판단: Target은 이번 버전에서 CD로 제한하고, 허용 공정변수와 leakage 차단 목록, Model 2 기준 비교, Random Forest 미사용, Holdout 비튜닝 원칙, 최종 해석과 한계를 유지했다.
- 기존 결과 보존: STEP 2~5 output CSV, 원본 데이터, `report/index.html`은 수정하지 않았다.
