# SK하이닉스 지원 AI 프로젝트 특강 — 수업 전 개인 노트북 준비

수업: 2026년 8월 14일 19:00~21:00  
대상: SK하이닉스 취업 희망자 10명  
준비 권장 시간: 45~70분  
준비 완료 권장 시각: 수업 당일 18:00

> 이번 수업은 프로그램 설치 강의가 아닙니다. SK하이닉스 채용설명회에서 안내한 것처럼, 제한된 시간에 직무 시나리오의 문제를 정의하고 LLM을 활용한 뒤 자신의 논리로 검증·발표하는 연습을 합니다. 아래 준비를 끝내야 120분을 실습에 사용할 수 있습니다.

## 먼저 구분할 두 가지 AI 환경

이번 준비에는 목적이 다른 두 환경이 있습니다.

1. **면접 모의훈련:** 일반 GPT 채팅 수준의 제한된 LLM을 가정합니다. 파일 편집, 터미널, 자동 코딩, 웹 검색, 멀티에이전트 기능이 없다고 보고 문제 분해·질문·검증·발표를 연습합니다.
2. **수업 후 프로젝트 제작:** Claude Code 또는 Codex로 데이터 분석 코드, 보고서와 GitHub Pages를 만듭니다. 이는 면접장에서 같은 도구를 쓴다는 뜻이 아니라, 지원서에 쓸 실제 경험과 검증 증거를 만드는 제작환경입니다.

설명회 정리에는 `화면 내 전용 LLM`이라고만 기록되어 있습니다. 제품명, 기반 모델, 파일 업로드, 코드 실행, 웹 검색 기능은 아직 확인되지 않았으며 **SK하이닉스 자체 개발 모델이라고 단정하지 않습니다.**

## 0. 수업 전에 완성할 다섯 가지

- [ ] 개인 GitHub 계정으로 강의 저장소를 Fork했다.
- [ ] Fork한 저장소를 개인 노트북에 Clone했다.
- [ ] Git·Python·VS Code가 실행된다.
- [ ] Antigravity와 Claude Code 또는 Codex 중 하나에 로그인했다.
- [ ] 자동점검 마지막 줄에 `READY`가 표시된다.

수업 중에는 새로운 유료 요금제에 가입하지 않습니다. 이미 사용할 수 있는 Claude Code 또는 Codex가 하나도 없다면 사전 설문에 표시하십시오. 강사가 브라우저 기반 대체 경로와 실습 파트너를 배정합니다.

## 1. 준비물과 보안 원칙

### 가져올 것

- Windows 10/11 또는 macOS 13 이상 개인 노트북
- 충전기와 휴대전화
- Chrome 또는 Edge 최신 버전
- 5GB 이상의 여유 저장공간
- GitHub 개인 계정
- Google 계정
- Claude 또는 ChatGPT 계정 중 실제로 사용할 수 있는 계정 하나

### 절대 사용하지 않을 것

- 회사·연구실의 실제 Fab 데이터
- 실제 Recipe, 내부 Spec, 장비 Log, 고객정보
- 개인정보가 들어 있는 파일
- API Key, 비밀번호, 인증 토큰

이번 강의는 공개 저장소와 GitHub Pages를 사용합니다. 모든 실습은 저장소의 **교육용 합성 데이터**로 진행합니다.

## 2. 사전 설문에 먼저 답할 내용

설치 전에 다음 내용을 사전 설문에 입력합니다.

1. 이름과 GitHub ID
2. 노트북 운영체제: Windows 또는 macOS
3. Git·Python·VS Code 설치 여부
4. 사용할 Coding Agent: Claude Code / Codex / 아직 없음
5. Antigravity 설치 및 Google 로그인 여부
6. 가장 관심 있는 직무: 설계 / 소자 / R&D공정 / 양산기술 / 기반기술 / Data Science / 기타
7. AI로 직접 만들어 본 것 한 가지
8. 수업에서 탐구하고 싶은 반도체 문제 한 가지
9. 실제 회사자료를 사용하지 않겠다는 확인

모르는 항목은 추측하지 말고 `모름`이라고 적습니다. 이 답으로 10명을 5개 페어로 배치합니다.

