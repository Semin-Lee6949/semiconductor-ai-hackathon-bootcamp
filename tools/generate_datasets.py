from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Callable

import numpy as np


BASE_SEED = 20260814
TRAIN_ROWS = 800
HOLDOUT_ROWS = 200
IDENTIFIERS = ["sample_id", "lot_id", "tool_id", "sequence"]


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-np.clip(x, -30, 30)))


def common(rng: np.random.Generator, n: int, holdout: bool, tools: int = 4) -> dict[str, np.ndarray]:
    offset = TRAIN_ROWS if holdout else 0
    probs = np.array([0.50, 0.22, 0.13, 0.09, 0.06][:tools], dtype=float)
    probs /= probs.sum()
    tool_idx = rng.choice(tools, n, p=probs)
    return {
        "sample_id": np.array([f"S{offset+i:05d}" for i in range(n)], dtype=object),
        "lot_id": np.array([f"L{(offset+i)//20:04d}" for i in range(n)], dtype=object),
        "tool_id": np.array([f"T{x+1:02d}" for x in tool_idx], dtype=object),
        "sequence": np.arange(offset, offset + n),
        "_tool": tool_idx,
    }


def photo(rng: np.random.Generator, n: int, v: str, h: bool):
    d = common(rng, n, h, 3)
    negative_share = 0.35 if v == "A" else 0.65
    negative = rng.random(n) < negative_share
    tone = np.where(negative, "NEGATIVE", "POSITIVE")
    retained_source = np.where(negative, "EXPOSED", "UNEXPOSED")
    nominal_dose = np.where(negative, 78.0, 100.0)
    normalized_dose = rng.normal(100 + (2 if h else 0), 6.5, n)
    dose = nominal_dose * normalized_dose / 100
    focus = rng.normal(0.02 if h else 0, 0.075, n)
    pr = rng.normal(115 if v == "B" else 100, 11, n)
    softbake = rng.normal(98, 2.5, n)
    peb = rng.normal(np.where(negative, 105, 110), 2.4, n)
    develop = rng.normal(np.where(negative, 54, 48), 6.0, n)
    developer = rng.normal(2.38, 0.055, n)
    x, y = rng.uniform(-1, 1, (2, n))
    radial = x**2 + y**2
    tool_bias = np.take([-1.3, 0.2, 1.8], d["_tool"])
    dose_delta = normalized_dose - 100
    tone_direction = np.where(negative, 1.0, -1.0)
    tone_cd = tone_direction * 0.27 * dose_delta
    develop_cd = np.where(negative, -0.025, -0.10) * (develop - np.where(negative, 54, 48))
    thickness_cd = 0.024 * (pr - 100)
    if v == "A":
        hidden = 42 * focus**2 + 0.9 * radial + tool_bias + 0.018 * dose_delta * (develop - 50)
        main = "PR tone별 Dose-to-CD 방향과 Positive PR Dose×Develop scum"
        conf = "Coat thickness와 Tool·Field position 편중"
    else:
        hidden = 0.035 * (peb - np.where(negative, 105, 110)) * (pr - 105) + 1.8 * radial + tool_bias * 0.4
        main = "Coat thickness×PEB와 Negative PR crosslink margin"
        conf = "PR tone 비율과 Field radial effect"
    cd = 50 + tone_cd + develop_cd + thickness_cd + hidden + rng.normal(0, 0.8, n)
    cdu = 1.5 + 17 * np.abs(focus) + 0.7 * radial + 0.018 * np.abs(pr - 105) + rng.normal(0, 0.24, n)
    ler = (
        1.15
        + 0.035 * np.abs(dose_delta)
        + 0.045 * (peb - np.where(negative, 105, 110)) ** 2
        + 0.12 * negative
        + rng.normal(0, 0.16, n)
    )
    positive_scum = (~negative) * sigmoid(-1.8 - 0.20 * dose_delta - 0.16 * (develop - 48) + 0.035 * (pr - 100))
    negative_loss = negative * sigmoid(-2.0 - 0.24 * dose_delta - 0.12 * (peb - 105) + 0.025 * (pr - 110))
    scum = np.clip(positive_scum + 0.55 * negative_loss + rng.normal(0, 0.015, n), 0, 1)
    aspect_proxy = pr / np.maximum(cd, 10)
    collapse = np.clip(
        sigmoid(-7 + 1.7 * aspect_proxy + 0.10 * (develop - 50) - 0.45 * negative)
        + rng.normal(0, 0.012, n),
        0,
        1,
    )
    defect = sigmoid(-4 + 0.85 * (cdu - 2.3) + 0.55 * (ler - 1.5) + 2.8 * scum + 2.5 * collapse)
    d.update(
        pr_tone=tone,
        retained_pattern_source=retained_source,
        nominal_cd_nm=np.full(n, 50.0),
        exposure_dose_mj_cm2=dose,
        normalized_dose_pct=normalized_dose,
        focus_um=focus,
        coat_thickness_nm=pr,
        softbake_temp_c=softbake,
        peb_temp_c=peb,
        develop_time_s=develop,
        developer_concentration_pct=developer,
        field_x=x,
        field_y=y,
        resist_line_cd_nm=cd,
        cdu_3sigma_nm=cdu,
        ler_nm=ler,
        scum_probability=scum,
        pattern_collapse_probability=collapse,
        defect_probability=defect,
        spec_pass=np.where(
            (np.abs(cd - 50) < 3)
            & (cdu < 3.2)
            & (scum < 0.25)
            & (collapse < 0.20)
            & (defect < 0.35),
            "PASS",
            "FAIL",
        ),
    )
    targets = [
        "resist_line_cd_nm",
        "cdu_3sigma_nm",
        "ler_nm",
        "scum_probability",
        "pattern_collapse_probability",
        "defect_probability",
        "spec_pass",
    ]
    return d, targets, main, conf, "peb_temp_c"


