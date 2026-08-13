# SK하이닉스 AI 프로젝트 특강 — 사전 준비

대상: Windows 노트북 · 예상 시간: 45분

> 아래 순서대로 설치하고 마지막 점검 결과만 보내 주세요. 비밀번호·인증코드·토큰은 누구에게도 보내지 않습니다.

## 1. 계정 가입

- [GitHub 가입](https://github.com/signup) → 이메일 인증
- [Streamlit 가입](https://share.streamlit.io/) → **Continue with GitHub** 선택

## 2. 기본 프로그램 설치

아래 링크에서 Windows 버전을 설치합니다.

1. [Git](https://git-scm.com/download/win)
2. [VS Code](https://code.visualstudio.com/download)
3. [Python](https://www.python.org/downloads/windows/) — 설치 화면에서 **Add Python to PATH** 선택
4. 아래 **AI 트랙 중 구독 중인 하나만** 준비

| 구독 | 설치·로그인 | 프로젝트 실행 |
|---|---|---|
| Claude | [Claude Desktop](https://claude.com/download) | Claude Desktop 또는 Claude Code |
| GPT | [ChatGPT Desktop](https://chatgpt.com/download) | ChatGPT Desktop 또는 Codex |
| Gemini | [Google Antigravity](https://antigravity.google/download) | Gemini 또는 Antigravity |

세 서비스를 모두 설치할 필요가 없습니다. 수업에서는 같은 [공통 프로젝트 프롬프트](../templates/UNIVERSAL_AI_PROJECT_PROMPT.md)를 사용합니다.

### 강의 당일 사용량 보호

- Claude·GPT 구독자는 **14:00 이후 긴 대화와 Agent 작업을 중지**합니다.
- 18:30에는 로그인과 사용량 화면만 확인하고 테스트 질문은 보내지 않습니다.
- Claude·GPT 사용자는 비상용 Gemini 또는 Antigravity 로그인도 준비합니다.
- 수업에서는 [3회용 압축 프롬프트](../templates/COMPACT_AI_PROMPTS.md)만 사용합니다.
- 추가 크레딧 구매나 자동 충전은 필수가 아닙니다.

설치 후 PowerShell을 새로 열고 확인합니다.

```powershell
git --version
py --version
code --version
```

세 명령 모두 버전 번호가 나오면 완료입니다.

## 3. 프로젝트 폴더 만들기

GitHub에서 강의 저장소를 `Fork`한 뒤, PowerShell에서 `YOUR_GITHUB_ID`를 바꿔 실행합니다.

```powershell
cd $HOME\Documents
git clone https://github.com/YOUR_GITHUB_ID/semiconductor-ai-hackathon-bootcamp.git semiconductor-ai-project
cd semiconductor-ai-project
code .
```

## 4. 필수 Python 패키지 설치

프로젝트 폴더의 PowerShell에서 실행합니다.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-class.txt
```

## 5. GitHub Class Token 저장

GitHub → `Settings` → `Developer settings` → `Personal access tokens` → `Fine-grained tokens` → `Generate new token`

- 이름: `SK-AI-Class`
- 만료: 7일
- Repository access: 개인 Fork 저장소 하나만 선택
- Repository permissions: `Contents — Read and write`

토큰은 발급 직후 한 번만 보입니다. 복사한 뒤 다음을 실행합니다.

```powershell
Copy-Item .env.example .env
code .env
```

`.env`에 붙여 넣고 저장합니다.

```text
AI_PROVIDER=claude
GITHUB_CLASS_TOKEN=YOUR_FINE_GRAINED_TOKEN
```

`AI_PROVIDER`는 자신의 구독에 따라 하나만 입력합니다.

- Claude: `claude`
- GPT·ChatGPT: `openai`
- Gemini: `gemini`

> `.env`는 이미 `.gitignore`에 등록되어 있습니다. 토큰을 GitHub·메일·텔레그램·화면 캡처에 노출하지 않습니다. 일반 `git push`는 브라우저 로그인을 우선 사용합니다.

## 6. 최종 확인

```powershell
.\.venv\Scripts\python.exe tools\student_preflight.py
```

마지막 줄에 다음 문구가 나오면 준비 완료입니다.

```text
READY: core environment checks passed
```

강사에게는 아래 항목만 보냅니다.

```text
GitHub ID: ______
Streamlit 가입: 완료 / 미완료
선택 AI: Claude / GPT / Gemini
선택 AI 로그인: 완료 / 미완료
비상 Gemini 로그인: 완료 / 미완료
14시 이후 AI 사용 중지: 확인
Preflight: READY / FAIL
```

## 추가 준비

- Chrome 또는 Edge 최신 버전
- 노트북 충전기와 마우스
- 저장공간 5GB 이상
- 실제 회사·연구실 데이터가 아닌 공개 또는 교육용 데이터만 사용
