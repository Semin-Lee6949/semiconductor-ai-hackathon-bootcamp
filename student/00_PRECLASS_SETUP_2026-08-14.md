# SK하이닉스 지원 AI 프로젝트 특강 — 수업 전 완전 준비

수업: 2026년 8월 14일 19:00–21:00

대상: Windows 노트북을 사용하는 이공계 수강생

예상 준비시간: 45–60분

완료 권장시각: 수업 시작 3시간 전

> 수업은 설치 시간이 아니라 문제 정의·데이터 분석·Agent 활용에 집중합니다. 아래 순서대로 하면 처음 사용하는 사람도 준비할 수 있습니다. 한 단계가 막혀도 다음 단계로 조용히 넘어가지 말고 해당 단계의 오류 대응을 확인합니다.

## 수업 전 최종 완료 기준

- [ ] GitHub 계정을 만들고 이메일 인증을 완료했다.
- [ ] 강의 저장소를 내 계정으로 Fork했다.
- [ ] 개인 Fork를 노트북에 Clone하고 VS Code로 열었다.
- [ ] Git·Python·VS Code가 실행된다.
- [ ] Claude Code 또는 Codex 중 하나를 설치하고 로그인했다.
- [ ] Antigravity를 설치하고 Google 계정으로 로그인했다.
- [ ] Python 가상환경과 강의 패키지를 설치했다.
- [ ] 자동점검 마지막 줄에서 `READY`를 확인했다.
- [ ] 교육용 데이터 그래프를 한 번 생성했다.

## 0. 준비물과 보안

준비물:

- Windows 10/11 개인 노트북과 충전기
- Chrome 또는 Edge
- 개인 이메일, Google 계정
- Claude 또는 ChatGPT 계정 중 Coding Agent 사용이 가능한 계정 하나
- 5GB 이상 여유 저장공간

사용 금지:

- 실제 Fab 데이터, Recipe, 내부 Spec, 장비 Log
- 회사·연구실·고객 정보와 개인정보
- API Key, 비밀번호, 인증코드

실습은 공개 저장소의 교육용 합성 데이터만 사용합니다.

## 1. GitHub 계정 생성과 인증

설문 응답자 중 GitHub 계정이 없는 사람이 많으므로 가장 먼저 끝냅니다.

