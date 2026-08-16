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
2. 같은 seed로 재현되는 3개 Lot 합성 원시 데이터 CSV를 다운로드해 결측·단위·Tool·위치 분포를 확인한다.
3. 공정별 핵심 용어 6개의 뜻과 데이터 관련성을 확인하고, 질문에 최소 1개를 포함한다.
4. OpenAI·Gemini·Anthropic·DeepSeek와 최대 15회 후속 질문을 `용어·데이터 이해 → 경쟁 가설 → 반증·누락 점검 → 판단 압축 → PT 최종 요약` 순서로 사용한다.
5. 대조군·요인·반복·판정 기준이 있는 실험을 설계한다.
6. 광학·SEM·TEM·EDX·XPS·전기 분석을 비용·시간·정보가치로 선택한다.
7. Holdout 결과로 적용 범위를 결정하고 Evidence trail을 남긴다.
8. 자신의 판단과 한계를 입력해 공정 키워드 맵을 포함한 STAR 기반 독립형 HTML 면접 슬라이드를 내려받는다.

## 단계별 3D 장면

- 문제 발생: edge 결함 웨이퍼
- 데이터·AI 공동분석: CSV + External AI Workbench + wafer map
- 실험계획: Screening DOE matrix
- 분석 툴: Optical CD·SEM·I–V 장비 bay
- 검증: Baseline–Holdout 비교 gate

## 게임 캐릭터와 미션 피드백

- 외부 에셋을 복제하지 않고 Three.js 기본 도형으로 만든 저폴리 클린룸 엔지니어 `FAB ROOKIE`를 사용한다.
- 단계가 바뀌면 캐릭터가 다음 스테이션으로 걸어가고 팔·다리·보행 높이가 실시간으로 애니메이션된다.
- 캐릭터 말풍선은 단계별 핵심 사고 질문을 제시하며 정답을 알려주지 않는다.
- Mission HUD가 현재 Quest, 진행 상태, XP를 React 세션 상태와 동기화한다.

## 개인 API 연결(BYOK)과 향후 운영자 API 전환

무료 파일럿은 학습자가 OpenAI·Google Gemini·Anthropic·DeepSeek 중 하나를 고르고 자신의 API 키로 연결하는 BYOK 방식이다. 제공사와 모델 ID를 선택한 뒤 모델 조회 API로 연결을 확인하고, 확인된 조합에서만 현재 공정 프롬프트를 보낼 수 있다.

- 개인 키는 React 메모리와 해당 요청 안에서만 사용하며 `localStorage`, SQLite, Evidence trail, 보고서, 로그에 저장하지 않는다.
- 새로고침·Coach 단계 이탈·서버 재시작 시 연결 확인 상태가 폐기된다.
- BYOK 엔드포인트는 HTTPS 또는 localhost에서만 열리고, 세션당 연결 확인 5회·문답 15회·IP당 분당 30회·30초 timeout을 적용한다.
- 질문·응답·모델·토큰·문답 단계·사용 키워드는 세션에 저장해 새로고침 후에도 대화 근거를 복원하고 최종 PT에 반영하지만 API 키는 저장하지 않는다.
- 질문 작성기는 선택한 전문용어, 현재 관찰, 단계별 질문 목표, 요구 출력 형식을 한 번에 조합한다. 공정 핵심 키워드가 없는 질문은 전송과 최종 저장을 차단한다.
- AI 응답이 도착하면 대화 팝업이 자동으로 열리고, 누적 질문·응답을 읽으면서 같은 창에서 후속 질문을 최대 15회까지 이어갈 수 있다. 최근 응답 복사와 키보드 `Esc` 닫기도 지원한다.
- 프롬프트와 화면에 공개된 교육용 합성 관찰은 사용자가 선택한 제공사로 전송된다. 실제 회사 Recipe·Spec·로그·개인정보는 입력하지 않는다.
- 개인 키를 쓰지 않으려면 기존처럼 프롬프트를 복사해 외부 AI에서 실행하고 답변을 붙여넣을 수 있다.

유료 서비스 전환 후에는 운영자 전용 키를 서버 `.env`에 저장하고 사용자에게 키 입력을 요구하지 않는 hosted mode로 교체한다. 현재의 `DEEPSEEK_API_KEY` 경로는 이 전환을 위한 서버 전용 fallback이며 브라우저에 노출하지 않는다.

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

## 공개 배포

- 공개 주소: <https://waterfirst.pro/virtual-fab/>
- Nginx가 TLS를 종료하고 로컬 `127.0.0.1:8510`으로 프록시한다.
- BYOK 기능은 반드시 위 HTTPS 주소 또는 localhost에서 사용한다.
- 인증서는 Let's Encrypt/Certbot 자동 갱신 대상으로 등록되어 있다.

## 검증

```bash
.venv/bin/python -m pytest -q tests/test_api.py
npm run build
npx playwright test
```

## 현재 MVP 한계

- 모든 수치와 데이터는 교육용 합성값이다.
- DeepSeek 또는 외부 AI의 답변은 정답이 아니다. 학습자가 출처·측정 원리·데이터와 대조해 직접 검증해야 한다.
- 공개 주소가 HTTPS가 아니면 개인 API 키 입력과 전송은 차단되고 수동 프롬프트 복사만 사용할 수 있다.
- 세션은 SQLite에 저장되어 서버 재시작 후에도 복원된다. 최근 24시간·최대 500개 세션만 유지한다.
- 모든 실행은 `scenario_version + seed`를 저장하고 각 판단에 같은 식별정보와 순번을 남긴다. 같은 seed로 생성한 실행은 같은 입력에서 같은 점수와 판정을 재현한다.
- 완료 후 다른 경로로 재실험하면 seed를 유지해 판단 경로만 비교할 수 있다.
- 만료되거나 유효하지 않은 세션 ID가 남아 있으면 새 세션을 자동 생성하고 처음부터 다시 선택하도록 안내한다.
- 결과는 실제 공정의 인과관계, Recipe 적합성 또는 현장 성과를 입증하지 않는다.
- 실제 기업의 UI·팹 배치·내부 Spec·데이터를 복제하지 않는다.
- 11장 면접 슬라이드는 데이터 다운로드·최근 AI 문답·사용한 공정 키워드·사람의 판단과 SVG 이미지를 내장해 다운로드 후 인터넷 없이 실행된다.
