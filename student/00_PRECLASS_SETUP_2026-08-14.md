# SK하이닉스 지원 AI 프로젝트 특강 — 수업 전 준비

수업: 2026년 8월 14일 19:00–21:00

준비 시간: 약 20–30분

대상 환경: Windows 노트북

> 설문 응답 9명 모두 Windows를 사용하고, 7명은 GitHub 계정이 없습니다. 따라서 수업 전에는 계정과 기본 프로그램만 준비합니다. Claude Code·Codex·Antigravity 설치는 선택입니다.

## 수업 전 필수 완료 4개

- [ ] GitHub 계정을 만들고 이메일 인증을 끝냈다.
- [ ] Chrome 또는 Edge에서 사용할 LLM에 로그인했다.
- [ ] Git, Python, VS Code를 설치했다.
- [ ] 아래 세 명령 중 두 개 이상에서 버전 번호가 보인다.

```powershell
git --version
py --version
code --version
```

완료되지 않아도 수업에는 참석합니다. 오류 화면을 캡처해 오면 페어 실습 경로로 바로 연결합니다.

## 1. GitHub 계정 만들기 — 가장 먼저

설문 응답자 대부분에게 필요한 단계입니다.

1. [GitHub 가입](https://github.com/signup)을 엽니다.
2. 개인 이메일 또는 `Continue with Google`을 선택합니다.
3. 공개해도 괜찮은 영문 사용자명을 정합니다.
4. 이메일 인증을 완료합니다.
5. [GitHub 로그인](https://github.com/login) 후 아래 주소가 열리는지 확인합니다.

```text
https://github.com/내_GitHub_ID
```

**완료 기준:** 자신의 프로필 화면이 보입니다.

**주의:** 비밀번호와 인증코드는 강사·텔레그램·저장소에 보내지 않습니다.

## 2. 사용할 LLM 하나에 로그인

현재 유료로 사용하는 서비스 하나만 준비합니다.

- [ChatGPT](https://chatgpt.com/)
- [Claude](https://claude.ai/)
- [Gemini](https://gemini.google.com/)

**완료 기준:** 새 대화를 열고 `CSV 데이터의 결측치를 확인하는 순서를 알려줘`라고 질문할 수 있습니다.

> 유료 가입을 새로 하지 않습니다. 수업의 목표는 비싼 모델 사용이 아니라 문제 정의·데이터 검증·사람의 판단을 증명하는 것입니다.

## 3. Windows 필수 프로그램 3개

공식 사이트에서만 설치합니다.

1. [Git for Windows](https://git-scm.com/download/win) — 기본 설정으로 설치
2. [Python for Windows](https://www.python.org/downloads/windows/) — Windows installer 사용
3. [VS Code User Installer](https://code.visualstudio.com/docs/setup/windows) — 사용자용 설치 권장

설치 후 **PowerShell을 새로 열고** 확인합니다.

```powershell
git --version
py --version
code --version
```

**완료 기준:** 버전 번호가 표시되고 VS Code가 열립니다.

**막힐 때:** `python`이 Microsoft Store를 열면 수업에서는 `py`를 사용합니다. WSL은 새로 설치하지 않습니다.

## 4. 강의 페이지와 데이터 열기

1. [실전 강의 페이지](https://waterfirst.github.io/semiconductor-ai-hackathon-bootcamp/)를 즐겨찾기합니다.
2. 페이지의 `주제·데이터`에서 관심 주제 하나를 누릅니다.
3. `A · 학습 데이터` CSV를 다운로드합니다.
4. 파일이 Excel 또는 메모장에서 열리는지 확인합니다.

**완료 기준:** CSV의 열 이름과 숫자 데이터가 보입니다.

## 선택 준비 — 이미 사용 중인 사람만

아래 도구가 이미 설치돼 있거나 계정 접근이 되는 사람만 준비합니다. 처음 사용하는 사람은 수업 중 강사 시연과 페어 실습으로 진행합니다.

- [Google Antigravity](https://antigravity.google/): 원문·논문·공식자료 조사
- [Claude Code 설치 안내](https://code.claude.com/docs/en/setup): Claude 구독·접근 가능자
- [OpenAI Codex](https://developers.openai.com/codex/): ChatGPT 계정에서 접근 가능한 사용자

두 Coding Agent를 모두 설치할 필요가 없습니다.

## 수업에 가져올 것

- 충전된 Windows 노트북과 충전기
- Chrome 또는 Edge
- GitHub ID
- 관심 반도체 직무 한 가지
- AI로 해결해 보고 싶은 작은 문제 한 가지

문제 예시:

- Photo 조건과 CD 산포의 관계를 어떻게 확인할까?
- 설비 신호에서 이상 구간을 어떻게 찾을까?
- 여러 Recipe 중 다음 DOE 후보를 어떻게 고를까?

## 수업 전에는 하지 않을 것

- 저장소 Fork·Clone
- Streamlit 배포
- GitHub Pages 설정
- Claude Code·Codex 강제 설치
- API Key 발급
- 실제 회사·연구실 데이터 준비

이 작업은 수업에서 구조를 보고, 수업 후 개인 프로젝트에서 단계별로 수행합니다.

## 보안 원칙

실제 Fab 데이터, Recipe, 내부 Spec, 장비 Log, 고객정보, 개인정보, API Key는 사용하지 않습니다. 강의 페이지에서 제공하는 교육용 합성 데이터만 사용합니다.

## 수업 시작 직전 체크

다음 네 줄을 텔레그램에 보낼 수 있으면 준비 완료입니다.

```text
GitHub ID: ______
사용 LLM: ChatGPT / Claude / Gemini
버전 확인: Git O / Python O / VS Code O
관심 주제: ______
```

준비가 덜 된 경우에도 `GitHub 없음 / 설치 오류`라고 적고 참석합니다. 강사는 페어를 배정해 분석 흐름부터 진행합니다.
