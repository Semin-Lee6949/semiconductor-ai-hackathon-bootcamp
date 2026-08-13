# SK하이닉스 AI 프로젝트 특강 — 수업 전 준비

대상: Windows 노트북 · 예상 시간: 30~45분

> 모든 명령은 **PowerShell**에서 한 줄씩 실행합니다. 토큰·API 키·비밀번호는 강사에게 보내지 않습니다.

## 0. 프로젝트 폴더 만들기

```powershell
cd $HOME\Documents
mkdir sk-ai-project
cd sk-ai-project
New-Item .env -ItemType File -Force
Set-Content .gitignore ".env`n.venv/`n__pycache__/"
```

## 1. GitHub 가입 · Class Token 발급

1. [GitHub 가입](https://github.com/signup) 후 이메일 인증
2. [새 저장소](https://github.com/new)에서 빈 저장소 `sk-ai-project` 생성
3. [Fine-grained token 발급](https://github.com/settings/personal-access-tokens/new)
4. 이름 `SK-AI-Class`, 만료 `7일`, 본인 계정 선택
5. Repository access에서 `Only select repositories` → `sk-ai-project` 선택
6. 권한은 `Contents: Read and write`, 발급 후 토큰 복사

```powershell
notepad .env
```

`.env`에 저장합니다.

```text
GITHUB_CLASS_TOKEN=여기에_발급받은_토큰
```

> `.env`는 GitHub에 올리지 않습니다. 토큰 화면을 캡처하거나 공유하지 않습니다.

## 2. Git 설치 · 이름과 이메일 설정

```powershell
winget install -e --id Git.Git
```

PowerShell을 닫았다가 다시 열고 실행합니다.

```powershell
git config --global user.name "본인 영문 이름"
git config --global user.email "GitHub 가입 이메일"
git --version
git config --global --list
```

## 3. Python 설치

```powershell
winget install -e --id Python.Python.3.13
```

PowerShell을 다시 연 뒤 확인합니다.

```powershell
py --version
```

## 4. VS Code 설치

```powershell
winget install -e --id Microsoft.VisualStudioCode
```

프로젝트 폴더를 엽니다.

```powershell
cd $HOME\Documents\sk-ai-project
code .
```

VS Code 확장 프로그램에서 `Python`과 `Jupyter`를 설치합니다.

## 5. Claude Code 또는 Codex 설치

**구독 중인 서비스 하나만 설치합니다.**

### Claude 구독자

```powershell
irm https://claude.ai/install.ps1 | iex
claude --version
claude
```

브라우저가 열리면 Claude 계정으로 로그인합니다.

### GPT 구독자

```powershell
winget install -e --id OpenJS.NodeJS.LTS
```

PowerShell을 다시 연 뒤 실행합니다.

```powershell
npm install -g @openai/codex
codex --version
codex
```

첫 실행에서 **Sign in with ChatGPT**를 선택합니다.

## 6. Antigravity 설치 · 조사 테스트

1. [Google Antigravity 다운로드](https://antigravity.google/download)
2. 설치 후 Google 계정으로 로그인
3. `sk-ai-project` 폴더 열기
4. 아래 문장으로 한 번만 테스트

```text
반도체 Photo 공정에서 CD에 영향을 주는 주요 변수를 조사하고,
공식 문서나 논문 URL과 함께 5개 이내로 정리해 줘.
파일은 수정하지 마.
```

## 7. Google AI Studio 가입 · API 키 저장

1. [Google AI Studio](https://aistudio.google.com/) 로그인
2. [API Keys](https://aistudio.google.com/apikey)에서 키 생성
3. 프로젝트 폴더에서 실행

```powershell
cd $HOME\Documents\sk-ai-project
code .env
```

기존 GitHub 토큰 아래에 추가합니다.

```text
GITHUB_CLASS_TOKEN=여기에_발급받은_토큰
GEMINI_API_KEY=여기에_Gemini_API_키
```

> 결제 등록은 필수가 아닙니다. API 키도 화면·메일·메신저·GitHub에 공개하지 않습니다.

## 8. Streamlit Community Cloud 가입

1. [Streamlit Community Cloud](https://share.streamlit.io/) 접속
2. **Continue with GitHub** 선택
3. GitHub 연결 승인

## 최종 확인

```powershell
cd $HOME\Documents\sk-ai-project
git --version
py --version
code --version
claude --version
# 또는
codex --version
```

- [ ] 프로젝트 폴더와 `.env` 생성
- [ ] GitHub 가입·이메일 인증·Class Token 저장
- [ ] Git·Python·VS Code 설치
- [ ] Claude Code 또는 Codex 로그인
- [ ] Antigravity 조사 테스트
- [ ] Google AI Studio API 키 저장
- [ ] Streamlit 가입

준비가 안 된 항목만 강사에게 알려 주세요. **토큰과 API 키 값은 보내지 않습니다.**
