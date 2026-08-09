# 1강 Telegram 진행문 — 20명 동시 실습용

이 문서는 강사가 Telegram에 **한 블록씩 복사해 보내는 운영 대본**입니다. 한꺼번에 전송하지 않습니다. 각 메시지의 완료율을 확인하고 다음 블록을 보냅니다.

## 강의 전 치환할 값

- `[STARTER_REPO_URL]`
- `[SUBMISSION_FORM_URL]`
- `[DATASET_ASSIGNMENT_URL]`
- `[ASSISTANT_NAME]`

## 상태 집계 규칙

- 4개 조 × 5명으로 좌석과 Telegram 번호를 맞춘다.
- 조별 마지막 번호가 완료 인원을 집계한다.
- `✅` 15명 이상이면 다음 단계로 이동한다.
- `🟡`은 파트너가 같이 진행하고, `🔴`은 보조강사가 별도 복구한다.
- 로그인·권한 장애가 10분을 넘으면 ZIP/웹 편집 우회로로 전환한다.

---

## 메시지 01 — 출석과 환경 분류 · 0분

```text
[실습 01/12] 번호와 환경을 한 줄로 답해주세요.
형식: 12번 / Windows 또는 macOS / GitHub 로그인 O·X / ChatGPT 로그인 O·X

완료: ✅
도움 필요: 🟡
진행 불가: 🔴

비밀번호·인증코드·API Key 화면은 올리지 마세요.
```

통과: 20명 번호와 OS를 확인한다.

## 메시지 02 — 결과와 보안 · 5분

```text
[실습 02/12] 오늘 끝날 때 남아야 할 증거는 4개입니다.
1) 내 GitHub 저장소
2) 데이터 감사 결과
3) 작동하는 로컬 웹앱
4) GitHub Pages URL

실제 회사 데이터·공정 Spec·장비 로그·고객정보·개인정보·API Key는
AI, Telegram, GitHub에 입력하지 않습니다.
읽었으면: 번호 + ✅ 보안 확인
```

## 메시지 03 — 숫자를 믿기 전 질문 · 8분

```text
[실습 03/12] 수율 평균이 내려갔다고 가정합니다.
공정이 변한 것일까요, 측정·수집·표본 구성이 변한 것일까요?

결측을 모두 지우면 위험조건까지 지울 수 있습니다.
이상치는 오류일 수도 있지만 실제 Fault일 수도 있습니다.
오늘은 삭제부터 하지 않고 발생 위치와 영향을 먼저 봅니다.

번호 + 결측/이상치 처리 전에 확인할 것 한 가지를 답해주세요.
```

강사는 응답을 Tool·Lot·시간·단위·센서 범위로 묶고 설치로 연결한다.

## 메시지 04 — 공식 설치 페이지 · 18분

```text
[실습 04/12] 아래 공식 사이트만 이용합니다.
VS Code: https://code.visualstudio.com/download
Git: https://git-scm.com/downloads
Python: https://www.python.org/downloads/
Codex: https://github.com/openai/codex

설치 후 터미널을 완전히 닫고 다시 여세요.
Windows는 PowerShell, macOS는 Terminal을 사용합니다.
```

강사 화면: `student/01_FIRST_CLASS_HANDS_ON_MANUAL.md`의 OS별 설치 명령을 띄운다.

## 메시지 05 — 버전 확인 · 30분

```text
[실습 05/12] 버전 네 개를 확인하세요.

Windows PowerShell:
git --version
py --version
code --version
codex --version

macOS Terminal:
git --version
python3 --version
code --version
codex --version

네 개가 보이면: 번호 + ✅ 버전 완료
안 되는 명령이 있으면: 번호 + 🟡 + 명령 이름만
```

15명 완료 시 이동. `code`만 실패하면 VS Code 직접 실행으로 통과시킨다.

## 메시지 06 — Codex 로그인·Git 설정 · 38분

```text
[실습 06/12] 실행:
codex login

브라우저 로그인 후 확인:
codex login status
codex doctor

API Key를 채팅이나 코드에 붙이지 마세요.
진단 완료: 번호 + ✅ Codex
```

이어 따옴표 안을 본인 정보로 바꿔 실행한다.

```text
git config --global user.name "YOUR NAME"
git config --global user.email "YOUR_GITHUB_EMAIL"
git config --global --list
```

## 메시지 07 — 저장소 생성과 Clone · 44분

```text
[실습 07/12]
Starter: [STARTER_REPO_URL]

Use this template → Create a new repository
이름: semiconductor-ai-project
공개범위: Public
생성 후 Code → HTTPS 주소 복사

Windows:
cd $HOME\Documents
git clone YOUR_URL semiconductor-ai-project
cd semiconductor-ai-project
code .

macOS:
cd ~/Documents
git clone YOUR_URL semiconductor-ai-project
cd semiconductor-ai-project
code .

탐색기에 AGENTS.md와 PLAN.md가 보이면: 번호 + ✅ Clone
```

## 메시지 08 — 자동 환경점검 · 50분

```text
[실습 08/12] VS Code Terminal에서 실행하세요.

Windows: py tools/student_preflight.py
macOS: python3 tools/student_preflight.py

READY가 보이면: 번호 + ✅ READY
FAIL이면: 번호 + 🟡 + FAIL 한 줄만 복사
```