def overlay(rng: np.random.Generator, n: int, v: str, h: bool):
    d = common(rng, n, h, 4)
    x, y = rng.uniform(-1, 1, (2, n))
    reticle = rng.integers(1, 5, n)
    align = np.clip(rng.normal(0.86, 0.1, n), 0.35, 1)
    temp = rng.normal(22 + (0.5 if h else 0), 0.8, n)
    t = d["sequence"] / 1000
    if v == "A":
        ox = 2.4 + 5.2 * y + 2.1 * x + 1.7 * t + np.take([0, 1.2, -0.8, 2.0], d["_tool"])
        oy = -1.7 - 4.8 * x + 1.6 * y - 0.8 * t
        main, conf = "Rotation·magnification systematic error", "Tool별 translation과 시간 drift"
    else:
        hotspot = ((x > 0.45) & (y < -0.35)).astype(float)
        ox = 1.2 + 2.6 * x + 7.5 * hotspot + 0.9 * reticle
        oy = -0.8 + 2.1 * y - 6.2 * hotspot + 4.5 * (1 - align)
        main, conf = "Local hotspot와 reticle offset", "Align quality와 위치 편중"
    ox += rng.normal(0, 1.2, n)
    oy += rng.normal(0, 1.2, n)
    residual = np.hypot(ox, oy)
    d.update(field_x=x, field_y=y, reticle_id=reticle, align_quality=align, ambient_temp_c=temp,
             overlay_x_nm=ox, overlay_y_nm=oy, residual_nm=residual, spec_pass=np.where(residual < 8, "PASS", "FAIL"))
    return d, ["overlay_x_nm", "overlay_y_nm", "residual_nm", "spec_pass"], main, conf, "ambient_temp_c"


