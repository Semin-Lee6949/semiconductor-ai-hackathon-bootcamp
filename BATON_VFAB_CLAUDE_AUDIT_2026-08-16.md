# BATON — Virtual Fab 검수 판정 (Claude → Codex) · 2026-08-16

대상: 배포본 `http://waterfirst.pro:8510` = HEAD `223616f` (API v0.7.0). 실제 세션 플레이 + `backend/main.py` 코드 확인.

## 판정: 요청분은 완료. 단, 출시 불가 결함 3건.

### 완료 확인 (재작업 금지)
- `incident` 블록 API 반영 — 역할·데드라인 60분·관찰3·미확인3·결정 문항 전부 확인
- `signal.bars` CENTER 31 → EDGE 82 단조증가, `risk_from=9`부터 경고선 54 초과 5개. edge 증가 요구 충족
- 단계순서 강제(409)·CSV 미다운로드 차단(422) — 구 "빈 payload +18점" 구멍 폐쇄 확인
- 시나리오 6개, `dataset.csv`/`rewind`/`llm/check` 추가

---

## P0-A. CSV에 진단할 답이 없다 (최우선)

`backend/main.py:447 dataset_rows()`는 **화면 막대그래프를 3회 복제**한다.
`tool_id = f"SIM-{(lot_index % 2) + 1}"` → tool 이 lot 의 함수라 독립 정보가 0 이다.

배포본 42행 실측 집계:
- Tool 평균 SIM-1 `49.354` / SIM-2 `49.386` (차 0.03)
- Lot 평균 `49.357` / `49.386` / `49.350`
- 유일 신호는 zone: CENTER `34.02` → EDGE `68.82`
- 결측 1행, 단위오류 0, 중복 0

→ 학생은 **브리핑이 이미 말하고 그래프가 이미 보여준 사실**을 표로 다시 받는다.
→ 브리핑의 미확인 원인 「설비·위치 편중」은 이 데이터로 **답이 나오지 않는다**.
→ `instructor/answer_keys/answer_key.json` 은 존재하나 `backend/main.py` 가 **한 번도 참조하지 않는다**.

**조치**: `dataset_rows()`를 답이 있는 생성기로 교체.
필수 요소 = 진짜 원인 Tool · **미끼 Tool**(평균이 가장 높지만 원인 아님) · 발생 시작 Lot · 결측/단위/중복 함정.
검증 완료본 `vfab_assets/generate_photo_cd.py` 사용 (seed 20260814: 원인 PHOTO_C, 미끼 PHOTO_B, edge −2.563nm, LOT-005부터 드리프트, 함정 결측99/단위44/중복29).

## P0-B. 채점이 정답 판정이 아니라 선택지 매칭이다

`state.score` 는 데이터셋을 **한 번도 읽지 않는다**.

재현(배포본에서 실제 실행, 100점 획득):
1. `incident/hold`
2. CSV 다운로드만 하고 **열지 않음**
3. `investigation/distribution` + `ai_conversation` 8회를 **클라이언트에서 위조**("CD 관련 질문 N 입니다 아무 내용") + `human_check` 무의미 20자
4. `experiment/screening` `repeats=2`
5. `analysis` tools=`["optical","sem"]`
6. `validation/controlled` `metrics={baseline:1, holdout:999}`
→ **score 100 / verdict "시나리오 해결 · 입력 증거 기준"**

세부 결함:
- `improved = holdout > baseline` — **학생이 입력한 두 숫자끼리 비교**. 자기채점이다
- `ai_conversation` 을 payload 로 받아 그대로 state 저장 → 문답 위조 가능

**조치**: 원인 Tool·영역·onset Lot·미끼 배제 근거를 정답과 대조해 채점.
**미끼를 원인으로 지목하면 0점.** `baseline`/`holdout` 은 서버가 데이터에서 계산한다.

## P0-C. 트레이드오프가 없다

단계별 최고점 선택지가 하나뿐: hold+10 → distribution+30 → screening+18 → coverage+16 → controlled+improved+28 = 102(→100 cap).
예산 80·시간 60 인데 최저가 조합(optical 4/3 + sem 15/10)만으로 coverage 충족 → **61·47 잔여**. 자원 압박이 설계상 발생하지 않는다.

**조치**: 필요 정보영역을 최저가 조합으로 덮을 수 없게 비용·요구영역을 재설계.

## 부수
- 6개 시나리오는 `bars` 숫자와 `required_analysis_kinds` 만 다르고 채점·데이터생성 로직 동일 — **콘텐츠 6개가 아니라 스킨 6개**
- 브리핑 수치(edge 3.2% / 경고선 2.0%)와 `bars`(82 / 54) 축척이 불일치. `signal` 에 단위 명시 필요
- 공유 링크 `?v=981ae4e` 는 20커밋 전. 배포는 `223616f`

---

## 작업 순서 (변경 금지)
1. **P0-A 데이터** → 2. **P0-B 채점 연동** → 3. P0-C 자원설계 → 4. 3D 입체감

## 금지사항
- **P0-A·P0-B 완료 전 3D(카메라·조명·그림자·재질)에 손대지 마라.** 화면이 가리키는 데이터에 답이 없는 상태에서 시각 개선은 「예쁘지만 아무나 100점」을 만든다
- `answer_key` 를 프런트로 내보내지 마라
- 시나리오 수를 더 늘리지 마라. 6개 중 1개를 먼저 진짜로 만든다

## 필수 경로 (2026-08-16 23:38 갱신 — 저장소 안으로 이동 완료)
- `virtual-fab-app/backend/main.py` — 447 `dataset_rows` / 840~945 `apply_decision`
- `vfab_assets/generate_photo_cd.py` — 데이터 생성기. `python3 generate_photo_cd.py` 로 CSV·정답키 동시 산출
- `vfab_assets/INTEGRATION_SPEC.md` — 채점 항목·배점·금지사항 정본
- `vfab_assets/answer_key_20260814.json` — seed 20260814 정답키
- `vfab_assets/photo_cd_20260814.csv` — 고정 fixture. md5 `3d9b9acaff67c29fe0f53cf7cc1d8b13`
- `vfab_assets/UPGRADE_SPEC_v2.md` — 4단계(3D·RPG) 설계. 지금은 열지 마라
- `instructor/answer_keys/answer_key.json` — 기존 파일. 현재 미사용

### 생성기 결정성 확인 (2026-08-16 재실행)
같은 seed 로 재생성한 CSV 가 원본과 **md5 동일**(`3d9b9acaff67c29fe0f53cf7cc1d8b13`, 2,969행).
정답키를 보지 않고 CSV 만으로 재집계한 Tool 평균: PHOTO_A `44.628` / **PHOTO_B `45.310`(미끼·최고값)** / **PHOTO_C `43.483`(진짜 원인)**.
→ 「Tool 평균만 비교하면 미끼를 원인으로 지목한다」는 함정이 실제로 작동한다.
함정 실측: 결측 99행 · 단위오류 44행 · 중복 29행 · onset `LOT-005` · edge `radius>=110.0mm` 에서 `3.13nm` 저하.

## 재현 명령
```bash
B=http://waterfirst.pro:8510
SID=$(curl -s -X POST $B/api/sessions -H 'Content-Type: application/json' -d '{"scenario_id":"photo-cd-drift"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
curl -s $B/api/sessions/$SID/dataset.csv   # tool/lot 평균이 동일한지 확인
```
