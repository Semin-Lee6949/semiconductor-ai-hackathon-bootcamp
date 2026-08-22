# Semiconductor AI Hackathon Bootcamp

반도체 공정 문제를 **데이터 감사 → 기준모델 → What-if 시뮬레이션 → 의사결정 → GitHub Pages → 3분 발표**로 연결하는 단기 특강 준비 저장소입니다.

도구 흐름은 **Claude·GPT·Gemini 중 하나로 계획·분석 → 같은 로컬 테스트와 Holdout 검증 → GitHub Push → GitHub Pages 포트폴리오**입니다.

> 교육용 합성 데이터만 사용합니다. 특정 회사의 공식 교육과정·실제 공정 조건·기술 노드·내부 Spec을 나타내지 않습니다.

## 저장소 목적

이 저장소는 교육용 반도체 공정 데이터로 문제 정의부터 데이터 감사, 가설 검토, 기준모델, 검증, 작동형 앱, 포트폴리오 보고서까지 재현하는 실습 공간입니다. 목표는 가장 복잡한 모델을 만드는 것이 아니라, 공정 엔지니어의 의사결정을 지원할 수 있는 근거와 한계를 코드·결과·기록으로 남기는 것입니다.

## 분석 작업 공간

| 경로 | 역할 |
|---|---|
| `projects/` | 공정별 독립 작업 공간. 각 프로젝트의 `PLAN.md`, 실행 코드, 결과, 앱, 보고서를 함께 관리합니다. |
| `datasets/` | 배포용 교육 데이터와 원본 역할의 데이터 묶음입니다. 원본은 직접 수정하지 않습니다. |
| `projects/<공정>/data/` | 프로젝트가 참조하는 분석 입력 복사본입니다. A/B와 train/holdout 분리를 유지합니다. |
| `projects/<공정>/scripts/` | 데이터 감사, EDA, 모델링, 검증, 보고서 생성 등 재현 가능한 실행 코드를 저장합니다. |
| `projects/<공정>/outputs/` | 단계별 CSV와 그래프를 저장합니다. 예: `data_audit/`, `eda/`, `modeling/`, `validation/`. |
| `templates/` | 새로운 공정 프로젝트에서 재사용할 계획·프롬프트·기록 양식입니다. |

## 공통 분석 Flow

```text
Problem
  → Data Audit
  → Hypothesis / EDA
  → Baseline
  → Validation
  → Streamlit
  → Report
```

1. **Problem:** 실제 사용자, 결정, KPI, 보안 경계와 아직 모르는 것을 `PLAN.md`에 기록합니다.
2. **Data Audit:** 모델링 전에 schema, 단위, 결측, 중복, 이상치 후보, Lot/Tool 편중과 leakage 가능성을 확인합니다.
3. **Hypothesis / EDA:** 전공지식 기반 주가설·대안가설·교란요인을 먼저 적고, 공정적으로 다른 그룹을 분리해 관찰합니다.
4. **Baseline:** 평균 예측과 해석 가능한 단순 모델부터 비교합니다. Train에서 학습한 전처리만 Validation에 적용합니다.
5. **Validation:** 단일 분할을 과신하지 않고 반복 분할과 Lot/Tool/시간 구조에 맞는 검증, 데이터 품질 민감도 분석을 수행합니다.
6. **Streamlit:** 입력 변화에 따라 결과·위험도·추천이 갱신되는 재현 앱으로 분석 로직을 확인합니다.
7. **Report:** 결과뿐 아니라 실패한 가설, 의심한 결과, 인간의 판단, 한계와 다음 실험을 함께 기록합니다.

공통 실행 원칙은 [`SKILL.md`](SKILL.md), 프로젝트 계획 양식은 [`templates/PLAN.md`](templates/PLAN.md)를 참고합니다.

## 01_photo 사례

Photo 공정 엔지니어가 다음 DOE에서 우선 확인할 PR tone과 Dose·Focus·PEB·현상조건 조합을 좁힐 수 있도록, `resist_line_cd_nm`을 중심으로 관찰적 관계와 모델 안정성을 분석했습니다.

핵심 결과는 다음과 같습니다.

