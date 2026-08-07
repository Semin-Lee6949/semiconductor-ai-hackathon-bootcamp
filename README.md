# Semiconductor AI Hackathon Bootcamp

반도체 공정 문제를 **데이터 감사 → 기준모델 → What-if 시뮬레이션 → 의사결정 → GitHub Pages → 3분 발표**로 연결하는 단기 특강 준비 저장소입니다.

> 교육용 합성 데이터만 사용합니다. 특정 회사의 공식 교육과정·실제 공정 조건·기술 노드·내부 Spec을 나타내지 않습니다.

## 운영 구조

- 1차: 2026-08-14, 오프라인 2시간
- 개인 프로젝트: 2026-08-14~20
- 2차: 2026-08-21, 발표·질의응답·피드백 2시간 30분 권장
- 대상: 반도체 소자·R&D 공정·양산기술·설비기술 지원자 약 20명
- 결과물: 개인 저장소, 작동형 MVP, Live Page, AI 활용기록, 3분 발표

## 첫날 성공 기준

수업이 끝날 때 모든 수강생이 다음 다섯 가지를 완료해야 합니다.

1. Starter Repository Fork/Clone 및 첫 Commit
2. `AGENTS.md`·`PLAN.md`에 문제·가설·완료조건 기록
3. 완성 예제 로컬 실행
4. GitHub Pages 초기 URL 생성
5. 배정 과제의 첫 데이터 감사 결과 제출

## 저장소 안내

- [`COURSE_PLAN.md`](COURSE_PLAN.md): 과정 범위·일정·완료 기준
- [`STATUS.md`](STATUS.md): 현재 준비상태와 남은 우선순위
- [`instructor/`](instructor/): 1·2차 진행표, 사전점검
- [`challenges/`](challenges/): 반도체 AI 문제 10종 카탈로그
- [`templates/`](templates/): 계획·AI 기록·발표·평가 양식
- [`demo/`](demo/): CMP 합성 데이터 기반 작동형 시연 예제

## 데모 실행

```bash
cd demo
python -m pip install -r requirements.txt
python src/build_demo.py
python -m http.server 8000 --directory docs
```

브라우저에서 <http://localhost:8000>을 열고 Down Force, 속도, Slurry, Pad Age, Pattern Density를 바꿔 결과가 갱신되는지 확인합니다.

## 보안 원칙

- 실제 Fab 데이터·장비 로그·내부 Spec·고객정보·개인정보를 업로드하지 않습니다.
- API Key·토큰·계정정보를 코드, Prompt, Screenshot, Commit에 남기지 않습니다.
- AI가 생성한 코드와 해석은 테스트·수치·원문 근거로 사람이 검증합니다.
- 상관관계를 인과관계로 표현하지 않습니다.