강사는 조별 READY 수를 기록한다. 이 시점의 미통과자는 보조강사에게 넘긴다.

## 메시지 09 — 통계적 데이터 감사 · 52분

```text
[실습 09/12] 데이터는 삭제하기 전에 발생 위치부터 봅니다.

Windows: py src/audit.py
macOS: python3 src/audit.py

확인할 숫자:
행·열 / 열별 결측 / 완전 중복 / 수치열 범위 / Tool·Lot 표본 수

Codex를 실행하고 아래 프롬프트를 넣으세요.

AGENTS.md, README.md, PLAN.md를 먼저 읽어라.
아직 수정하지 마라.
입력 데이터→감사→모델→시뮬레이션→테스트→배포 흐름을
실제 파일명을 근거로 설명하라.
없는 파일이나 확인되지 않은 공정 사실을 만들지 마라.

이상치는 자동 삭제하지 말고 단위·센서·Tool·Lot·시간 원인을 구분하세요.
숫자가 확인되면: 번호 + ✅ Audit
```

## 메시지 10 — 그래프 갤러리와 seaborn 실습 · 67분

```text
[실습 10/12] 먼저 갤러리를 엽니다.
seaborn: https://seaborn.pydata.org/examples/index.html
ggplot2: https://ggplot2.tidyverse.org/reference/index.html

질문→그래프:
분포→histogram
Tool 비교→boxplot + 실제 점
변수 관계→scatter
Run Drift→line
결측·상관→heatmap

Windows:
py -m pip install -r requirements-class.txt
py lessons/data_quality_visualization_demo.py

macOS:
python3 -m pip install -r requirements-class.txt
python3 lessons/data_quality_visualization_demo.py

cmp_audit_gallery.png를 열고 결측 위치·Tool 차이·시간 Drift를 말하세요.
되면: 번호 + ✅ Gallery
```

## 메시지 11 — 최소 변경과 Push · 95분

```text
[실습 11/12] Codex에 요청:
화면 상단에 내 DATASET_ID를 표시하라.
수정 전에 성공 기준과 변경 파일을 말하라.
무관한 리팩터링은 하지 마라.
수정 후 테스트와 빌드를 실행하라.

사람이 diff를 확인한 뒤:
git diff
git status
git add README.md docs src tests prompts PLAN.md
git commit -m "Complete first hands-on checkpoint"
git push origin main

GitHub에 Commit이 보이면: 번호 + ✅ Push
```

## 사전 메시지 — 문제발견 질문지 · 수업 전 10분

```text
[사전 준비]
student/00_PROBLEM_DISCOVERY_QUESTIONNAIRE.md를 열고
A·B·C·G 항목을 한 문장씩 먼저 작성하세요.

실제 회사 데이터·Recipe·장비 Log·내부 Spec은 적지 않습니다.
문제 → 관련 전공 → 도메인 제약 → 데이터 → 사용자 결정 순서로 씁니다.
완벽한 주제가 아니라 반복해서 불편했던 문제 1개면 됩니다.

완료 응답: 번호 + ✅ 문제 한 문장
```

## 메시지 12 — 로컬 웹앱·Pages·제출 · 106분

```text
[실습 12/12]
Windows:
py src/build_site.py
py -m http.server 8000 --directory docs

macOS:
python3 src/build_site.py
python3 -m http.server 8000 --directory docs

브라우저에서 http://localhost:8000 확인 후 Ctrl+C

GitHub 저장소 → Settings → Pages
Source: Deploy from a branch
Branch: main / Folder: /docs → Save

제출: [SUBMISSION_FORM_URL]
데이터 배정: [DATASET_ASSIGNMENT_URL]

제출 항목: 번호, DATASET_ID, 저장소 URL, Pages URL
완료 응답: 12번 ✅ 제출 완료 · 05-CMP-A
```

## 종료 2분 안내

```text
다음 작업은 모델을 고르는 것이 아니라 주제를 좁히는 것입니다.
student/00_PROBLEM_DISCOVERY_QUESTIONNAIRE.md를 다시 열어
상관관계와 대안 설명을 각각 1개씩 보완하세요.
student/02_TOPIC_AND_PROJECT_GUIDE.md를 열고
1순위·2순위 후보와 실제 사용자의 결정을 먼저 적으세요.
오늘은 후보 2개까지만, 최종 확정은 데이터 감사 후 합니다.
```

## 강사 비상 우회로

### GitHub Clone 실패

- Starter ZIP을 내려받아 압축 해제한다.
- 로컬 실습은 계속한다.
- 쉬는 시간에 Git 인증을 복구한 뒤 새 저장소에 업로드한다.

### Codex 로그인 실패

- 파트너가 프롬프트를 실행하고 실패자는 결과를 검증·기록한다.
- 브라우저 ChatGPT에서 파일을 통째로 올리지 않고, 공개 가능한 최소 코드만 사용한다.

### Python 실패

- 완성된 `docs/`를 정적 서버 없이 `index.html`로 확인한다.
- 데이터 감사는 강사 화면을 따라 수기로 체크한 뒤 설치를 복구한다.

### Pages 지연 또는 404

- `docs/index.html` 존재 확인
- Pages source가 `main /docs`인지 확인
- Actions 완료 여부 확인
- URL 끝의 저장소 이름과 대소문자 확인
- 배포 지연은 실패로 판정하지 않고 저장소 URL을 먼저 제출