## 3. GitHub 계정부터 만들기

현재 GitHub 계정이 없는 수강생이 많으므로 프로그램 설치 전에 계정부터 만듭니다. 계정 생성은 이메일 인증과 사용자명 선택에 시간이 걸릴 수 있어 수업 중에 처리하지 않습니다.

1. <https://github.com/signup>을 엽니다.
2. 개인 이메일 주소를 입력합니다.
3. 공개해도 괜찮은 영문 사용자명을 정합니다.
4. 이메일로 받은 인증 절차를 완료합니다.
5. <https://github.com/login>에서 다시 로그인합니다.
6. 자신의 프로필 주소를 열어 봅니다.

```text
https://github.com/YOUR_GITHUB_ID
```

### 통과 기준

- 로그인 후 오른쪽 위에 자신의 프로필이 보인다.
- 자신의 프로필 URL이 열린다.
- 사전 설문에 GitHub ID를 입력했다.

사용자명에는 학번, 주민번호, 생년월일 전체를 넣지 않습니다. 비밀번호와 이메일 인증코드를 강사나 채팅방에 보내지 않습니다.

## 4. 필수 프로그램 설치

설치 파일은 검색 광고나 블로그가 아니라 아래 공식 사이트에서만 받습니다.

- [Git](https://git-scm.com/downloads)
- [Python](https://www.python.org/downloads/)
- [VS Code](https://code.visualstudio.com/download)
- [Google Antigravity](https://antigravity.google/)
- [Claude Code 공식 설치](https://code.claude.com/docs/en/setup)
- [Codex CLI 공식 설치](https://learn.chatgpt.com/docs/codex/cli)

### Windows 10/11

1. Git for Windows를 기본 설정으로 설치합니다.
2. Python을 설치합니다. 설치 첫 화면에 `Add python.exe to PATH`가 보이면 체크합니다.
3. VS Code를 설치합니다.
4. PowerShell을 새로 엽니다.
5. 다음 명령을 한 줄씩 실행합니다.

```powershell
git --version
py --version
code --version
```

`python`을 실행했을 때 Microsoft Store가 열리면 수업에서는 `python` 대신 `py`를 사용합니다. WSL을 사용해 본 적이 없다면 이번 수업을 위해 새로 설치하지 않습니다.

### macOS

1. Python과 VS Code를 공식 사이트에서 설치합니다.
2. Terminal을 열고 다음 명령을 실행합니다.

```bash
git --version
python3 --version
```

`git --version`을 처음 실행했을 때 Command Line Tools 설치 창이 나타나면 설치를 완료한 뒤 Terminal을 다시 엽니다. `code` 명령이 없어도 VS Code 앱을 직접 열 수 있으므로 준비 실패가 아닙니다.

### 통과 기준

- Git이 버전 번호를 표시한다.
- Python 3.11 이상이 표시된다.
- VS Code 앱이 열린다.

## 5. 자료조사 도구: Antigravity

1. [Antigravity 공식 사이트](https://antigravity.google/)에서 운영체제에 맞는 앱을 설치합니다.
2. Google 계정으로 로그인합니다.
3. 다음 테스트 질문을 실행합니다.

```text
반도체 포토 공정에서 Dose, Focus, PR 두께와 CD의 관계를 조사하라.
공식 문서나 논문 원문 URL을 우선 제시하고,
확인된 사실·해석·확인하지 못한 내용을 구분하라.
아직 코드나 최종 해답은 만들지 마라.
```

### 통과 기준

- Antigravity가 실행된다.
- 답변에 원문 URL이 최소 1개 표시된다.
- 로그인 화면으로 되돌아가지 않는다.

Antigravity는 **근거 조사**에 사용합니다. 검색 요약을 그대로 사실로 쓰지 않고, 수업에서는 원문·변수·적용 범위를 근거카드로 정리합니다.

## 6. 제작 도구: Claude Code 또는 Codex 중 하나

두 도구를 모두 설치할 필요는 없습니다. 자신이 이미 구독하거나 접근 가능한 도구 하나만 선택합니다.

### A. Claude Code 선택자

Claude Code는 Anthropic의 지원 계정이 필요합니다. 무료 Claude 웹 계정만으로는 Claude Code를 쓸 수 없으므로, 접근권한이 없다면 억지로 결제하지 말고 Codex 또는 대체 경로를 선택합니다.

Windows PowerShell:

```powershell
irm https://claude.ai/install.ps1 | iex
```

macOS Terminal:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

설치 후 터미널을 닫고 새로 열어 확인합니다.

```bash
claude --version
claude doctor
claude
```

마지막 `claude` 명령에서 브라우저 로그인 안내를 완료합니다.

### B. Codex 선택자

공식 [Codex CLI 설치 페이지](https://learn.chatgpt.com/docs/codex/cli)에서 자신의 운영체제 탭을 선택해 설치합니다.

macOS Terminal에서는 다음 공식 독립 설치 명령을 사용할 수 있습니다.

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

설치 후 프로젝트 폴더에서 `codex`를 실행하고 `Sign in with ChatGPT`를 선택합니다.

```bash
codex --version
codex
```

Windows 사용자는 공식 페이지의 Windows 설치 절차를 따릅니다. 수업 직전에 WSL을 새로 구성하지 않습니다.

### 통과 기준

- `claude --version` 또는 `codex --version` 중 하나가 버전을 표시한다.
- 선택한 Agent를 실행했을 때 대화 입력 화면이 열린다.
- 로그인 과정에서 API Key를 텔레그램이나 저장소에 붙여넣지 않았다.

## 7. 강의 저장소 Fork

1. [GitHub](https://github.com/login)에 개인 계정으로 로그인합니다.
2. 이메일 인증이 끝났는지 확인합니다.
3. 강의 저장소를 엽니다.

<https://github.com/waterfirst/semiconductor-ai-hackathon-bootcamp>

4. 오른쪽 위 `Fork`를 누릅니다.
5. Owner가 자신의 GitHub ID인지 확인합니다.
6. 저장소 이름은 그대로 두고 `Create fork`를 누릅니다.
7. 생성된 주소가 아래 형식인지 확인합니다.

```text
https://github.com/YOUR_GITHUB_ID/semiconductor-ai-hackathon-bootcamp
```

### Fork가 필요한 이유

원본 강의자료를 복사하는 것이 목적이 아닙니다. 개인 Fork에서 문제정의, 데이터 감사, AI 활용기록, 실패와 수정 이력을 남기면 **본인이 실제로 수행한 과정**을 Git commit으로 설명할 수 있습니다.

## 8. Git 이름과 이메일 설정

아래 예시를 자신의 정보로 바꿉니다. GitHub에서 이메일을 공개하고 싶지 않다면 GitHub 계정 설정의 `noreply` 이메일을 사용합니다.

Windows PowerShell 또는 macOS Terminal:

```bash
git config --global user.name "YOUR NAME"
git config --global user.email "YOUR_GITHUB_EMAIL"
git config --global --list
```

### 통과 기준

출력에 `user.name`과 `user.email`이 빈칸 없이 표시된다.

## 9. 개인 Fork를 노트북에 Clone

GitHub의 개인 Fork에서 `Code → HTTPS`를 누르고 주소를 복사합니다.

### Windows PowerShell

```powershell
cd $HOME\Documents
git clone https://github.com/YOUR_GITHUB_ID/semiconductor-ai-hackathon-bootcamp.git
cd semiconductor-ai-hackathon-bootcamp
code .
```

### macOS Terminal

```bash
cd ~/Documents
git clone https://github.com/YOUR_GITHUB_ID/semiconductor-ai-hackathon-bootcamp.git
cd semiconductor-ai-hackathon-bootcamp
code .
```

`code .`이 작동하지 않으면 VS Code를 직접 열고 `File → Open Folder`에서 `semiconductor-ai-hackathon-bootcamp` 폴더를 선택합니다.

### 통과 기준

- VS Code 왼쪽에 `AGENTS.md`, `README.md`, `student`, `datasets`, `tools` 폴더가 보인다.
- 터미널에서 `git status`를 실행하면 오류 없이 현재 branch가 표시된다.

## 10. Python 가상환경과 수업 패키지 설치

개인 프로젝트 폴더 안에서만 패키지를 관리하기 위해 `.venv`를 만듭니다.

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-class.txt
```

### macOS Terminal

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements-class.txt
```

### 통과 기준

- 빨간 오류 없이 설치가 끝난다.
- 프로젝트 폴더에 `.venv`가 생긴다.
- `.venv`는 `.gitignore`에 포함되어 있으므로 GitHub에 업로드되지 않는다.

## 11. 자동점검 `READY` 만들기

반드시 Clone한 프로젝트 폴더에서 실행합니다.

### Windows PowerShell

```powershell
.\.venv\Scripts\python.exe tools\student_preflight.py
```

### macOS Terminal

```bash
./.venv/bin/python tools/student_preflight.py
```

정상이라면 마지막 줄에 다음이 표시됩니다.

```text
READY: core environment checks passed
```

`FAIL`이 있다면 전체 화면 대신 **FAIL로 시작하는 줄만** 복사해 사전 설문이나 안내 채널에 제출합니다. 계정명, 토큰, 인증 QR, 비밀번호는 보내지 않습니다.

## 12. 데이터와 그래프 사전 실행

### Windows PowerShell

```powershell
.\.venv\Scripts\python.exe lessons\data_quality_visualization_demo.py
```

### macOS Terminal

```bash
./.venv/bin/python lessons/data_quality_visualization_demo.py
```

다음 파일이 만들어졌는지 확인합니다.

```text
artifacts/data_quality/cmp_audit_gallery.png
```

이미지를 열고 다음 두 질문에 한 문장씩 답합니다.

1. 결측이나 이상치가 어느 변수 또는 집단에 몰려 있는가?
2. 전체 데이터의 관계가 Tool별로 나누었을 때도 유지되는가?

정답을 맞히는 단계가 아닙니다. 숫자를 보고 **추가로 확인할 질문**을 만드는 단계입니다.

## 13. Coding Agent가 저장소를 읽는지 확인

Clone한 프로젝트 폴더에서 선택한 Agent를 실행합니다.

```bash
claude
```

또는:

```bash
codex
```

다음 프롬프트를 그대로 입력합니다.

```text
AGENTS.md, README.md, student/00_PROBLEM_DISCOVERY_QUESTIONNAIRE.md를 먼저 읽어라.
아직 어떤 파일도 수정하지 마라.
이 수업에서 학생이 만들어야 할 증거를 5개로 요약하라.
데이터 분석 전에 확인해야 할 품질 문제를 실제 파일명을 근거로 설명하라.
저장소에 없는 파일·수치·반도체 공정 사실은 만들지 마라.
마지막에 네가 실제로 읽은 파일명을 적어라.
```

### 사람이 확인할 것

- Agent가 실제 파일명을 읽었는가?
- 없는 파일을 읽었다고 말하지 않았는가?
- 코드 수정 없이 설명만 했는가?
- 실제 회사 데이터를 요구하지 않았는가?

이 단계가 지난 역사학 석사논문 지도의 `저장소 파악 → 사료 확인 → 주장 감사`에 해당합니다. 이번에는 `저장소 파악 → 데이터 확인 → 가설·대안가설 감사`로 적용합니다.

## 14. 문제발견 질문지 10분 작성

다음 파일을 엽니다.

[`student/00_PROBLEM_DISCOVERY_QUESTIONNAIRE.md`](00_PROBLEM_DISCOVERY_QUESTIONNAIRE.md)

전체를 완성할 필요는 없습니다. 수업 전에는 아래 여섯 줄만 준비합니다.

```text
관심 직무:
누가 판단하는가:
반복해서 보는 데이터:
내려야 하는 결정:
관련 전공과목:
AI를 써도 사람이 검증해야 할 것:
```

완성 문장:

> **[사용자]**가 **[관측 데이터]**를 보고 **[결정]**할 수 있도록, **[전공 원리 또는 제약]**와 AI 분석을 결합한다.

수업 전에 모델명, 정확도, 결론을 정하지 않습니다. 첫 수업에서 팀원이 질문하고 반박한 뒤 문제를 좁힙니다.

## 15. 수업 전 제출할 준비 증거

사전 설문에 다음 네 가지를 제출합니다.

1. 개인 Fork URL
2. 사용할 Agent와 버전
3. 자동점검 결과: `READY` 또는 `FAIL` 줄
4. 위 문제정의 한 문장

제출 예시:

```text
GitHub: https://github.com/example/semiconductor-ai-hackathon-bootcamp
Agent: Claude Code 2.x / 또는 Codex 0.x
Status: READY
Problem: 포토 공정 엔지니어가 Dose·Focus·PR 조건을 보고 먼저 검증할 작은 DOE 조건을 고를 수 있도록 공정 원리와 AI 분석을 결합한다.
```

## 16. 준비 상태별 수업 참여 경로

### GREEN — 정상 참여

- Fork·Clone·Agent 로그인·`READY` 완료
- 개인 노트북에서 데이터 감사와 Agent 실습 진행

### YELLOW — 부분 참여

- GitHub 로그인은 되지만 로컬 설치 또는 Agent 하나가 실패
- 18:30까지 도착해 강사에게 `FAIL` 줄을 보여준다.
- 준비가 끝난 학생과 페어로 문제해결 PT를 먼저 수행한다.
- 설치는 수업을 멈추지 않고 쉬는 시간 또는 수업 후 복구한다.

### RED — 브라우저 대체 참여

- 노트북 사용 불가 또는 GitHub 로그인이 안 됨
- 사전 설문에 미리 표시한다.
- 강사가 제공하는 브라우저 자료와 페어의 실행환경으로 시나리오 분석·검증·발표에 참여한다.
- 개인 포트폴리오 구축은 수업 후 별도 보완한다.

## 17. 자주 발생하는 문제

### `git`을 찾을 수 없음

- 터미널을 모두 닫고 새로 엽니다.
- 해결되지 않으면 Git for Windows를 다시 설치합니다.

### Windows에서 `python`이 Microsoft Store를 엶

- `python` 대신 `py`를 사용합니다.

### `claude` 또는 `codex`를 찾을 수 없음

- 설치 후 터미널을 새로 열었는지 확인합니다.
- 공식 설치 페이지의 운영체제별 절차와 비교합니다.
- 수업 직전에 여러 설치법을 반복하지 말고 `FAIL: agent command not found`라고 제출합니다.

### GitHub Clone에서 인증 실패

- 브라우저에서 자신의 Fork가 실제로 생성됐는지 확인합니다.
- 주소가 `waterfirst` 원본이 아니라 자신의 GitHub ID인지 확인합니다.
- 비밀번호나 토큰을 채팅방에 보내지 않습니다.

### 패키지 설치가 오래 걸림

- 네트워크를 바꾸며 여러 번 동시에 실행하지 않습니다.
- 오류 마지막 10줄만 저장하고 YELLOW로 제출합니다.

## 18. 수업에서 실제로 할 일

설치를 끝낸 상태에서 10명이 5개 페어로 다음 과정을 수행합니다.

1. SK하이닉스 직무 시나리오에서 사실·목표·제약과 판단 기준 찾기
2. 채팅형 LLM에 문제 재진술·원인 후보·대안 가설·추가 확인 질문을 나누어 요청하기
3. AI 답변을 데이터·전공 원리·반례로 검증하기
4. 짧은 문제해결 PT와 꼬리질문 진행하기
5. 교육용 데이터 감사와 작은 프로젝트 범위 확정하기
6. 일주일 동안 남길 GitHub 증거 계획 작성하기

목표는 수업 두 시간 안에 완성품을 만드는 것이 아닙니다. **면접에서 설명할 수 있는 문제해결 과정과, 일주일 동안 완성할 검증 가능한 프로젝트의 출발점**을 만드는 것입니다.

## 최종 확인

- [ ] 개인 Fork URL을 제출했다.
- [ ] `READY` 또는 정확한 `FAIL` 줄을 제출했다.
- [ ] 사용할 Agent 하나가 정해졌다.
- [ ] 문제정의 한 문장을 작성했다.
- [ ] 실제 회사정보와 인증정보를 저장소에 넣지 않았다.
- [ ] 노트북과 충전기를 준비했다.

이 여섯 항목이 끝나면 수업 준비가 완료된 것입니다.
