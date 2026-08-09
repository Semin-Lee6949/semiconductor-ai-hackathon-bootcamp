# 1강 실무 매뉴얼 — 설치부터 첫 배포까지

대상: 반도체 공정·소자·양산·설비 직무 지원자 20명

방식: 강사가 텔레그램에 한 단계씩 안내하면 전원이 같은 단계까지 완료한 뒤 이동

시간: 120분

> 오늘의 목표는 도구 설명을 듣는 것이 아닙니다. 내 PC에서 저장소를 내려받고, 데이터를 검사하고, Codex와 함께 최소 변경을 수행하고, 테스트한 뒤 GitHub에 기록하는 것입니다.

1강 이후 자신의 주제를 일주일 동안 집중 탐구하는 전체 절차는 [`03_INDIVIDUAL_ACHIEVEMENT_GUIDE.md`](03_INDIVIDUAL_ACHIEVEMENT_GUIDE.md)를 따릅니다. 역사학 연구의 연구질문·사료카드·주장감사처럼, 데이터카드·전공 근거카드·가설 반증·GitHub 증거를 단계별로 남깁니다.

## 0. 수업을 시작하기 전에 준비할 것

- 노트북과 충전기
- Chrome 또는 Edge
- GitHub 계정과 이메일 인증
- ChatGPT 계정 또는 별도로 안내받은 Codex 접근 방법
- 휴대전화 Telegram
- 회사 내부자료가 아닌 교육용 합성 데이터만 사용한다는 동의
- [`00_PROBLEM_DISCOVERY_QUESTIONNAIRE.md`](00_PROBLEM_DISCOVERY_QUESTIONNAIRE.md) 10분 1차 작성

강사가 Telegram에 보낸 다음 세 가지를 메모합니다.

- `STARTER_REPO_URL`: 개인 저장소를 만들 템플릿 주소
- `DATASET_ID`: 예: `05-CMP-A`
- `SUBMISSION_FORM_URL`: 저장소·Pages 주소 제출처

## 1. 20명 동시 실습 규칙

각 단계가 끝나면 Telegram에 다음 중 하나만 보냅니다.

- `✅ 07 완료` — 다음 단계 진행 가능
- `🟡 07 도움` — 옆 사람과 계속 진행하고 보조강사 호출
- `🔴 07 중단` — 로그인·권한·설치 문제로 진행 불가

메시지 앞에는 항상 본인 번호를 붙입니다. 예: `12번 ✅ Git 설치 완료`.

전체 수업은 한 사람의 오류 때문에 멈추지 않습니다.

- 15명 이상 완료: 다음 단계로 이동
- 미완료자는 4개 조의 실습 파트너 또는 보조강사와 복구
- 10분 이상 걸리는 설치 문제: 브라우저·ZIP 우회 경로로 수업을 계속하고 쉬는 시간에 복구

## 2. 120분 완주 지도

| 시간 | 직접 하는 일 | 통과 증거 |
|---|---|---|
| 0~8분 | 문제발견 질문 공유·결과물·보안 확인 | 문제 한 문장과 Telegram 번호 응답 |
| 8~18분 | 결측·이상치가 판단을 바꾸는 사례 | 처리 전 질문 2개 |
| 18~38분 | Git·Python·VS Code·Antigravity·Claude Code/Codex 선택 설치 | 앱 로그인과 선택 Agent 버전 |
| 38~52분 | 로그인·Git 설정·Clone·자동점검 | `READY` 출력 |
| 52~67분 | noisy CSV 통계 감사 | 결측·중복·이상치 숫자 |
| 67~80분 | ggplot2·seaborn 갤러리 | 질문별 그래프 선택 |
| 80~95분 | seaborn 감사 그래프 생성·해석 | PNG와 답변 6개 |
| 95~106분 | 선택한 Coding Agent로 최소 변경·테스트·Commit | GitHub Commit |
| 106~116분 | 로컬 웹앱·GitHub Pages | 공개 URL |
| 116~120분 | 문제정의 재작성·프로젝트 가이드 | 후보 2개와 대안 설명 기록 |

