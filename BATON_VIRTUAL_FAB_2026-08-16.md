# Virtual Fab 바톤 — 2026-08-16

> 다음 세션은 긴 대화 기록을 다시 읽지 말고 이 문서와 현재 코드만 확인한다.

## 1. 현재 목표

SK하이닉스 취업준비생을 위한 **반도체 공정 불량 해결 RPG**를 개발한다. 절차 암기가 아니라 상황 파악 → 가설 → 데이터 분석 → 측정 도구 선택 → 검증 → 면접용 결과물 생성 과정을 평가한다.

- 공식 SK하이닉스 서비스가 아닌 교육용 합성 팹이다.
- 실제 기업의 팹 배치·Recipe·Spec을 복제하지 않는다.
- 그래픽보다 문제해결 콘텐츠와 판단 로그가 우선이다.

## 2. 실행 위치

- 저장소: `/home/waterfirst/.cokacdir/workspace/syctizfu/semiconductor-ai-hackathon-bootcamp`
- 앱: `virtual-fab-app/`
- 공개 URL: <http://waterfirst.pro:8510/>
- 서비스: `systemctl --user status virtual-fab.service`
- GitHub: <https://github.com/waterfirst/semiconductor-ai-hackathon-bootcamp>

## 3. 현재 구현

- React + TypeScript + React Three Fiber + FastAPI
- 첫 화면 문구:
  - `환영합니다`
  - `SK하이닉스 반도체 팹에 오셨습니다`
  - 교육용 가상 환경임을 같은 화면에서 고지
- 사람형 저폴리 캐릭터:
  - 이동 방향 회전
  - 골반 움직임
  - 팔·다리 교차 보행
  - 손 세정, 마스크, 방진복, 에어샤워 동작
- 입실 절차:
  1. 출입 등록
  2. 손 세정
  3. 마스크 착용
  4. 방진복·장갑 착용
  5. 에어샤워
- 에어샤워 이후 시네마틱:
  - 앞문 닫힘
  - 반대편 출구문 개방
  - 문 너머 클린룸 라인·천장 조명·장비 실루엣 표시
  - 캐릭터와 카메라 슬로모션 이동
  - 청록 광원·입자·원형 파동·화이트 플래시 스플래시
  - `이제, 네가 증명할 차례야.` 표시 후 공정룸 공개
- 공정 시나리오 6종:
  - Photo
  - Dry Etch
  - Sputter
  - CVD
  - CMP
  - Device Characterization

## 4. 마지막 커밋

- `d1973df` — 클린룸 라인과 스플래시 전환
- `6d0d8a3` — 환영 문구
- `5076ef1` — 클린룸 입실 시네마틱
- `5f27229` — 캐릭터 보행·절차 동작
- `b2de289` — 게임형 로비

현재 `main`에 push 완료.

## 5. 검증 상태

- `npm run build` 통과
- Python 테스트 `6 passed`
- 데스크톱 전체 입실 E2E 통과
- 직전 PC·모바일 입실 E2E `2 passed`
- 공개 서버 HTTP 200
- Impeccable UI detector: 경고 0

검증 명령:

```bash
cd virtual-fab-app
npm run build
.venv/bin/python -m pytest -q
npx playwright test tests/e2e.spec.ts -g "open a new dry etch"
systemctl --user restart virtual-fab.service
```

## 6. 수정 핵심 파일

- `virtual-fab-app/src/CleanroomLobby.tsx`
- `virtual-fab-app/src/styles.css`
- `virtual-fab-app/tests/e2e.spec.ts`

## 7. 다음 작업 원칙

1. 사용자의 다음 요청 전에는 기능을 임의로 확장하지 않는다.
2. 외형보다 시나리오·데이터·분기·평가 기준을 우선한다.
3. 캐릭터나 입실 연출 수정 시 PC와 모바일을 함께 확인한다.
4. `prefers-reduced-motion` 사용자는 긴 시네마틱을 건너뛴다.
5. 공개 전 build → pytest → 필요한 E2E → HTTP 200 순으로 검증한다.

## 8. 건드리지 말 것

아래는 현재 저장소에 있지만 이번 가상 팹 UI 작업과 무관한 변경이다. 사용자 지시 없이는 stage·수정·삭제하지 않는다.

- `artifacts/data_quality/cmp_audit_gallery.png`
- `PLAN.md`
- `design-directions/`
- `proposals/preview/`
- `submission/`
- `virtual-fab-mvp/`