- Positive PR과 Negative PR에서 normalized dose–CD 방향이 다르게 관찰되어 두 그룹을 분리했습니다.
- 이 방향은 30회 반복 분할에서도 각 tone에서 모두 유지됐지만, 예측 R²는 분할에 따라 흔들렸습니다.
- Tool별 CD 수준 차이가 관찰되어 Tool 구성과 condition/calibration 가능성을 대안 설명으로 유지했습니다.
- 단순한 Model 2가 좋은 기준이었고, 전체 변수 확장은 단일 Validation 성능을 개선하지 못했습니다.
- 입력·단위 오류 의심 5행의 포함 여부가 반복 Validation 성능과 변동성에 큰 영향을 주었습니다.
- 따라서 복잡한 모델을 즉시 추가하기보다 원자료 품질을 먼저 확인하기로 판단했습니다.

이 결과는 교육용 합성 데이터의 특정 공정창에서 관찰된 연관성입니다. 인과관계나 실제 Photo recipe의 일반 법칙을 의미하지 않으며, 최종 Holdout 평가는 아직 수행하지 않았습니다. Photo 전용 해석 주의사항은 [`projects/01_photo/SKILL_NOTES.md`](projects/01_photo/SKILL_NOTES.md)에 분리했습니다.

### Photo 실행 및 재현

필요 패키지를 설치하고 Streamlit 앱을 실행합니다.

```bash
python -m pip install -r requirements-class.txt
streamlit run projects/01_photo/app.py
```

CSV를 업로드하지 않으면 `projects/01_photo/data/A/train.csv`를 사용합니다. 앱은 `projects/01_photo/artifacts/`의 고정 A/train Model 2 Pipeline으로 신규 Lot을 평가하거나 예측하며, 업로드만으로 Reference Model을 재학습하지 않습니다. Target 없는 파일은 예측만 하고 Random Forest는 사용하지 않습니다.

Reference artifact를 명시적으로 재생성할 때만 다음을 실행합니다.

```bash
python projects/01_photo/scripts/train_reference_model.py
```

단계별 산출물을 다시 생성하려면 저장소 루트에서 다음 순서로 실행합니다.

```bash
python projects/01_photo/scripts/data_audit.py
python projects/01_photo/scripts/eda.py
python projects/01_photo/scripts/baseline_regression.py
python projects/01_photo/scripts/model_validation.py
python projects/01_photo/scripts/build_report.py
```

각 스크립트는 결과를 `projects/01_photo/outputs/<단계>/`에 저장합니다. 마지막 명령은 기존 CSV와 그래프를 읽어 오프라인 단일 파일 보고서 [`projects/01_photo/report/index.html`](projects/01_photo/report/index.html)을 생성합니다. Holdout 최종 평가는 분석·모델 선택을 고정한 뒤 별도 단계에서 수행해야 합니다.

## 보안 및 재현 주의사항

- 실제 회사 데이터, 장비 로그, 내부 Spec, 고객정보와 개인정보를 저장소나 외부 AI 서비스에 전송하지 않습니다.
- API Key, 토큰, `.env`와 계정정보를 코드·문서·Prompt·Screenshot·Commit에 포함하지 않습니다.
- 개인 PC의 절대경로를 문서나 코드에 고정하지 않고 저장소 기준 상대경로를 사용합니다.
- `datasets/` 원본과 프로젝트 입력 CSV를 직접 수정하지 않습니다. 제외·보정은 코드와 로그로 남깁니다.
- Holdout은 모델·가설 선택에 사용하지 않고 최종 평가 전까지 봉인합니다.
- AI가 만든 코드·수치·해석은 테스트와 원자료로 사람이 검증하며, 상관관계를 인과관계로 표현하지 않습니다.

## 운영 구조

- 1차: 2026-08-14, 오프라인 2시간
- 자율 프로젝트: 2026-08-20 이후, 같은 8단계를 개인 데이터로 반복
- 대상: 반도체 소자·R&D 공정·양산기술·설비기술 지원자 10명
- 결과물: 개인 저장소, 작동형 MVP, Live Page, AI 활용기록, 3분 발표

## 첫날 성공 기준

수업이 끝날 때 모든 수강생이 다음 다섯 가지를 이해하고, 최소 한 단계는 직접 수행해야 합니다.

1. 사용자·데이터·결정을 포함한 문제정의
2. 선택한 AI를 이용한 근거 조사와 근거카드
3. Claude·GPT·Gemini 공통 프롬프트로 저장소를 읽고 계획하는 과정
4. AI 결과를 데이터·전공 원리·반례로 검증하는 방법
5. Git diff·Commit·Pages로 과정의 증거를 남기는 방법

개인 Fork·Commit·Pages는 사전 준비 상태에 따라 수업 중 또는 수업 후 완성합니다.

## 저장소 안내