def dry_etch(rng: np.random.Generator, n: int, v: str, h: bool):
    d = common(rng, n, h, 4)
    rf = rng.normal(850, 55, n); bias = rng.normal(190, 22, n); pressure = rng.normal(28, 2.8, n)
    gas = rng.normal(105, 8, n); esc = rng.normal(18, 1.2, n); age = rng.uniform(0, 180, n)
    oes = rng.normal(1.0, 0.08, n); slope = rng.normal(-0.045, 0.012, n)
    if v == "A":
        drift = 0.035 * age + 0.07 * (gas - 105) * (pressure - 28)
        main, conf = "Chamber age×Gas/Pressure drift", "Tool usage imbalance"
    else:
        contam = (d["_tool"] == 2) * (age > 95)
        oes = oes - 0.22 * contam + rng.normal(0, 0.03, n)
        drift = 9 * contam + 26 * (oes - 1) ** 2
        main, conf = "OES contamination-induced endpoint bias", "Age와 특정 chamber 결합"
    endpoint = 62 + 0.035 * (rf - 850) - 28 * slope + drift + rng.normal(0, 2.3, n)
    cd_bias = -1.5 + 0.025 * (bias - 190) + 0.12 * (endpoint - 62) + rng.normal(0, 0.8, n)
    selectivity = 4.3 + 0.018 * (gas - 105) - 0.035 * (bias - 190) + rng.normal(0, 0.3, n)
    risk = sigmoid(-3 + 0.15 * np.maximum(endpoint - 68, 0) + 0.35 * np.abs(cd_bias))
    d.update(oes_peak_ratio=oes, endpoint_slope=slope, rf_source_w=rf, rf_bias_w=bias, pressure_mtorr=pressure,
             gas_flow_sccm=gas, esc_temp_c=esc, chamber_age_runs=age, endpoint_time_s=endpoint,
             cd_bias_nm=cd_bias, selectivity=selectivity, overetch_risk=risk)
    return d, ["endpoint_time_s", "cd_bias_nm", "selectivity", "overetch_risk"], main, conf, "esc_temp_c"


def har_etch(rng: np.random.Generator, n: int, v: str, h: bool):
    d = common(rng, n, h, 3)
    ar = rng.uniform(18, 65, n); density = rng.uniform(0.15, 0.85, n); gas = rng.uniform(0.35, 0.75, n)
    bias = rng.normal(320, 38, n); pressure = rng.normal(19, 2.5, n); time = rng.normal(145, 14, n)
    if v == "A":
        bow = 4 + 0.075 * ar * (bias - 300) / 30 + 9 * (gas - 0.55) ** 2
        main, conf = "Aspect ratio×Bias bowing", "Gas ratio의 비선형 영향"
    else:
        bow = 3 + 15 * density * (pressure - 18) / 6 + 0.045 * ar
        main, conf = "Pattern density×Pressure microloading", "Aspect ratio와 density 편중"
    depth = 1250 + 5.4 * time + 0.9 * bias - 4.2 * ar - 110 * density + rng.normal(0, 35, n)
    top = 74 + rng.normal(0, 1.5, n); bottom = top - 0.11 * ar - 0.45 * bow + rng.normal(0, 1.2, n)
    angle = 90 - np.degrees(np.arctan(np.maximum(top - bottom, 0.1) / np.maximum(depth, 1))) + rng.normal(0, 0.18, n)
    d.update(aspect_ratio=ar, pattern_density=density, gas_ratio=gas, rf_bias_w=bias, pressure_mtorr=pressure,
             etch_time_s=time, etch_depth_nm=depth, top_cd_nm=top, bottom_cd_nm=bottom,
             sidewall_angle_deg=angle, bowing_nm=bow + rng.normal(0, 1.1, n))
    return d, ["etch_depth_nm", "top_cd_nm", "bottom_cd_nm", "sidewall_angle_deg", "bowing_nm"], main, conf, "pressure_mtorr"


