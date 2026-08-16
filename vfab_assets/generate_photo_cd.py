# -*- coding: utf-8 -*-
"""Virtual Fab 시나리오 1 «사라진 선폭의 비밀» 합성 데이터 생성기.

교육용 합성 데이터다.  실제 회사 Recipe·Spec·현장 데이터가 아니다.

설계 원칙
  1. 평균 CD 는 규격 안에 있다.  평균만 보면 아무 문제가 없다.
  2. Tool 평균 비교는 **오답(PHOTO_C)** 으로 유도한다.  미끼를 심었다.
  3. 진짜 원인은 radius x tool 상호작용에서만 드러난다 (PHOTO_B 의 edge 저하).
  4. 원인은 특정 시점부터 시작한다.  시간축을 봐야 drift 를 본다.
  5. 데이터 품질 함정 4종(결측·단위혼입·중복·Tool편중)을 함께 심는다.

seed 를 바꾸면 원인 Tool·발생시점·크기가 달라져 암기가 불가능하다.
"""
from __future__ import annotations

import argparse, csv, json, math, random
from datetime import datetime, timedelta
from pathlib import Path

TARGET_CD = 45.0          # nm
SPEC_LO, SPEC_HI = 42.0, 48.0
WAFER_R = 150.0           # mm (300mm wafer)
TOOLS = ["PHOTO_A", "PHOTO_B", "PHOTO_C"]


def polar_points() -> list[tuple[float, float]]:
    """center 1점 + 반경 4개 링 x 12점 = 49점."""
    pts = [(0.0, 0.0)]
    for r in (45.0, 85.0, 120.0, 142.0):
        for k in range(12):
            a = 2 * math.pi * k / 12
            pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def build(seed: int) -> tuple[list[dict], dict]:
    rng = random.Random(seed)

    culprit = rng.choice(TOOLS)                     # 진짜 원인 Tool
    decoy = rng.choice([t for t in TOOLS if t != culprit])   # 미끼 Tool
    edge_drop = round(rng.uniform(2.2, 3.4), 2)     # edge CD 저하량 (nm)
    decoy_shift = round(rng.uniform(0.5, 0.9), 2)   # 미끼의 전면 균일 상승 (nm)
    onset_lot = rng.randint(5, 8)                   # drift 시작 Lot 번호
    edge_r = 110.0                                  # 이 반경 밖을 edge 로 본다

    pts = polar_points()
    t0 = datetime(2026, 7, 20, 6, 0)
    rows: list[dict] = []

    for lot_i in range(1, 13):
        lot = f"LOT-{lot_i:03d}"
        tool = TOOLS[(lot_i * 7 + seed) % 3]        # Tool 배정 (편중 유발)
        for waf in range(1, 6):
            slot = waf * 3
            ts = t0 + timedelta(hours=lot_i * 8 + waf)
            for pi, (x, y) in enumerate(pts):
                r = math.hypot(x, y)
                cd = TARGET_CD + rng.gauss(0, 0.55)          # 기본 산포
                cd += -0.004 * r                              # 공통 radial 기울기(약함)
                if tool == decoy:
                    cd += decoy_shift                         # 미끼: 전면 균일 상승
                if tool == culprit and lot_i >= onset_lot and r >= edge_r:
                    cd -= edge_drop + rng.gauss(0, 0.35)      # 진짜 원인: edge 만, 특정 시점부터
                defects = max(0, int(rng.gauss(2, 1.5)))
                if tool == culprit and lot_i >= onset_lot and r >= edge_r:
                    defects += max(0, int(rng.gauss(6, 2.5)))
                rows.append({
                    "lot_id": lot, "wafer_id": f"{lot}-W{waf:02d}", "tool_id": tool,
                    "slot": slot, "point_id": pi,
                    "radius_mm": round(r, 1), "angle_deg": round(math.degrees(math.atan2(y, x)) % 360, 1),
                    "cd_nm": round(cd, 3), "defect_count": defects,
                    "measured_at": ts.strftime("%Y-%m-%d %H:%M:%S"),
                })

    n = len(rows)
    # 함정 1) 결측 — 특정 slot 구간에 집중
    miss_slot = rng.choice([3, 6, 9, 12, 15])
    missing = [i for i, r in enumerate(rows) if r["slot"] == miss_slot and rng.random() < 0.18]
    for i in missing:
        rows[i]["cd_nm"] = ""
    # 함정 2) 단위 혼입 — nm 대신 um
    unit_bad = rng.sample(range(n), int(n * 0.015))
    for i in unit_bad:
        if rows[i]["cd_nm"] != "":
            rows[i]["cd_nm"] = round(float(rows[i]["cd_nm"]) / 1000.0, 6)
    # 함정 3) 중복행
    dup_src = rng.sample(range(n), int(n * 0.01))
    rows.extend([dict(rows[i]) for i in dup_src])
    rng.shuffle(rows)

    # 정답키는 **최종 CSV 기준**으로 재집계한다.  중복 복제가 결측·단위오류 행을
    # 함께 복사하므로 생성 시점 카운트를 그대로 쓰면 채점 정답과 어긋난다.
    final_missing = sum(1 for r in rows if r["cd_nm"] == "")
    final_unit = sum(1 for r in rows if r["cd_nm"] != "" and float(r["cd_nm"]) < 1.0)
    seen: set = set()
    final_dup = 0
    for r in rows:
        k = (r["wafer_id"], r["point_id"], r["measured_at"])
        if k in seen:
            final_dup += 1
        seen.add(k)

    key = {
        "seed": seed,
        "culprit_tool": culprit,
        "decoy_tool": decoy,
        "edge_drop_nm": edge_drop,
        "decoy_uniform_shift_nm": decoy_shift,
        "onset_lot": f"LOT-{onset_lot:03d}",
        "edge_radius_mm": edge_r,
        "traps": {
            "missing_slot": miss_slot,
            "missing_rows": final_missing,
            "unit_error_rows": final_unit,
            "duplicate_rows": final_dup,
        },
        "expected_findings": [
            f"평균 CD 는 규격({SPEC_LO}~{SPEC_HI}nm) 안이다. 평균만으로는 이상이 보이지 않는다.",
            f"Tool 평균만 비교하면 {decoy} 가 가장 높아 원인으로 오인하기 쉽다. 이는 전면 균일 shift 이며 결함과 무관하다.",
            f"진짜 원인은 {culprit} 의 radius>={edge_r}mm edge 영역 CD 저하({edge_drop}nm)다.",
            f"이 현상은 {f'LOT-{onset_lot:03d}'} 부터 시작한다. 시간축을 봐야 drift 를 확인할 수 있다.",
            "결함 증가는 edge 영역에 집중되어 CD 저하와 공간적으로 일치한다.",
        ],
        "notice": "교육용 합성 데이터. 실제 공정·Spec·회사 데이터가 아니다.",
    }
    return rows, key


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260814)
    ap.add_argument("--outdir", default=".")
    a = ap.parse_args()
    rows, key = build(a.seed)
    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
    csv_p = out / f"photo_cd_{a.seed}.csv"
    with csv_p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    key_p = out / f"answer_key_{a.seed}.json"
    key_p.write_text(json.dumps(key, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{csv_p}  {len(rows)}행")
    print(f"{key_p}  원인={key['culprit_tool']} 미끼={key['decoy_tool']} onset={key['onset_lot']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
