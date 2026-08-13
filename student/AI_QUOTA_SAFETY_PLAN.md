# 강의용 AI 사용량 보호 계획

수업: 19:00–21:00

## 수업 전

1. **14:00 이후 Claude·ChatGPT·Codex로 긴 작업을 하지 않습니다.**
2. 18:30에 주 AI의 로그인과 사용량 화면만 확인합니다.
3. 새 질문, 파일 업로드, Deep Research, 긴 코드 분석은 실행하지 않습니다.
4. Claude·GPT 사용자는 비상용으로 Gemini 또는 Antigravity 로그인만 준비합니다.
5. AI 계정·토큰을 다른 수강생과 공유하지 않습니다.

## 수업 중 AI 사용은 3회

| 시점 | AI에게 맡길 일 | 입력 |
|---|---|---|
| 1회 | 문제·가설·계획 | 데이터 설명과 `PLAN.md` |
| 2회 | 최소 분석 코드 | 승인한 계획과 필요한 파일만 |
| 3회 | 결과 검수·보고서 | `git diff`, 테스트, 핵심 그래프 |

- 매 단계마다 **새 대화**를 사용합니다.
- 저장소 전체 대신 필요한 파일만 전달합니다.
- Extended thinking·Deep Research·불필요한 웹 검색은 끕니다.
- 같은 오류를 AI에 반복 질문하지 않고 오류 한 줄과 재현 명령만 보냅니다.

## 한도 발생 시 전환 순서

1. 주 AI: Claude / GPT / Gemini
2. 비상 AI: Gemini 또는 Antigravity
3. 같은 조의 다른 AI 사용자와 페어 검토
4. 저장소에 준비된 **로컬 스크립트**를 직접 실행
5. 강사 제공 기준 결과와 비교해 보고서 작성

AI가 멈춰도 아래 작업은 계속할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe tools\student_preflight.py
.\.venv\Scripts\python.exe lessons\data_quality_visualization_demo.py
python -m pytest -q
git diff
```

## 강의 운영 원칙

- 추가 크레딧 구매는 필수가 아닙니다.
- 자동 충전은 강의 준비를 위해 켜지 않습니다.
- AI가 응답하지 않아도 프로젝트 실패로 평가하지 않습니다.
- 평가 대상은 `PLAN.md`, 실행 결과, Holdout 검증, 그래프, 수정 판단과 보고서입니다.