def cmp_process(rng: np.random.Generator, n: int, v: str, h: bool):
    d = common(rng, n, h, 4)
    force = rng.uniform(2, 4.5, n); platen = rng.uniform(70, 150, n); head = rng.uniform(65, 145, n)
    slurry = rng.uniform(120, 230, n); age = rng.uniform(0, 140, n); density = rng.uniform(0.2, 0.8, n)
    if v == "A":
        wiwnu = 2.1 + 0.03 * age + 0.00024 * age**2 + 0.6 * np.abs(force - 3.2)
        main, conf = "Pad age의 비선형 WIWNU 악화", "Old pad가 특정 tool에 편중"
    else:
        wiwnu = 2.4 + 8 * density * (slurry - 170) / 100 + 0.7 * np.abs(force - 3.1)
        main, conf = "Pattern density×Slurry interaction", "Product mix와 slurry flow 상관"
    removal = 105 + 45 * force + 0.75 * platen + 0.35 * slurry - 0.22 * age + rng.normal(0, 8, n)
    dishing = 18 + 9 * force + 22 * density - 0.07 * slurry + rng.normal(0, 4, n)
    erosion = 8 + 25 * density + 0.12 * age + rng.normal(0, 3, n)
    yld = np.clip(99 - 1.8 * np.maximum(wiwnu - 3, 0) - 0.18 * np.maximum(dishing - 45, 0) - 0.12 * erosion + rng.normal(0, 1.2, n), 60, 99.8)
    d.update(down_force_psi=force, platen_speed_rpm=platen, head_speed_rpm=head, slurry_flow_ml_min=slurry,
             pad_age_runs=age, pattern_density=density, removal_rate_proxy=removal,
             wiwnu_proxy=wiwnu + rng.normal(0, 0.35, n), dishing_nm=dishing, erosion_nm=erosion, yield_proxy=yld)
    return d, ["removal_rate_proxy", "wiwnu_proxy", "dishing_nm", "erosion_nm", "yield_proxy"], main, conf, "slurry_flow_ml_min"


def deposition(rng: np.random.Generator, n: int, v: str, h: bool):
    d = common(rng, n, h, 5)
    temp = rng.normal(390, 8, n); pressure = rng.normal(2.4, 0.22, n); gas = rng.normal(180, 13, n)
    cycles = rng.integers(80, 141, n); age = rng.uniform(0, 240, n); since = rng.uniform(0, 160, n)
    if v == "A":
        drift = np.take([0, 1.8, -1.0, 3.2, -2.2], d["_tool"]) + 0.018 * age
        main, conf = "Chamber-specific thickness drift", "Chamber age와 생산량 편중"
    else:
        reset = np.where(since < 18, -3.5 * np.exp(-since / 6), 0)
        drift = reset + 0.035 * (temp - 390) * np.maximum(since - 70, 0) / 30
        main, conf = "Maintenance reset과 temperature hysteresis", "Maintenance 직후 표본 부족"
    thickness = 42 + 0.21 * cycles + 0.07 * (temp - 390) + 0.025 * (gas - 180) + drift + rng.normal(0, 1.1, n)
    uniformity = 1.4 + 0.012 * age + 0.5 * np.abs(pressure - 2.4) + rng.normal(0, 0.22, n)
    sheet = 145 - 1.25 * thickness + 0.05 * (temp - 390) + rng.normal(0, 2.2, n)
    correction = np.clip((70 - thickness) / 0.21, -12, 12)
    d.update(temp_c=temp, pressure_torr=pressure, gas_flow_sccm=gas, cycles=cycles,
             chamber_age_runs=age, hours_since_maintenance=since, thickness_nm=thickness,
             uniformity_pct=uniformity, sheet_resistance_proxy=sheet, next_run_cycle_correction=correction)
    return d, ["thickness_nm", "uniformity_pct", "sheet_resistance_proxy", "next_run_cycle_correction"], main, conf, "temp_c"


