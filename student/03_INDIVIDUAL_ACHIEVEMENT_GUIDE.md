# 개인 성과 집중 가이드 — 설치에서 7일 주제 탐구까지

## 1. 이 프로젝트를 왜 하는가

역사학 석사생이 연구질문을 정하고, 사료카드를 만들고, 주장을 반증하며 논문을 완성하듯이 수강생도 일주일 동안 자신의 문제를 깊게 탐구합니다. 목표는 AI 도구를 많이 사용했다는 기록이 아니라 다음 증거를 남기는 것입니다.

1. 내가 선택한 직무 문제
2. 데이터를 믿을 수 있는지 확인한 기록
3. 전공 원리와 근거자료
4. 주가설과 대안가설
5. 기준모델과 개선모델의 공정한 비교
6. 실패 사례와 인간의 수정
7. 사용자의 결정을 돕는 작동형 페이지
8. 재현 가능한 GitHub 이력과 3분 발표

## 2. 역사 연구와 엔지니어링 탐구의 대응

| 역사학 연구 | 반도체 AI 프로젝트 | 남길 증거 |
|---|---|---|
| 연구질문 | 사용자와 의사결정 | `PLAN.md` 문제 한 문장 |
| 사료카드 | 데이터카드 | 출처·스키마·단위·생성시점 |
| 사료비판 | 데이터 감사 | 결측·중복·이상치·편중·누수 |
| 선행연구 | 전공 원리와 Governing equation 후보 | 교재·논문·공식문서 링크 |
| 주장감사 | 주가설·대안가설·반증조건 | 가설표와 필요한 그래프 |
| 본문 논증 | 기준모델·개선모델·오차 분석 | Holdout 지표와 실패 사례 |
| 논문 결론 | 사용자 결정·한계·추가실험 | Live Page와 3분 발표 |

## 3. 1강에서 설치부터 첫 증거까지

### STEP 0 — 계정 준비

- 개인 GitHub 계정을 만들고 이메일 인증을 완료합니다.
- ChatGPT 계정으로 Codex를 사용할 수 있는지 확인합니다.
- 실제 회사 데이터·공정 Spec·장비 Log·개인정보를 공개 저장소에 올리지 않기로 확인합니다.

### STEP 1 — 네 도구 설치

#### Windows 11

