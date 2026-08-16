# Virtual Fab · 사라진 선폭의 비밀

React·Three.js·FastAPI로 만든 첫 번째 반도체 공정 문제해결 시나리오다.

## React UI 구조

- `useFabSession` custom hook이 시나리오 로딩·판단 제출·재시작·세션 복원을 관리한다.
- 브라우저 `localStorage`에는 세션 ID만 저장하고, 새로고침하면 FastAPI의 최신 상태를 다시 조회한다.
- `StageProgress`가 진행·완료·대기 상태를 서버 상태에서 파생해 즉시 표시한다.
- `EvidenceDrawer`는 현재 입력을 유지한 채 완료한 판단과 비용·시간을 언제든 확인하게 한다.
- 분석 툴 비용·시간과 Holdout 변화량은 `useMemo`로 즉시 계산해 선택 전에 보여준다.
- 단계별 패널은 React `key` 전환과 reduced-motion 대응 애니메이션으로 교체된다.

## 학습 흐름

1. 평균 CD가 규격 안이어도 edge 산포를 근거로 Lot 보류 여부를 판단한다.
2. DeepSeek API 또는 Gemini·ChatGPT·Claude 등 외부 AI로 질문을 분석하고 답변과 사람의 검증 계획을 함께 기록한다.
3. 평균이 아니라 Tool·Lot·위치별 분포와 데이터 품질을 확인한다.
4. 대조군·요인·반복·판정 기준이 있는 실험을 설계한다.
5. 광학·SEM·TEM·EDX·XPS·전기 분석을 비용·시간·정보가치로 선택한다.
6. Holdout 결과로 적용 범위를 결정하고 Evidence trail을 남긴다.
7. 자신의 판단과 한계를 입력해 STAR 기반 독립형 HTML 면접 슬라이드를 내려받는다.

## 단계별 3D 장면

- 문제 발생: edge 결함 웨이퍼
- AI 협업: External AI Workbench
- 데이터 판단: 3D wafer map
- 실험계획: Screening DOE matrix
- 분석 툴: Optical CD·SEM·I–V 장비 bay
- 검증: Baseline–Holdout 비교 gate

## 게임 캐릭터와 미션 피드백

- 외부 에셋을 복제하지 않고 Three.js 기본 도형으로 만든 저폴리 클린룸 엔지니어 `FAB ROOKIE`를 사용한다.
- 단계가 바뀌면 캐릭터가 다음 스테이션으로 걸어가고 팔·다리·보행 높이가 실시간으로 애니메이션된다.
- 캐릭터 말풍선은 단계별 핵심 사고 질문을 제시하며 정답을 알려주지 않는다.
- Mission HUD가 현재 Quest, 진행 상태, XP를 React 세션 상태와 동기화한다.

## DeepSeek API와 외부 AI fallback

기본 자동 분석은 `deepseek-v4-flash` 비사고 모드를 사용하고 출력은 최대 500토큰으로 제한한다. 서버 `.env`에만 키를 저장하며 브라우저와 GitHub에는 노출하지 않는다.

```bash
cp .env.example .env
# .env의 DEEPSEEK_API_KEY 값을 서버에서만 입력
```

API 키 미설정·잔액 부족·응답 지연 때는 질문 프롬프트를 복사하여 Gemini·ChatGPT·Claude 등에 입력하고 답변을 붙여넣는 방식으로 그대로 진행한다.

저장 항목은 `prompt`, `llm_model`, `llm_response`, `human_check`이며 FastAPI 세션의 Evidence trail과 최종 면접 슬라이드에 함께 남는다. 회사 Recipe·Spec·로그, 개인정보, API 키는 외부 서비스에 입력하지 않는다.

## 로컬 실행

```bash
npm install
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt pytest==8.4.2
npm run build
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8510
```

`http://127.0.0.1:8510`에서 실행한다.

## 검증

```bash
.venv/bin/python -m pytest -q tests/test_api.py
npm run build
npx playwright test
```

## 현재 MVP 한계

- 모든 수치와 데이터는 교육용 합성값이다.
- DeepSeek 또는 외부 AI의 답변은 정답이 아니다. 학습자가 출처·측정 원리·데이터와 대조해 직접 검증해야 한다.
- 세션은 FastAPI 프로세스 메모리에 저장되어 서버 재시작 시 초기화된다.
- 새로고침 복원은 서버 프로세스가 유지되는 동안만 가능하며, 저장된 세션이 사라지면 새 세션을 자동 생성한다.
- 결과는 실제 공정의 인과관계, Recipe 적합성 또는 현장 성과를 입증하지 않는다.
- 실제 기업의 UI·팹 배치·내부 Spec·데이터를 복제하지 않는다.
- 면접 슬라이드의 SVG 이미지는 Base64로 내장되어 다운로드 후 인터넷 없이 실행된다.