def fdc(rng: np.random.Generator, n: int, v: str, h: bool):
    d = common(rng, n, h, 4)
    pmean = rng.normal(28, 1.1, n); pstd = np.abs(rng.normal(0.35, 0.12, n)); temp = rng.normal(44, 1.6, n)
    rf = rng.normal(820, 25, n); gas = rng.normal(105, 3, n); motor = rng.normal(12, 0.8, n)
    vib = np.abs(rng.normal(0.8, 0.22, n)); slope = rng.normal(-0.04, 0.009, n); duration = rng.normal(72, 3.5, n)
    label = np.full(n, "NORMAL", dtype=object)
    if v == "A":
        leak = rng.random(n) < 0.055; drift = (d["sequence"] > (900 if h else 610)) & (rng.random(n) < 0.25)
        label[leak] = "LEAK"; label[drift] = "DRIFT"
        pmean += leak * 5 + drift * 2.2; pstd += leak * 0.8; gas -= leak * 8; temp += drift * 3
        main, conf = "Pressure leak와 late-sequence drift", "강한 class imbalance와 시간순 분포차"
    else:
        arc = rng.random(n) < 0.04; bearing = rng.random(n) < 0.06; endpoint = rng.random(n) < 0.05
        label[arc] = "ARC"; label[bearing] = "BEARING"; label[endpoint] = "ENDPOINT"
        rf += arc * rng.normal(120, 20, n); vib += bearing * 1.8; motor += bearing * 3.5; slope += endpoint * 0.055; duration += endpoint * 12
        main, conf = "Arc·bearing·endpoint multi-fault", "희귀 class와 센서 간 상관"
    score = np.clip((np.abs(pmean - 28) / 5 + pstd + np.abs(rf - 820) / 100 + np.maximum(vib - 0.8, 0)) / 4, 0, 1)
    loss = np.clip(2 + 28 * score + rng.normal(0, 2.5, n), 0, 45)
    d.update(pressure_mean=pmean, pressure_std=pstd, temperature_c=temp, rf_power_w=rf, gas_flow_sccm=gas,
             motor_current_a=motor, vibration_rms=vib, endpoint_slope=slope, step_duration_s=duration,
             anomaly_type=label, anomaly_score=score, yield_loss_proxy=loss)
    return d, ["anomaly_type", "anomaly_score", "yield_loss_proxy"], main, conf, "temperature_c"


def dram(rng: np.random.Generator, n: int, v: str, h: bool):
    d = common(rng, n, h, 4)
    cd = rng.normal(42, 2.4, n); eot = rng.normal(1.15, 0.08, n); dose = rng.normal(1.0, 0.07, n)
    anneal = rng.normal(920, 14, n); contact = rng.normal(82, 9, n)
    if v == "A":
        hidden = 0.11 * (cd - 42) * (eot - 1.15) + np.take([0, 0.025, -0.018, 0.04], d["_tool"])
        main, conf = "Gate CD×EOT interaction", "Tool offset와 CD sampling bias"
    else:
        hidden = 0.0015 * (contact - 82) * (anneal - 920) + 0.035 * (d["_tool"] == 3)
        main, conf = "Contact resistance×Anneal interaction", "Anneal과 tool assignment 편중"
    vth = 0.52 + 0.012 * (cd - 42) + 0.28 * (eot - 1.15) + 0.35 * (dose - 1) + hidden + rng.normal(0, 0.018, n)
    ion = 1.2 - 0.032 * (cd - 42) - 0.004 * (contact - 82) + 0.002 * (anneal - 920) + rng.normal(0, 0.045, n)
    ioff = np.exp(-7 + 3.2 * (0.52 - vth) + rng.normal(0, 0.25, n))
    retention = sigmoid(-4 + 7 * np.abs(vth - 0.52) + 0.035 * np.maximum(contact - 88, 0))
    yld = np.clip(100 * (1 - retention) - 7 * np.maximum(0.9 - ion, 0) + rng.normal(0, 1, n), 50, 99.8)
    d.update(gate_cd_nm=cd, eot_nm=eot, channel_dose_proxy=dose, anneal_temp_c=anneal,
             contact_resistance_proxy=contact, vth_v=vth, ion_proxy=ion, ioff_proxy=ioff,
             retention_risk=retention, spec_yield_pct=yld)
    return d, ["vth_v", "ion_proxy", "ioff_proxy", "retention_risk", "spec_yield_pct"], main, conf, "anneal_temp_c"


