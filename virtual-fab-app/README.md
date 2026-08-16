# Virtual Fab · 사라진 선폭의 비밀

React·Three.js·FastAPI와 서버 로컬 Ollama로 만든 첫 번째 반도체 공정 문제해결 시나리오다.

## 학습 흐름

1. 평균 CD가 규격 안이어도 edge 산포를 근거로 Lot 보류 여부를 판단한다.
2. LLM에 경쟁 가설과 반증 증거를 묻고 사람의 검증 계획을 별도로 기록한다.
3. 평균이 아니라 Tool·Lot·위치별 분포와 데이터 품질을 확인한다.
4. 대조군·요인·반복·판정 기준이 있는 실험을 설계한다.
5. 광학·SEM·TEM·EDX·XPS·전기 분석을 비용·시간·정보가치로 선택한다.
6. Holdout 결과로 적용 범위를 결정하고 Evidence trail을 남긴다.
7. 자신의 판단과 한계를 입력해 STAR 기반 독립형 HTML 면접 슬라이드를 내려받는다.

## 단계별 3D 장면

- 문제 발생: edge 결함 웨이퍼
- LLM Coach: Ollama Evidence Mentor 콘솔
- 데이터 판단: 3D wafer map
- 실험계획: Screening DOE matrix
- 분석 툴: Optical CD·SEM·I–V 장비 bay
- 검증: Baseline–Holdout 비교 gate

## 로컬 Ollama

서버 성능을 고려해 `qwen2.5:1.5b`를 사용한다. API는 외부에 공개하지 않고 `127.0.0.1:11434`에서만 수신한다. 검증 가능한 Evidence 프레임은 코드가 제공하고, Ollama 출력은 비판·수정할 초안으로 분리한다. CPU 환경에서 약 40~60초가 걸릴 수 있다.

```bash
ollama pull qwen2.5:1.5b
curl http://127.0.0.1:8510/api/llm/health
```

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
- 질문은 로컬 Ollama가 실제 생성하지만 숨은 원인이나 정답을 전달하지 않으며, 세 가설과 반증 측정은 재현 가능한 코드 프레임으로 분리한다.
- 세션은 FastAPI 프로세스 메모리에 저장되어 서버 재시작 시 초기화된다.
- 결과는 실제 공정의 인과관계, Recipe 적합성 또는 현장 성과를 입증하지 않는다.
- 실제 기업의 UI·팹 배치·내부 Spec·데이터를 복제하지 않는다.
- 면접 슬라이드의 SVG 이미지는 Base64로 내장되어 다운로드 후 인터넷 없이 실행된다.