1. [GitHub 가입](https://github.com/signup)을 엽니다.
2. 개인 이메일 또는 `Continue with Google`을 선택합니다.
3. 공개해도 괜찮은 영문 사용자명을 정합니다.
4. 이메일 인증을 완료합니다.
5. [GitHub 로그인](https://github.com/login) 후 자신의 프로필을 엽니다.

```text
https://github.com/YOUR_GITHUB_ID
```

완료 기준:

- 프로필 화면이 열린다.
- 주소에 자신의 GitHub ID가 보인다.
- 비밀번호와 인증코드를 누구에게도 보내지 않았다.

## 2. Windows 기본 프로그램 설치

아래 공식 페이지에서 설치합니다.

1. [Git for Windows](https://git-scm.com/download/win): 기본 설정으로 설치
2. [Python for Windows](https://www.python.org/downloads/windows/): Windows installer로 설치
3. [VS Code User Installer](https://code.visualstudio.com/docs/setup/windows): User Setup 설치

설치가 끝나면 기존 PowerShell을 닫고 **새 PowerShell**을 엽니다.

```powershell
git --version
py --version
code --version
```

완료 기준:

- 세 명령이 버전 번호를 표시한다.
- VS Code가 열린다.

오류 대응:

- `python`이 Microsoft Store를 열면 `py`를 사용합니다.
- `code`만 인식하지 못하면 VS Code를 직접 실행합니다.
- 설치 후 명령을 못 찾으면 PowerShell을 닫고 새로 엽니다.
- WSL은 이번 준비를 위해 새로 설치하지 않습니다.

## 3. Claude Code 또는 Codex 한 개 설치

둘 다 설치하지 않습니다. 본인이 접근 가능한 도구 하나를 선택합니다.

### A. Claude Code 선택

Windows PowerShell:

```powershell
irm https://claude.ai/install.ps1 | iex
```

PowerShell을 새로 연 뒤:

```powershell
claude --version
claude doctor
claude
```

브라우저 로그인 안내가 나타나면 본인 Claude 계정으로 완료합니다.

### B. Codex 선택

[OpenAI Codex 공식 안내](https://developers.openai.com/codex/)를 먼저 엽니다.

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://chatgpt.com/codex/install.ps1 | iex"
```

PowerShell을 새로 연 뒤:

```powershell
codex --version
codex login
codex
```

`Sign in with ChatGPT`을 선택해 로그인합니다.

완료 기준:

- `claude --version` 또는 `codex --version` 중 하나가 버전을 표시한다.
- 선택한 Agent에 문장을 입력할 수 있다.
- API Key를 채팅방이나 코드에 붙여넣지 않았다.

계정 접근권한 때문에 설치할 수 없다면 새 요금제를 결제하지 말고, 사용하는 브라우저 LLM에 로그인한 뒤 강사에게 미리 알립니다.

## 4. Antigravity 설치와 조사 테스트

1. [Google Antigravity](https://antigravity.google/)를 설치합니다.
2. Google 계정으로 로그인합니다.
3. 아래 질문을 실행합니다.

```text
반도체 포토 공정에서 Dose, Focus, PR 두께와 CD의 관계를 조사하라.
공식 문서나 논문 원문 URL을 우선 제시하라.
확인된 사실, 해석, 확인하지 못한 내용을 구분하라.
아직 코드나 최종 해답은 만들지 마라.
```

완료 기준:

- 원문 URL이 한 개 이상 표시된다.
- 사실과 해석이 구분되어 있다.
- 로그인 화면으로 되돌아가지 않는다.

## 5. 강의 저장소 Fork

1. [강의 저장소](https://github.com/waterfirst/semiconductor-ai-hackathon-bootcamp)를 엽니다.
2. 오른쪽 위 `Fork`를 누릅니다.
3. Owner가 자신의 GitHub ID인지 확인합니다.
4. 저장소 이름을 바꾸지 않고 `Create fork`를 누릅니다.

완성 주소:

```text
https://github.com/YOUR_GITHUB_ID/semiconductor-ai-hackathon-bootcamp
```

완료 기준: 주소의 `waterfirst`가 자신의 GitHub ID로 바뀌어 있습니다.

## 6. Git 사용자 설정과 Clone

아래 이름과 이메일을 자신의 정보로 바꿉니다.

```powershell
git config --global user.name "YOUR NAME"
git config --global user.email "YOUR_GITHUB_EMAIL"
git config --global --list
```

개인 Fork에서 `Code → HTTPS`를 눌러 주소를 복사한 뒤 실행합니다.

```powershell
cd $HOME\Documents
git clone https://github.com/YOUR_GITHUB_ID/semiconductor-ai-hackathon-bootcamp.git
cd semiconductor-ai-hackathon-bootcamp
code .
```

완료 기준:

- VS Code 왼쪽에 `README.md`, `student`, `datasets`, `tools`가 보인다.
- VS Code Terminal에서 `git status`가 오류 없이 실행된다.

`code .`이 실패하면 VS Code를 직접 열고 `File → Open Folder`에서 해당 폴더를 선택합니다.

## 7. Python 가상환경과 패키지 설치

VS Code Terminal 또는 PowerShell에서 프로젝트 폴더인지 먼저 확인합니다.

```powershell
Get-Location
```

경로 끝이 `semiconductor-ai-hackathon-bootcamp`인지 확인한 뒤 실행합니다.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-class.txt
```

완료 기준:

- 빨간 오류 없이 설치가 끝난다.
- 프로젝트 폴더에 `.venv`가 생긴다.

설치가 오래 걸려도 창을 닫지 않습니다. `Access denied`가 나오면 OneDrive가 아닌 `$HOME\Documents` 아래에서 다시 Clone합니다.

## 8. 자동점검 READY 확인

```powershell
.\.venv\Scripts\python.exe tools\student_preflight.py
```

정상 마지막 줄:

```text
READY: core environment checks passed
```

`FAIL`이 있으면 `FAIL`로 시작하는 줄만 복사해 강사에게 보냅니다. 전체 화면, 계정명, 토큰, 인증 QR은 보내지 않습니다.

## 9. 교육용 데이터와 그래프 실행

```powershell
.\.venv\Scripts\python.exe lessons\data_quality_visualization_demo.py
```

생성 파일:

```text
artifacts\data_quality\cmp_audit_gallery.png
```

이미지를 열고 아래 두 질문에 한 문장씩 답합니다.

1. 결측이나 이상치가 어느 변수 또는 집단에 몰려 있는가?
2. 전체 관계가 Tool별로 나누어도 유지되는가?

## 10. Agent가 저장소를 읽는지 확인

프로젝트 폴더의 VS Code Terminal에서 선택한 Agent를 실행합니다.

```powershell
claude
```

또는:

```powershell
codex
```

첫 요청:

```text
이 저장소의 README.md, AGENTS.md, student 폴더를 읽어라.
파일을 수정하지 말고 강의 목적, 사용 가능한 데이터, 수업 전 준비 상태를 요약하라.
그다음 내가 확인해야 할 항목을 5개 이내로 제시하라.
```

완료 기준:

- Agent가 저장소 이름과 `datasets`, `student` 폴더를 언급한다.
- 아직 파일을 수정하지 않는다.

## 11. 최종 제출 메시지

수업 시작 전에 아래 양식만 채워 보냅니다.

```text
GitHub ID: ______
Fork URL: https://github.com/______/semiconductor-ai-hackathon-bootcamp
Agent: Claude Code / Codex
Antigravity: 완료 / 오류
Preflight: READY / FAIL 한 줄
그래프 생성: 완료 / 오류
관심 주제: ______
```

준비가 완료되면 수업에서는 설치를 반복하지 않고 바로 문제 정의와 데이터 분석을 시작합니다.