- [`index.html`](index.html): 1차 강의용 반응형 GitHub Pages 자료
- [`preclass_setup.html`](preclass_setup.html): 계정·프로그램·패키지·토큰을 한 번에 확인하는 Windows 사전 준비 페이지
- [`COURSE_PLAN.md`](COURSE_PLAN.md): 과정 범위·일정·완료 기준
- [`STATUS.md`](STATUS.md): 현재 준비상태와 남은 우선순위
- [`instructor/`](instructor/): 1·2차 진행표, 사전점검
- [`student/00_PROBLEM_DISCOVERY_QUESTIONNAIRE.md`](student/00_PROBLEM_DISCOVERY_QUESTIONNAIRE.md): 문제→전공→Governing equation·도메인 제약→상관·대안가설→의사결정으로 좁히는 1강 질문지
- [`student/00_PRECLASS_SETUP_2026-08-14.md`](student/00_PRECLASS_SETUP_2026-08-14.md): 수강생에게 전달할 간단한 설치 체크리스트
- [`templates/UNIVERSAL_AI_PROJECT_PROMPT.md`](templates/UNIVERSAL_AI_PROJECT_PROMPT.md): Claude·GPT·Gemini 공통 프로젝트 프롬프트
- [`templates/COMPACT_AI_PROMPTS.md`](templates/COMPACT_AI_PROMPTS.md): 수업 중 계획·구현·검수 3회용 압축 프롬프트
- [`student/AI_QUOTA_SAFETY_PLAN.md`](student/AI_QUOTA_SAFETY_PLAN.md): Claude·GPT 한도 보호와 Gemini·로컬 대체 경로
- [`student/01_FIRST_CLASS_HANDS_ON_MANUAL.md`](student/01_FIRST_CLASS_HANDS_ON_MANUAL.md): 설치부터 첫 Pages 배포까지 수강생 실습서
- [`instructor/01_TELEGRAM_DELIVERY_SCRIPT.md`](instructor/01_TELEGRAM_DELIVERY_SCRIPT.md): 20명 동시 진행용 Telegram 메시지 대본
- [`instructor/SESSION1_SMOOTH_FLOW.md`](instructor/SESSION1_SMOOTH_FLOW.md): 통계·시각화·AI·배포가 이어지는 120분 강사 진행표
- [`instructor/SESSION1_AGENT_WORKFLOW_10_BEGINNERS.md`](instructor/SESSION1_AGENT_WORKFLOW_10_BEGINNERS.md): GitHub 미가입자가 포함된 10명 초급반용 Agent 시연·페어 실습·시간 부족 대응안
- [`templates/PLAN.md`](templates/PLAN.md): 현재 문제의 목표·전공지식·가설·실행·검증 기준 작성 틀
- [`templates/SKILL.md`](templates/SKILL.md): 여러 프로젝트에서 검증된 문제해결 절차를 재사용하기 위한 작성 틀
- [`student/02_TOPIC_AND_PROJECT_GUIDE.md`](student/02_TOPIC_AND_PROJECT_GUIDE.md): 주제선정·범위축소·7일 프로젝트 가이드
- [`student/03_INDIVIDUAL_ACHIEVEMENT_GUIDE.md`](student/03_INDIVIDUAL_ACHIEVEMENT_GUIDE.md): 설치→데이터카드→근거카드→주장감사→MVP→발표의 개인 성과 집중 가이드
- [`lessons/01_DATA_QUALITY_AND_VISUALIZATION.md`](lessons/01_DATA_QUALITY_AND_VISUALIZATION.md): 결측·이상치·편중 처리와 ggplot2·seaborn 그래프 선택 실습
- [`challenges/`](challenges/): 반도체 AI 문제 10종 카탈로그
- [`datasets/`](datasets/): 노이즈·결측·이상치·교란이 포함된 A/B 합성 데이터 20팩
- [`templates/`](templates/): 계획·AI 기록·발표·평가 양식
- [`demo/`](demo/): CMP 합성 데이터 기반 작동형 시연 예제

## 데모 실행

```bash
cd demo
python -m pip install -r requirements.txt
python src/build_demo.py
python -m http.server 8000 --directory docs
```

브라우저에서 <http://localhost:8000>을 열고 Down Force, 속도, Slurry, Pad Age, Pattern Density를 바꿔 결과가 갱신되는지 확인합니다.

## 전체 데이터 재생성·검증

```bash
python tools/generate_datasets.py
python -m unittest discover -s tests -v
```

수강생 환경점검:

```bash
python tools/student_preflight.py
```
