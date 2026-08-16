# Virtual Fab · 사라진 선폭의 비밀

React·Three.js·FastAPI로 만든 첫 번째 반도체 공정 문제해결 시나리오다.

## 학습 흐름

1. 평균 CD가 규격 안이어도 edge 산포를 근거로 Lot 보류 여부를 판단한다.
2. LLM에 경쟁 가설과 반증 증거를 묻고 사람의 검증 계획을 별도로 기록한다.
3. 평균이 아니라 Tool·Lot·위치별 분포와 데이터 품질을 확인한다.
4. 대조군·요인·반복·판정 기준이 있는 실험을 설계한다.
5. 광학·SEM·TEM·EDX·XPS·전기 분석을 비용·시간·정보가치로 선택한다.
6. Holdout 결과로 적용 범위를 결정하고 Evidence trail을 남긴다.

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
- LLM 응답을 자동 생성하지 않고, 질문과 사람의 검증 계획을 기록한다.
- 세션은 FastAPI 프로세스 메모리에 저장되어 서버 재시작 시 초기화된다.
- 결과는 실제 공정의 인과관계, Recipe 적합성 또는 현장 성과를 입증하지 않는다.
- 실제 기업의 UI·팹 배치·내부 Spec·데이터를 복제하지 않는다.
