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
- 공개 URL: <https://waterfirst.pro/virtual-fab/>
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
- 시나리오별 전문용어 6개:
  - 용어 뜻과 현재 문제·데이터와의 관련성을 함께 표시
  - 질문마다 최소 1개 공정 키워드 포함을 프론트엔드와 API에서 검증
  - 공식 장비·공정 자료 링크 제공
- 제한된 AI 문답 15회 운영 전략:
  - 최소 8회 완료 필수, 최대 15회
  - 1–2회 용어·CSV 데이터 이해
  - 3–4회 경쟁 가설·예상 분포
  - 5–6회 반증·누락 점검
  - 7–8회 판단·PT 구조 압축
  - 9–15회 반론·한계·면접 질문 선택 심화
- 질문 작성기:
  - 선택 키워드 + 현재 관찰 + 단계 목표 + 출력 형식을 구조화 프롬프트로 조합
  - 질문·응답·모델·토큰·문답 단계·키워드를 세션에 보존
  - Evidence trail과 동적 HTML PT에 문답 단계와 공정 키워드 맵 반영
- AI 문답 팝업:
  - 응답 수신 즉시 자동 표시
  - 누적 문답·모델·토큰·키워드 확인
  - 팝업 안에서 다음 질문을 수정하고 최대 15회까지 연속 전송
  - 최근 응답 복사, 바깥 클릭·닫기 버튼·`Esc` 닫기, 모바일 전체 화면 대응
  - Gemini 응답·사고·전체 토큰 분리 표시
  - Gemini 출력 8,192 tokens; 짧은 `MAX_TOKENS` 응답은 16,384로 1회 자동 재시도
  - 요청 실패 시 제공사 상세 오류와 같은 질문 재시도 버튼을 팝업 안에 표시
  - Gemini 503 일시 과부하는 1초·2초 간격으로 최대 2회 자동 재시도
- CSV 기반 AI 분석:
  - 사용자의 PC 로컬 경로를 Gemini가 열도록 요구하지 않음
  - 다운로드한 파일과 같은 scenario version·seed의 CSV 원문 42행을 서버가 AI 요청에 직접 첨부
  - 행 수·결측·영역별·Tool별 통계 요약과 원본 행을 함께 전달
  - 다운로드 완료 영역에 `AI 질문에 동일 CSV 42행 자동 첨부` 상태 표시
  - 수강자에게 `AI 데이터 자동 연결됨` 상태와 현재 세션의 서버 CSV 경로를 표시
  - 브라우저가 PC Downloads 경로를 임의로 읽을 수 없다는 점과 로컬 경로 입력이 불필요함을 안내
  - 모든 자동 질문 초안에 서버 CSV 원문·통계 자동 첨부 사실을 명시
  - Step 1 주 버튼은 파일 다운로드가 아니라 `서버 CSV 불러오기·미리보기`
  - 화면 안에서 전체 42행 × 9열을 고정 헤더·가로/세로 스크롤 표로 확인
  - 파일이 필요한 수강자만 미리보기 헤더의 `CSV 파일로 저장` 보조 버튼 사용
- 심층 PT 생성:
  - 합성 CSV 42행의 결측·CENTER/MIDDLE/EDGE·Tool별 통계를 직접 계산해 삽입
  - 전체 질문·응답을 2회당 한 장으로 생성해 마지막 5회만 남던 문제 해결
  - 8회 문답은 15장, 15회 문답은 19장으로 자동 확장
  - 모델·누적 토큰·사용 키워드·사람의 검증 판단을 별도 요약
- 상단 Step 복귀:
  - 완료한 Step은 `돌아가기` 버튼으로 표시하고 클릭 시 해당 단계부터 다시 판단
  - 해당 단계 이후 판단·Evidence·점수·예산·시간은 서버에서 재계산해 롤백
  - 이미 내려받은 합성 데이터와 AI 문답·호출 횟수는 보존해 비용·횟수 우회를 차단
  - 현재 단계와 미래 단계는 비활성화

## 4. 마지막 커밋

- 최신 작업 — Step 1을 서버 CSV 42행 미리보기 중심으로 전환하고 파일 저장을 보조 기능으로 분리
- 최신 작업 — 수강자용 서버 CSV 경로·자동 연결 상태 안내와 질문 초안 데이터 출처 명시
- 최신 작업 — Gemini 요청에 합성 CSV 원문 42행 자동 첨부 및 503 자동 재시도
- 최신 작업 — 상단 완료 Step 클릭으로 이전 단계 복귀 및 이후 판단 서버 롤백
- 최신 작업 — 최소 8회 데이터 기반 심층 토론과 전체 문답·CSV 통계 동적 PT 반영
- 최신 작업 — Gemini 등 개인 AI 응답 자동 팝업과 연속 후속 질문 UI
- `cbfc7c1` — 데이터 판단과 최대 15회 AI 코치 문답 통합, 최종 PT 다운로드 복구
- `e57aa0b` — OpenAI·Gemini·Anthropic·DeepSeek 개인 API 연결(BYOK), 연결 확인, 프롬프트 분석
- `2174252` — 데스크톱 캐릭터·좌측 카드 겹침 해소와 상단 단계 글자 확대
- `91a7852` — 시나리오 seed·버전 기반 재현성과 세션 복원 강화
- `d1973df` — 클린룸 라인과 스플래시 전환
- `6d0d8a3` — 환영 문구
- `5076ef1` — 클린룸 입실 시네마틱
- `5f27229` — 캐릭터 보행·절차 동작
- `b2de289` — 게임형 로비

현재 `main`에 push 완료.

## 5. 검증 상태

- `npm run build` 통과
- Python 테스트 `20 passed`
- 전체 desktop 시나리오 E2E `1 passed`
- 상단 Step 복귀 desktop E2E `1 passed`
- 데스크톱·모바일 전체 E2E `6 passed`
- 공개 HTTPS 서버와 `/api/health` HTTP/2 200
- 공개 주소에서 공정 키워드 6개·문답 전략 5단계·구조화 질문 초안·콘솔 오류 0건 확인
- Let's Encrypt 인증서 자동 갱신 설정(현재 만료일 2026-11-14)
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
- `virtual-fab-app/src/App.tsx`
- `virtual-fab-app/src/components/EvidenceDrawer.tsx`
- `virtual-fab-app/src/components/PersonalAIConnector.tsx`
- `virtual-fab-app/src/types.ts`
- `virtual-fab-app/src/styles.css`
- `virtual-fab-app/backend/main.py`
- `virtual-fab-app/tests/test_api.py`
- `virtual-fab-app/tests/e2e.spec.ts`

## 7. 다음 작업 원칙

1. 사용자의 다음 요청 전에는 기능을 임의로 확장하지 않는다.
2. 외형보다 시나리오·데이터·분기·평가 기준을 우선한다.
3. 캐릭터나 입실 연출 수정 시 PC와 모바일을 함께 확인한다.
4. `prefers-reduced-motion` 사용자는 긴 시네마틱을 건너뛴다.
5. 공개 전 build → pytest → 필요한 E2E → HTTPS·API health·브라우저 콘솔 순으로 검증한다.

## 8. 건드리지 말 것

아래는 현재 저장소에 있지만 이번 가상 팹 UI 작업과 무관한 변경이다. 사용자 지시 없이는 stage·수정·삭제하지 않는다.

- `artifacts/data_quality/cmp_audit_gallery.png`
- `PLAN.md`
- `design-directions/`
- `proposals/preview/`
- `submission/`
- `virtual-fab-mvp/`