def nand(rng: np.random.Generator, n: int, v: str, h: bool):
    d = common(rng, n, h, 3)
    layer = rng.integers(1, 193, n); cycles = np.exp(rng.uniform(np.log(10), np.log(5000), n))
    pulse = rng.normal(18, 1.3, n); temp = rng.normal(45 + (5 if h else 0), 9, n)
    retention = np.exp(rng.uniform(np.log(1), np.log(1000), n)); state = rng.integers(0, 8, n)
    if v == "A":
        wear = 0.16 * np.log1p(cycles) + 0.00011 * cycles
        main, conf = "P/E cycle의 비선형 wear", "Log-scale sampling과 state imbalance"
    else:
        wear = 0.12 * np.log1p(retention) * np.exp((temp - 45) / 55) + 0.0015 * np.abs(layer - 96)
        main, conf = "Retention time×temperature×layer", "Holdout의 고온 분포 이동"
    vmean = -1.2 + 0.72 * state + 0.045 * (pulse - 18) - wear + rng.normal(0, 0.09, n)
    vsigma = 0.18 + 0.028 * np.log1p(cycles) + 0.0007 * np.abs(layer - 96) + rng.normal(0, 0.025, n)
    window = np.clip(0.72 - 1.8 * vsigma - 0.12 * wear + rng.normal(0, 0.04, n), 0.03, 0.9)
    ber = sigmoid(-7 + 11 * (0.35 - window) + 0.35 * state)
    d.update(layer=layer, pe_cycle=cycles, program_pulse_v=pulse, temperature_c=temp,
             retention_time_h=retention, state=state, vth_mean_v=vmean, vth_sigma_v=vsigma,
             read_window_v=window, ber_proxy=ber, read_error=np.where(ber > 0.12, "HIGH", "LOW"))
    return d, ["vth_mean_v", "vth_sigma_v", "read_window_v", "ber_proxy", "read_error"], main, conf, "temperature_c"


def virtual_lot(rng: np.random.Generator, n: int, v: str, h: bool):
    d = common(rng, n, h, 5)
    photo = rng.normal(50, 2.1, n); overlay = np.abs(rng.normal(4.5, 1.8, n)); etch_bias = rng.normal(-1.5, 1.2, n)
    depth = rng.normal(980, 45, n); dishing = np.abs(rng.normal(38, 12, n)); film = rng.normal(68, 3.5, n)
    if v == "A":
        interaction = 0.12 * (photo - 50) * (etch_bias + 1.5) + 0.002 * (depth - 980)
        main, conf = "Photo CD→Etch bias interaction", "상류 CD와 etch tool assignment 편중"
    else:
        interaction = 0.045 * dishing * overlay + np.take([0, 0.8, -0.5, 1.4, -1.0], d["_tool"])
        main, conf = "Overlay×CMP dishing risk propagation", "Tool-chain offset와 product mix"
    final_cd = photo + etch_bias + interaction + rng.normal(0, 0.7, n)
    resistance = 100 + 2.1 * (50 - final_cd) + 0.18 * (68 - film) + 0.035 * dishing + rng.normal(0, 1.7, n)
    risk = sigmoid(-5 + 0.45 * overlay + 0.055 * dishing + 0.8 * np.abs(final_cd - 48.5))
    fail = np.where(rng.random(n) < risk, "FAIL", "PASS")
    yld = np.clip(99 - 32 * risk + rng.normal(0, 1.5, n), 45, 99.7)
    d.update(photo_cd_nm=photo, overlay_nm=overlay, etch_bias_nm=etch_bias, etch_depth_nm=depth,
             cmp_dishing_nm=dishing, film_thickness_nm=film, final_cd_nm=final_cd,
             resistance_proxy=resistance, defect_risk=risk, electrical_result=fail, yield_proxy=yld)
    return d, ["final_cd_nm", "resistance_proxy", "defect_risk", "electrical_result", "yield_proxy"], main, conf, "film_thickness_nm"