## 3. STEP 1 — 필수 사이트 로그인

브라우저에서 다음 사이트를 각각 새 탭으로 엽니다.

1. [GitHub](https://github.com/login)
2. [ChatGPT](https://chatgpt.com/)
3. 강사가 Telegram에 공유한 Starter Repository

### 성공 기준

- GitHub 오른쪽 위에 내 프로필 아이콘이 보인다.
- ChatGPT에서 내 계정 또는 교육용 Workspace가 확인된다.
- Starter Repository의 `README.md`가 보인다.

### 실패하면

- GitHub 이메일 인증이 안 된 경우 받은편지함에서 인증을 먼저 완료합니다.
- 회사·학교 SSO 계정은 개인 공개 저장소 생성이 제한될 수 있으므로 개인 GitHub 계정을 사용합니다.
- 비밀번호, API Key, 인증 화면을 Telegram에 올리지 않습니다.

## 4. STEP 2 — 조사 도구와 제작 도구 설치

역할을 섞지 않습니다.

- **Antigravity:** 웹·논문·공식문서 조사와 근거카드 작성
- **Claude Code 또는 Codex 중 하나:** 저장소 이해, 데이터 분석, 보고서·웹페이지 제작
- **GitHub·Pages:** 과정 기록, Push, 최종 포트폴리오 공개

### Windows 11 권장 경로

각 공식 사이트에서 설치합니다.

1. [VS Code](https://code.visualstudio.com/download)
2. [Git for Windows](https://git-scm.com/install/windows)
3. [Python](https://www.python.org/downloads/windows/)
4. [Google Antigravity](https://antigravity.google/)를 설치하고 Google 계정으로 로그인
5. 다음 중 사용할 Coding Agent 하나를 선택
   - [Claude Code](https://code.claude.com/docs/en/setup)
   - [Codex CLI](https://learn.chatgpt.com/docs/codex/cli)

Claude Code를 선택했다면 PowerShell에서 실행합니다.

```powershell
irm https://claude.ai/install.ps1 | iex
```

Codex를 선택했다면 PowerShell에서 실행합니다.

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://chatgpt.com/codex/install.ps1 | iex"
```

설치가 끝나면 **PowerShell을 닫고 새로 열어야** PATH가 반영됩니다.

### macOS 권장 경로

1. [VS Code](https://code.visualstudio.com/download)
2. [Git](https://git-scm.com/download/mac)
3. [Python](https://www.python.org/downloads/macos/)
4. [Google Antigravity](https://antigravity.google/)를 설치하고 Google 계정으로 로그인
5. 다음 중 사용할 Coding Agent 하나를 선택
   - [Claude Code](https://code.claude.com/docs/en/setup)
   - [Codex CLI](https://learn.chatgpt.com/docs/codex/cli)

Claude Code를 선택했다면 Terminal에서 실행합니다.

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Codex를 선택했다면 Terminal에서 실행합니다.

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

설치 후 Terminal을 닫고 새로 엽니다.

### 버전 확인

Windows PowerShell:

```powershell
git --version
py --version
code --version
claude --version  # Claude Code 선택자
codex --version   # Codex 선택자
```

macOS Terminal:

```bash
git --version
python3 --version
code --version
claude --version  # Claude Code 선택자
codex --version   # Codex 선택자
```

### 성공 기준

- Git·Python·VS Code가 버전을 표시합니다.
- `claude --version` 또는 `codex --version` 중 선택한 하나가 성공합니다.
- Python은 **3.11 이상**을 사용합니다.
- Antigravity 앱이 열리고 Google 로그인이 완료됩니다.

### 설치가 막힐 때 최소 복구

- `code`만 인식되지 않음: VS Code를 직접 실행해 수업을 계속합니다.
- Windows에서 `python`이 Microsoft Store를 엶: `py` 명령을 사용합니다.
- Claude Code·Codex가 인식되지 않음: 새 터미널을 열고 다시 확인합니다.
- 관리자 권한으로 설치할 수 없음: 강사가 제공한 ZIP과 GitHub 웹 편집 경로로 실습을 계속합니다.
- Windows WSL 경험이 없는 수강생은 수업 중 새로 WSL을 구성하지 않습니다. 환경 분기와 복구 시간이 커집니다.

## 5. STEP 3 — 선택한 Coding Agent 로그인과 진단

### Claude Code 선택자

```bash
claude --version
claude doctor
claude
```

마지막 명령을 실행하고 브라우저 안내에 따라 로그인합니다.

### Codex 선택자

```bash
codex login
```

브라우저가 열리면 자신의 계정으로 로그인합니다. API Key를 Telegram이나 코드에 붙여넣지 않습니다.

로그인 확인:

```bash
codex login status
codex doctor
```

### 성공 기준

- 선택한 Coding Agent의 버전과 로그인 상태가 확인된다.
- `claude doctor` 또는 `codex doctor`에서 실행을 막는 오류가 없다.

## 6. STEP 4 — Git 사용자 설정

아래 이름과 이메일을 **자신의 정보로 바꿔서** 실행합니다.

```bash
git config --global user.name "YOUR NAME"
git config --global user.email "YOUR_GITHUB_EMAIL"
git config --global --list
```

GitHub에서 이메일을 공개하고 싶지 않다면 GitHub의 `noreply` 이메일을 사용할 수 있습니다.

### 성공 기준

`user.name`과 `user.email`이 빈칸이 아닙니다.

## 7. STEP 5 — 개인 프로젝트 저장소 만들기

1. Telegram의 `STARTER_REPO_URL`을 엽니다.
2. **Use this template → Create a new repository**를 선택합니다.
3. 저장소 이름을 `semiconductor-ai-project`로 입력합니다.
4. 교육용 결과를 Pages로 공개하려면 `Public`을 선택합니다.
5. **Create repository**를 누릅니다.
6. 내 저장소의 **Code → HTTPS** 주소를 복사합니다.

> GitHub Pages는 웹에 공개됩니다. 실제 회사 데이터·공정 Spec·장비 로그·고객정보·개인정보·API Key를 절대 넣지 않습니다.

### Clone

Windows PowerShell:

```powershell
cd $HOME\Documents
git clone YOUR_REPOSITORY_HTTPS_URL semiconductor-ai-project
cd semiconductor-ai-project
code .
```

macOS Terminal:

```bash
cd ~/Documents
git clone YOUR_REPOSITORY_HTTPS_URL semiconductor-ai-project
cd semiconductor-ai-project
code .
```

### 성공 기준

- VS Code 왼쪽 탐색기에 `AGENTS.md`, `PLAN.md`, `README.md`, `data`, `src`, `docs`가 보인다.
- Terminal에서 `git status`를 실행하면 현재 브랜치가 표시된다.

## 8. STEP 6 — 자동 환경점검

프로젝트 폴더의 VS Code Terminal에서 실행합니다.

Windows:

```powershell
py tools/student_preflight.py
```

macOS:

```bash
python3 tools/student_preflight.py
```

### 성공 기준

마지막 줄에 다음이 표시됩니다.

```text
READY: core environment checks passed
```

`FAIL`이 있으면 그 줄 전체만 Telegram에 올립니다. 계정정보나 토큰은 올리지 않습니다.

## 9. STEP 7 — 선택한 Coding Agent에게 먼저 읽게 하기

프로젝트 폴더에서 선택한 도구를 실행합니다.

```bash
claude  # Claude Code 선택자
codex   # Codex 선택자
```

첫 프롬프트:

```text
AGENTS.md, README.md, PLAN.md를 먼저 읽어라.
아직 파일을 수정하지 마라.
이 저장소의 입력 데이터, 데이터 감사, 기준모델, 개선모델,
브라우저 시뮬레이션, 테스트, 배포 흐름을 초보자에게 설명하라.
확인되지 않은 반도체 공정 사실은 추가하지 마라.
마지막에 오늘 실행할 명령만 순서대로 제시하라.
```

### 사람이 확인할 것

- Coding Agent가 실제 파일명을 근거로 설명했는가?
- 없는 파일이나 실행 명령을 지어내지 않았는가?
- `data/raw/`를 수정하라고 하지 않았는가?

틀린 내용은 `prompts/AI_USAGE.md`에 기록합니다.

## 9A. STEP 7A — Antigravity 자료조사와 근거 인계

Antigravity에서는 코드를 만들지 않고 주제의 근거를 조사합니다. 공식 문서·교재·논문을 우선하고, 검색 결과 요약문만 근거로 사용하지 않습니다.

```text
내 주제는 [주제]이고 사용자의 결정은 [결정]이다.
관련 전공 원리, Governing equation·도메인 제약 후보,
데이터 변수 정의, 대표적인 분석법과 한계를 조사하라.
각 항목에 원문 URL, 문서명, 생산기관·저자, 발행일,
직접 확인한 사실, 적용 범위, 말하지 않는 것을 구분하라.
확인하지 못한 수치·수식·인과관계는 미확인으로 표시하라.
```

조사 결과를 `research/SOURCES.md`에 다음 형식으로 정리합니다.

```text
출처 ID:
원문 URL:
생산기관·저자 / 날짜:
직접 확인한 사실:
프로젝트에 적용할 범위:
자료가 말하지 않는 것:
내 데이터로 검증할 질문:
```

그다음 Claude Code 또는 Codex에서 다음과 같이 인계합니다.

```text
AGENTS.md, PLAN.md, research/SOURCES.md를 먼저 읽어라.
자료조사의 사실·가설·한계를 구분하고 출처 없는 주장을 추가하지 마라.
코드는 아직 수정하지 말고, 데이터 감사 → 기준모델 → Holdout 평가 →
오차 사례 → 보고서 → GitHub Pages 순서의 실행계획을 작성하라.
단계마다 성공 기준, 변경 파일, 실행 명령을 명시하라.
```

### 성공 기준

- 원문을 직접 확인한 근거카드가 최소 3개 있다.
- 출처가 설명하는 범위와 설명하지 못하는 범위가 구분된다.
- Coding Agent가 근거 없이 공정 수치나 인과관계를 새로 만들지 않는다.

## 10. STEP 8 — 데이터 감사 실행

먼저 [`lessons/01_DATA_QUALITY_AND_VISUALIZATION.md`](../lessons/01_DATA_QUALITY_AND_VISUALIZATION.md)를 열어 결측·이상치·그래프 선택 순서를 확인합니다.

Windows:

```powershell
py src/audit.py
```

macOS:

```bash
python3 src/audit.py
```

반드시 확인할 숫자:

1. 행·열 수
2. 결측값 수
3. 완전 중복행 수
4. 각 수치열의 최소·중앙·최대
5. Lot·Tool별 표본 수
6. 목표변수 분포

### 해석 규칙

- 이상치는 곧바로 삭제하지 않습니다.
- 단위 오류, 센서 오류, 실제 희귀 공정상태를 먼저 구분합니다.
- 전체 상관계수 하나로 원인을 단정하지 않습니다.
- Tool·Lot·시간 편중을 확인한 뒤 가설을 말합니다.

### ggplot2·seaborn 갤러리

- [seaborn Example Gallery](https://seaborn.pydata.org/examples/index.html)
- [ggplot2 Reference](https://ggplot2.tidyverse.org/reference/index.html)

두 갤러리에서 histogram, boxplot, scatterplot, lineplot, heatmap을 비교합니다. 문법을 동시에 암기하지 않고, 실습은 Python·seaborn으로 통일합니다.

Windows:

```powershell
py -m pip install -r requirements-class.txt
py lessons/data_quality_visualization_demo.py
```

macOS:

```bash
python3 -m pip install -r requirements-class.txt
python3 lessons/data_quality_visualization_demo.py
```

생성된 `artifacts/data_quality/cmp_audit_gallery.png`를 열고 다음을 답합니다.

1. 결측은 어디에 몰려 있는가?
2. 이상치 후보는 무엇인가?
3. 전체 관계가 Tool별로 유지되는가?
4. 시간 Drift가 있는가?
5. 처리 전후 결론이 바뀌는가?
6. 어떤 추가 측정이 필요한가?

## 11. STEP 9 — 데모 빌드와 로컬 실행

Windows:

```powershell
py src/build_site.py
py -m http.server 8000 --directory docs
```

macOS:

```bash
python3 src/build_site.py
python3 -m http.server 8000 --directory docs
```

브라우저에서 <http://localhost:8000>을 엽니다.

### 성공 기준

- 화면이 열린다.
- 슬라이더 또는 선택 메뉴 2개 이상을 바꾸면 결과가 갱신된다.
- 기준값·위험도·추천 중 하나가 입력과 함께 변한다.

종료는 Terminal에서 `Ctrl+C`입니다.

## 12. STEP 10 — 최소 변경, 테스트, 첫 Commit

Codex에 다음을 입력합니다.

```text
현재 화면 상단에 내 DATASET_ID를 표시하라.
수정 전에 성공 기준과 변경할 파일을 말하라.
요청과 무관한 리팩터링은 하지 마라.
수정 후 테스트와 빌드를 실행하고 변경 파일을 요약하라.
```

변경을 직접 확인한 뒤 실행합니다.

```bash
git diff
git status
git add README.md docs src tests prompts PLAN.md
git commit -m "Complete first hands-on checkpoint"
git push origin main
```

`git add .` 대신 파일을 지정하여 실제 회사자료나 Key가 섞이지 않았는지 확인합니다.

### 성공 기준

- GitHub 저장소 첫 화면에 새 Commit이 보인다.
- `git status`에 의도하지 않은 파일이 남지 않는다.

## 13. STEP 11 — GitHub Pages 배포

내 GitHub 저장소에서 다음을 클릭합니다.

1. **Settings**
2. 왼쪽 **Pages**
3. **Build and deployment → Source → Deploy from a branch**
4. Branch는 `main`, Folder는 `/docs`
5. **Save**

Pages는 즉시 보이지 않을 수 있습니다. Actions 또는 Pages 화면에서 배포 완료를 확인한 뒤 **Visit site**를 누릅니다.

예상 주소:

```text
https://YOUR_GITHUB_ID.github.io/semiconductor-ai-project/
```

### 성공 기준

- 휴대전화의 모바일 데이터로도 URL이 열린다.
- 저장소가 비공개여도 Pages 공개 범위는 별개일 수 있으므로 민감정보가 전혀 없다.

## 14. STEP 12 — 첫날 제출

`SUBMISSION_FORM_URL`에 다음 네 가지를 제출합니다.

1. 이름·수강생 번호
2. `DATASET_ID`
3. GitHub 저장소 URL
4. GitHub Pages URL

Telegram에는 URL 전체 대신 다음 형식으로 완료 여부만 남깁니다.

```text
12번 ✅ 저장소/Pages 제출 완료 · DATASET 05-CMP-A
```

## 15. 수업 종료 전 체크리스트

- [ ] GitHub·ChatGPT 로그인
- [ ] Git·Python·VS Code·Antigravity 실행
- [ ] Claude Code 또는 Codex 중 하나의 로그인과 진단
- [ ] 개인 저장소 Clone
- [ ] 자동점검 `READY`
- [ ] 데이터 감사 숫자 확인
- [ ] 로컬 웹앱 실행
- [ ] 최소 변경 후 테스트
- [ ] 첫 Commit·Push
- [ ] GitHub Pages URL 제출
- [ ] 문제→전공→도메인 제약→데이터→결정 한 문장 작성
- [ ] 후보 주제 2개 기록

## 공식 설치·배포 근거

- [Google Antigravity 공식 사이트](https://antigravity.google/)
- [Anthropic Claude Code 공식 설치법](https://code.claude.com/docs/en/setup)
- [OpenAI Codex CLI 공식 설치법](https://learn.chatgpt.com/docs/codex/cli)
- [GitHub: 원격 저장소 Clone](https://docs.github.com/en/get-started/using-git/getting-changes-from-a-remote-repository)
- [GitHub Pages 사이트 생성](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)
- [VS Code 공식 다운로드](https://code.visualstudio.com/download)
- [Python 공식 다운로드](https://www.python.org/downloads/)