1. [VS Code](https://code.visualstudio.com/download)의 User Installer를 설치합니다.
2. [Git for Windows](https://git-scm.com/install/windows)를 기본 옵션으로 설치합니다.
3. [Python](https://www.python.org/downloads/windows/) 설치 첫 화면에서 `Add python.exe to PATH`를 선택합니다.
4. PowerShell에서 Codex 공식 설치 명령을 실행합니다.

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://chatgpt.com/codex/install.ps1 | iex"
```

5. PowerShell을 닫고 새로 엽니다.

#### macOS

1. [VS Code](https://code.visualstudio.com/download)를 Applications로 이동합니다.
2. [Git](https://git-scm.com/download/mac)과 [Python](https://www.python.org/downloads/macos/)을 설치합니다.
3. VS Code에서 Command Palette를 열고 `Shell Command: Install 'code' command in PATH`를 실행합니다.
4. Terminal에서 Codex 공식 설치 명령을 실행합니다.

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

5. Terminal을 닫고 새로 엽니다.

각 도구의 역할:

- VS Code: 파일과 Terminal을 한 화면에서 관리
- Git: 변경 이력과 사람의 판단을 기록
- Python: 데이터 감사·그래프·모델 실행
- Codex: 저장소를 읽고 계획·코드·테스트를 보조

### STEP 2 — 버전 확인

Windows PowerShell:

```powershell
git --version
py --version
code --version
codex --version
```

macOS Terminal:

```bash
git --version
python3 --version
code --version
codex --version
```

성공 기준은 네 명령이 모두 버전을 표시하고 Python이 3.11 이상인 것입니다.

### STEP 3 — Codex 로그인과 진단

```bash
codex login
codex login status
codex doctor
```

브라우저에서 자신의 계정으로 로그인합니다. API Key·비밀번호·인증 화면을 Telegram이나 저장소에 올리지 않습니다.

### STEP 4 — 개인 저장소 생성과 Clone

Starter Repository에서 `Use this template`을 눌러 공개 저장소 `semiconductor-ai-project`를 만듭니다.

```bash
cd ~/Documents
git clone YOUR_REPOSITORY_HTTPS_URL semiconductor-ai-project
cd semiconductor-ai-project
code .
```

Windows PowerShell에서 문서 폴더 이동이 실패하면 다음을 사용합니다.

```powershell
cd $HOME\Documents
```

### STEP 5 — 자동점검

Windows:

```powershell
py tools/student_preflight.py
```

macOS:

```bash
python3 tools/student_preflight.py
```

마지막 줄의 `READY: core environment checks passed`를 첫 통과 증거로 남깁니다.

### STEP 6 — 저장소를 수정하지 않고 설명하게 하기

```text
AGENTS.md, README.md, PLAN.md를 먼저 읽어라.
아직 파일을 수정하지 마라.
입력 데이터, 데이터 감사, 기준모델, 개선모델, 웹페이지,
테스트, 배포 흐름을 실제 파일명을 근거로 설명하라.
확인되지 않은 반도체 사실은 추가하지 마라.
```

사람은 없는 파일·명령을 만들지 않았는지, 원본 데이터를 수정하라고 하지 않았는지 확인합니다.

## 4. 자신의 주제를 탐구하는 10단계

### 1단계 — 직무와 사용자 한 명

공정·설비·소자·양산기술 중 하나를 고르고 실제 결정을 내릴 사용자 역할을 한 명만 씁니다.

### 2단계 — 반복되는 관측과 결정

사용자가 매일 보는 숫자와 그 뒤에 내리는 행동을 적습니다. `수율 예측`이 아니라 `어떤 Tool을 먼저 점검할지 선택`처럼 씁니다.

### 3단계 — 데이터카드

다음을 `PLAN.md`에 기록합니다.

```text
한 행의 단위:
생성·관측 시점:
입력 신호와 단위:
품질 결과와 측정 시점:
결측·이상치 발생 가능성:
Tool·Lot·기간 편중:
미래정보 누수 위험:
```

### 4단계 — 전공 근거카드

관련 전공과목, 핵심 현상, Governing equation 또는 도메인 제약 후보를 적습니다. AI가 제안한 수식은 후보일 뿐이며 교재·논문·공식 문서에서 적용 조건과 변수 정의를 확인합니다.

```text
근거자료:
자료가 직접 말하는 것:
프로젝트에 적용 가능한 범위:
자료가 말하지 않는 것:
확인한 사람과 날짜:
```

### 5단계 — 주장감사

| 구분 | 작성 내용 |
|---|---|
| 관찰 사실 | 그래프와 숫자로 직접 확인한 것 |
| 주가설 | 가장 먼저 검증할 설명 |
| 대안가설 | Sensor, Recipe, Tool, 시간 등 다른 설명 |
| 반증조건 | 어떤 결과가 나오면 가설을 버릴 것인가 |
| 추가자료 | 판단을 위해 더 필요한 측정 |

### 6단계 — 데이터 감사

스키마 → 단위 → 결측 → 중복 → 이상치 → Tool·Lot·시간 편중 → 누수 순서로 확인합니다. 처리 전후의 결과를 함께 남기며 원본은 수정하지 않습니다.

### 7단계 — 기준모델

- 회귀: 평균 또는 단순 선형회귀
- 분류: 다수 클래스 또는 단순 임계값
- 시계열: 이전 Run 또는 이동평균
- 최적화: 현재 Recipe 또는 단일 KPI 최대화

복잡한 AI가 기준모델보다 Holdout에서 실제로 나은지 확인합니다.

### 8단계 — 개선모델과 실패 사례

성능 숫자 하나만 보고 끝내지 않습니다. Tool·Lot·기간별 성능과 중요한 오차 사례 세 개를 확인하고, AI의 설명이 원자료와 맞는지 검증합니다.

### 9단계 — 작동형 MVP

필수 화면은 다음 여섯 개입니다.

1. 데이터 선택 또는 CSV 입력
2. 데이터 품질 진단
3. 기준모델과 개선모델 비교
4. 입력 두 개 이상의 What-if 조작
5. 위험도·추천·추가실험
6. 한계와 인간 검증 기록

### 10단계 — GitHub 증거와 발표

모든 주요 단계에서 작은 Commit을 남깁니다. 최종 발표는 문제 30초, 데이터·가설 30초, 데모 50초, 성능 30초, 인간 검증 20초, 효과·한계 20초로 구성합니다.

## 5. 대표 탐구 — Plasma FDC

### 문제 정의

> 설비 엔지니어가 RF matcher·Vpp·Vdc 등 Run Log를 보고 상태 변화를 조기에 찾고, 박막 품질과 함께 검토하여 계속 진행·점검·재측정을 선택할 수 있게 한다.

### 데이터카드

- 한 행: 하나의 Run 또는 고정 시간창
- 입력: 정규화한 matcher state, Vpp, Vdc, reflected-power index, pressure, gas-flow index
- 결과: 교육용 두께·균일도·결함 Quality index
- 시간 규칙: 알람 시점보다 나중에 측정된 Quality는 예측 입력에 사용하지 않음
- 편중 후보: Recipe, Chamber, 센서 교체 전후, Run sequence

### 세 개의 검증 질문

1. RF 신호 조합의 변화점이 단순 관리한계보다 먼저 이상을 찾는가?
2. 신호와 Quality의 관계가 Recipe·Chamber별로도 유지되는가?
3. Sensor drift와 실제 공정 변화라는 대안 설명을 구분할 수 있는가?

### 기준과 개선

- 기준: 이동평균과 관리한계
- 개선 후보: 변화점 탐지 또는 다변량 이상점수
- 성능 KPI: Recall과 검출 지연
- 위험 KPI: False alarm과 정상 Run Hold 비율
- 오차 분석: 놓친 이상 3건과 불필요한 알람 3건

### 최종 MVP 화면

1. Run 시계열과 변화점
2. Matcher·Vpp·Vdc와 Quality 동시 보기
3. Recipe·Chamber 필터
4. 기준모델과 개선모델 비교
5. 계속 진행·점검·재측정 제안과 근거
6. 대안 설명과 추가 측정 항목

## 6. 설치 실패 시 수업을 멈추지 않는 법

- `code`만 실패: VS Code를 직접 실행합니다.
- Windows가 Python 대신 Store를 열면 `py`를 사용합니다.
- Codex가 보이지 않으면 Terminal을 닫고 새로 엽니다.
- 관리자 권한이 없으면 GitHub 웹 편집과 제공된 결과물로 수업을 계속합니다.
- WSL을 처음 설치하는 작업은 수업 중 하지 않습니다.
- 10분 이상 막히면 `🟡 번호/단계/오류 한 줄`만 Telegram에 보내고 다음 분석 단계로 이동합니다.

## 7. 최종 완료 기준

- [ ] 문제와 사용자의 결정이 한 문장이다.
- [ ] 데이터카드와 전공 근거카드가 있다.
- [ ] 주가설·대안가설·반증조건이 있다.
- [ ] 기준모델과 Holdout 비교가 있다.
- [ ] 오차 사례와 AI의 인간 검증 기록이 있다.
- [ ] 입력 두 개 이상이 움직이는 Live Page가 있다.
- [ ] 실제 회사자료 없이 재현할 수 있다.
- [ ] GitHub Commit이 탐구 과정을 보여준다.
- [ ] 3분 안에 문제·증거·한계를 설명할 수 있다.