GENERATORS: list[tuple[str, str, Callable]] = [
    ("01_photo", "Photo PR Coat-Expose-Develop CD Window", photo),
    ("02_overlay", "Overlay Systematic Error", overlay),
    ("03_dry_etch", "Dry Etch Endpoint", dry_etch),
    ("04_har_etch", "HAR Etch Profile", har_etch),
    ("05_cmp", "CMP Multi-objective Optimization", cmp_process),
    ("06_deposition_apc", "Deposition Run-to-Run APC", deposition),
    ("07_fdc", "Equipment FDC", fdc),
    ("08_dram", "DRAM Cell Transistor", dram),
    ("09_nand", "3D NAND Vth Window", nand),
    ("10_virtual_lot", "Photo-Etch-CMP Virtual Lot", virtual_lot),
]


def to_rows(data: dict[str, np.ndarray], targets: list[str]) -> list[dict[str, object]]:
    keys = [k for k in data if not k.startswith("_")]
    rows = []
    for i in range(len(data["sample_id"])):
        row = {}
        for key in keys:
            value = data[key][i]
            if isinstance(value, (np.floating, float)):
                value = round(float(value), 6)
            elif isinstance(value, (np.integer, int)):
                value = int(value)
            else:
                value = str(value)
            row[key] = value
        rows.append(row)
    return rows


def corrupt_train(rows: list[dict[str, object]], targets: list[str], unit_col: str, rng: np.random.Generator, variant: str):
    features = [k for k in rows[0] if k not in IDENTIFIERS + targets]
    missing_rate = 0.012 if variant == "A" else 0.02
    for row in rows:
        for key in features:
            if rng.random() < missing_rate:
                row[key] = ""
    numeric_features = [k for k in features if any(isinstance(row[k], (int, float)) for row in rows)]
    for _ in range(max(4, int(len(rows) * 0.012))):
        row = rows[int(rng.integers(0, len(rows)))]
        key = str(rng.choice(numeric_features))
        if isinstance(row[key], (int, float)):
            row[key] = round(float(row[key]) * float(rng.choice([0.1, 5, 10])), 6)
    for idx in rng.choice(len(rows), max(3, int(len(rows) * 0.006)), replace=False):
        if isinstance(rows[int(idx)].get(unit_col), (int, float)):
            value = float(rows[int(idx)][unit_col])
            rows[int(idx)][unit_col] = round(value + 273.15 if "temp" in unit_col else value * 10, 6)
    for target in targets:
        clean = [row[target] for row in rows if row[target] != ""]
        indices = rng.choice(len(rows), max(2, int(len(rows) * 0.004)), replace=False)
        if clean and isinstance(clean[0], (int, float)):
            scale = float(np.std(clean)) or 1.0
            for idx in indices:
                rows[int(idx)][target] = round(float(rows[int(idx)][target]) + float(rng.normal(0, 3 * scale)), 6)
        else:
            labels = sorted(set(map(str, clean)))
            if len(labels) > 1:
                for idx in indices:
                    current = str(rows[int(idx)][target])
                    rows[int(idx)][target] = str(rng.choice([label for label in labels if label != current]))
    for _ in range(max(4, int(len(rows) * 0.007))):
        rows.append(dict(rows[int(rng.integers(0, len(rows)))]))
    rng.shuffle(rows)


