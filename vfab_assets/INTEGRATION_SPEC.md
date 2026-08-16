# P0-1 데이터셋 연동 규격 — Codex 인계

작성 2026-08-14 · Claude(레드팀) → Codex(구현)
대상: `virtual-fab-app` 시나리오 1 «사라진 선폭의 비밀»

이 폴더는 **레드팀 지시서 P0-1(데이터 부재)** 를 해소하기 위한 완성 산출물이다.
백엔드·프론트 코드는 건드리지 않았다. 파일만 가져다 붙이면 된다.

## 동봉물

| 파일 | 용도 |
|---|---|
| `generate_photo_cd.py` | 데이터 생성기. `--seed` 로 정답 랜덤화 |
| `photo_cd_20260814.csv` | 샘플 데이터 2,969행 |
| `answer_key_20260814.json` | 채점용 정답키 (학생에게 노출 금지) |

```bash
python3 generate_photo_cd.py --seed <세션시드> --outdir data/
```

## 데이터 스키마

`lot_id, wafer_id, tool_id, slot, point_id, radius_mm, angle_deg, cd_nm, defect_count, measured_at`

- 12 Lot × 5 Wafer × 49 측정점 (center 1 + 반경 45/85/120/142mm 링 각 12점)
- 목표 CD 45.0nm, 규격 42.0~48.0nm, 300mm wafer

## 심어둔 함정 — 검증 완료

seed 20260814 실측값이다.

**① 평균만 보면 정상이다**
전체 평균 **44.474nm** — 규격 한가운데. 평균 확인만으로는 아무 문제가 없다.

**② Tool 평균 비교는 오답으로 유도된다**

| Tool | 평균 CD |
|---|---|
| PHOTO_A | 44.628 |
| **PHOTO_B** | **45.310** ← 최고. 원인으로 오인하기 쉽다 |
| PHOTO_C | 43.483 |

Tool 평균 1위는 `PHOTO_B`(미끼)지만 **진짜 원인은 `PHOTO_C`** 다.
미끼는 전면 균일 shift라 결함과 무관하다. **이 함정이 P0-2(변별력) 요구를 충족시킨다.**

**③ radius × tool 로 쪼개야 진실이 보인다**

| Tool | center | edge | 차이 |
|---|---|---|---|
| PHOTO_A | 44.757 | 44.494 | −0.262 |
| PHOTO_B | 45.439 | 45.174 | −0.265 |
| **PHOTO_C** | 44.745 | **42.182** | **−2.563** |

**④ 시간축을 봐야 drift 를 안다**
`PHOTO_C` edge: onset 이전 44.507 → 이후 **41.405nm**. `LOT-005` 부터 시작한다.

**⑤ 데이터 품질 함정**
결측 99행(특정 slot 집중) · 단위혼입 44행(µm) · 중복 29행

## 채점 연동 요구

**선택지 클릭이 아니라 학생이 도달한 결론으로 채점하라.** 현재 `apply_decision` 의
`distribution`/`mean_only` 이분 선택을 아래로 교체한다.

| 문항 | 입력 | 정답 | 배점 |
|---|---|---|---|
| 원인 Tool 지목 | Tool 선택 | `answer_key.culprit_tool` | 25 |
| 이상 발생 영역 | center / edge / 전면 | edge (radius ≥ `edge_radius_mm`) | 15 |
| drift 시작 Lot | Lot 선택 | `answer_key.onset_lot` ±1 Lot | 15 |
| 결측 행 수 | 정수 입력 | `traps.missing_rows` ±5% | 10 |
| 단위오류 행 수 | 정수 입력 | `traps.unit_error_rows` ±5% | 10 |
| 중복 행 수 | 정수 입력 | `traps.duplicate_rows` ±5% | 10 |
| 미끼 배제 근거 | 서술 | `decoy_tool` 언급 + "균일/전면/결함무관" 키워드 | 15 |

**미끼 Tool 을 원인으로 지목하면 0점 처리한다.** 부분점수를 주면 함정이 무력화된다.

## 필수 UI (P0-1 요구)

1. **CSV 다운로드 버튼** — 학생이 Python·Excel 로 직접 분석할 수 있어야 한다
2. **그룹핑 축 선택** — Tool / Lot / radius bin / slot / 시간
3. **집계 방식 선택** — mean / median / std / p95 / count
4. **시각화 3종** — wafer map(산점, 색=CD), 박스플롯(그룹별), 시계열(Lot 순)

`radius_mm` 를 bin 으로 묶는 기능이 없으면 학생이 edge 효과를 발견할 수 없다. **필수다.**

## 금지

- `answer_key_*.json` 을 프론트로 내려보내지 마라. 서버 채점 전용이다.
- CSV 에 정답 컬럼(`is_culprit` 등)을 추가하지 마라.
- 함정 비율(결측 18%/단위 1.5%/중복 1%)을 낮추지 마라. 낮추면 데이터 품질 검증이 무의미해진다.

## 검수

```bash
# 생성기가 매 seed 마다 다른 정답을 내는지
for s in 1001 2002 3003; do python3 generate_photo_cd.py --seed $s --outdir /tmp/vfk; done
# -> culprit_tool / onset_lot / edge_drop_nm 이 모두 달라야 한다 (확인 완료)

# 정답키가 최종 CSV 와 일치하는지
# -> 결측·단위·중복 카운트 3종 일치 (확인 완료)
```

레드팀 검수 기준 #1 「데이터 없이는 못 푼다」와 #4 「암기가 안 된다」를 이 데이터로 충족한다.

교육용 합성 데이터다. 실제 공정·Spec·회사 데이터가 아니다.