def corrupt_holdout(rows: list[dict[str, object]], targets: list[str], rng: np.random.Generator):
    features = [k for k in rows[0] if k not in IDENTIFIERS + targets]
    for row in rows:
        for key in features:
            if rng.random() < 0.006:
                row[key] = ""


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fields} for row in rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(root: Path, train_rows: int = TRAIN_ROWS, holdout_rows: int = HOLDOUT_ROWS) -> dict[str, object]:
    manifest: dict[str, object] = {
        "version": 1,
        "base_seed": BASE_SEED,
        "educational_synthetic_only": True,
        "student_packs": 20,
        "files": [],
    }
    answers: dict[str, object] = {}
    schema: dict[str, object] = {}
    for ci, (slug, title, generator) in enumerate(GENERATORS, start=1):
        schema[slug] = {"title": title, "variants": {}}
        for vi, variant in enumerate(("A", "B")):
            seed = BASE_SEED + ci * 100 + vi * 10
            train_rng = np.random.default_rng(seed)
            holdout_rng = np.random.default_rng(seed + 1)
            train_data, targets, main, conf, unit_col = generator(train_rng, train_rows, variant, False)
            holdout_data, holdout_targets, _, _, _ = generator(holdout_rng, holdout_rows, variant, True)
            assert targets == holdout_targets
            train = to_rows(train_data, targets)
            holdout_full = to_rows(holdout_data, targets)
            corrupt_train(train, targets, unit_col, train_rng, variant)
            corrupt_holdout(holdout_full, targets, holdout_rng)
            train_fields = list(train[0])
            feature_fields = [k for k in train_fields if k not in targets]
            label_fields = ["sample_id", *targets]
            student_dir = root / "datasets/student" / slug / variant
            answer_dir = root / "instructor/answer_keys" / slug / variant
            paths = [
                (student_dir / "train.csv", train, train_fields, "student_train"),
                (student_dir / "holdout_features.csv", holdout_full, feature_fields, "student_holdout"),
                (answer_dir / "holdout_labels.csv", holdout_full, label_fields, "instructor_labels"),
            ]
            for path, rows, fields, kind in paths:
                write_csv(path, rows, fields)
                manifest["files"].append({
                    "path": str(path.relative_to(root)), "kind": kind, "rows": len(rows), "sha256": sha256(path)
                })
            key = f"{slug}_{variant}"
            answers[key] = {
                "title": title,
                "variant": variant,
                "seed": seed,
                "targets": targets,
                "main_signal": main,
                "confounder_or_trap": conf,
                "injected_quality_issues": [
                    "Gaussian measurement noise", "missing feature values", "exact duplicate rows in train",
                    "extreme numeric outliers", "small target-label corruption", f"mixed-unit fault in {unit_col}", "tool/lot imbalance",
                    "holdout time or covariate shift",
                ],
                "safe_conclusion": "합성 데이터 범위의 예측·진단 근거만 제시하고 실제 공정 인과나 Recipe로 일반화하지 않는다.",
            }
            schema[slug]["variants"][variant] = {
                "student_train_rows": len(train), "holdout_rows": len(holdout_full),
                "features": [k for k in feature_fields if k not in IDENTIFIERS], "targets": targets,
            }
    manifest_path = root / "datasets/manifest.json"
    schema_path = root / "datasets/schema.json"
    answer_path = root / "instructor/answer_keys/answer_key.json"
    for path, payload in ((manifest_path, manifest), (schema_path, schema), (answer_path, answers)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate noisy educational semiconductor AI datasets")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--train-rows", type=int, default=TRAIN_ROWS)
    parser.add_argument("--holdout-rows", type=int, default=HOLDOUT_ROWS)
    args = parser.parse_args()
    result = generate(args.root.resolve(), args.train_rows, args.holdout_rows)
    print(json.dumps({"status": "ok", "student_packs": result["student_packs"], "files": len(result["files"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
