"""Data-quality, monitoring, failure-case, and DOE evidence helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from baseline_regression import TARGET, clean_category, detect_suspected_input_errors

DOWNSTREAM_OUTCOMES = [
    "spec_pass", "cdu_3sigma_nm", "ler_nm", "scum_probability",
    "pattern_collapse_probability", "defect_probability",
]


@dataclass
class QualityGateResult:
    status: str
    checks: pd.DataFrame
    flagged_rows: pd.DataFrame
    outside_reference: pd.DataFrame


def _clean_categories(frame: pd.DataFrame, column: str) -> pd.Series:
    return clean_category(frame[column]) if column in frame else pd.Series(index=frame.index, dtype="string")


def data_quality_gate(raw: pd.DataFrame, schema: dict) -> QualityGateResult:
    rows = []; blocking = False; warning = False
    required = schema["required_model_columns"]
    missing_required = sorted(set(required).difference(raw.columns))
    if missing_required:
        blocking = True; rows.append(["필수 컬럼", "BLOCK", f"누락: {missing_required}", "Reference Model 입력을 만들 수 없습니다."])
    else: rows.append(["필수 컬럼", "PASS", "모두 존재", "Model 2 입력 계약 충족"])
    invalid_numeric = {}
    for column in schema["numeric_process_columns"]:
        if column not in raw: continue
        source = raw[column]; converted = pd.to_numeric(source, errors="coerce")
        count = int((source.notna() & converted.isna()).sum())
        if count: invalid_numeric[column] = count
    if invalid_numeric:
        warning = True; rows.append(["숫자 datatype", "WARNING", str(invalid_numeric), "일부 값을 숫자로 해석할 수 없어 Train 중앙값 대체 가능성이 있습니다."])
    else: rows.append(["숫자 datatype", "PASS", "변환 실패 0건", "숫자 형식 정상"])
    if "normalized_dose_pct" in raw and pd.to_numeric(raw["normalized_dose_pct"], errors="coerce").notna().sum() == 0:
        blocking = True; rows.append(["Normalized dose", "BLOCK", "유효 숫자 0건", "핵심 연속 입력이 없어 예측할 수 없습니다."])
    tones = set(_clean_categories(raw, "pr_tone")); unknown_tones = sorted(tones.difference(schema["allowed_pr_tone"]))
    if unknown_tones:
        blocking = True; rows.append(["PR tone 허용값", "BLOCK", f"미학습 값: {unknown_tones}", "Positive/Negative/MISSING 외 tone은 안전한 기준 범주로 매핑할 수 없습니다."])
    elif "pr_tone" in raw: rows.append(["PR tone 허용값", "PASS", f"관측: {sorted(tones)}", "Reference 범주 안"])
    tools = set(_clean_categories(raw, "tool_id")); unknown_tools = sorted(tools.difference(schema["known_tool_id"]))
    if unknown_tools:
        warning = True; rows.append(["Tool ID", "WARNING", f"새 Tool: {unknown_tools}", "기존 Tool 효과를 새 Tool에 일반화할 근거가 없습니다."])
    elif "tool_id" in raw: rows.append(["Tool ID", "PASS", f"관측: {sorted(tools)}", "Reference 범주 안"])
    missing_cells = int(raw.isna().sum().sum())
    if missing_cells:
        warning = True; rows.append(["결측", "WARNING", f"{missing_cells:,}셀", "자동 삭제하지 않고 모델 전처리와 결과 해석에 반영합니다."])
    else: rows.append(["결측", "PASS", "0셀", "결측 없음"])
    duplicates = int(raw.duplicated(keep="first").sum())
    if duplicates:
        warning = True; rows.append(["중복", "WARNING", f"추가 중복 {duplicates:,}행", "신규 데이터에서는 자동 삭제하지 않고 생성 경로를 확인합니다."])
    else: rows.append(["중복", "PASS", "0행", "완전 중복 없음"])
    prepared = raw.copy()
    for column in schema["numeric_process_columns"]:
        if column in prepared: prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    flagged = detect_suspected_input_errors(prepared)
    if len(flagged):
        warning = True; rows.append(["입력·단위 오류 후보", "WARNING", f"{flagged.sample_id.nunique()}행", "기존 STEP 2 검토 규칙; 오류 확정이나 자동 삭제 근거가 아닙니다."])
    else: rows.append(["입력·단위 오류 후보", "PASS", "0행", "정의된 검토 후보 없음"])
    outside_rows = []
    for column, bounds in schema["reference_ranges"].items():
        if column not in prepared: continue
        values = pd.to_numeric(prepared[column], errors="coerce")
        for index in prepared.index[(values < bounds["min"]) | (values > bounds["max"])]:
            outside_rows.append({"row_index": index, "sample_id": prepared.at[index, "sample_id"] if "sample_id" in prepared else f"ROW_{index}", "variable": column, "value": values.at[index], "reference_min": bounds["min"], "reference_max": bounds["max"], "basis": "A/train observed range; not industry Spec"})
    outside = pd.DataFrame(outside_rows)
    if len(outside):
        warning = True; rows.append(["Reference 범위", "WARNING", f"{outside.sample_id.nunique()}행 · {outside.variable.nunique()}변수", "A/train 관측 범위 밖이며 외삽 신뢰도가 낮을 수 있습니다."])
    else: rows.append(["Reference 범위", "PASS", "관측 min/max 안", "산업 Spec이 아닌 A/train reference range 기준"])
    status = "BLOCK" if blocking else "WARNING" if warning else "PASS"
    checks = pd.DataFrame(rows, columns=["검사 항목", "판정", "결과", "이유/영향"])
    return QualityGateResult(status, checks, flagged, outside)


def evaluate_reference(bundle, frame: pd.DataFrame) -> tuple[pd.DataFrame, dict | None]:
    result = frame.copy(); prediction = bundle.predict(frame); result["predicted_resist_line_cd_nm"] = prediction
    metrics = None
    if TARGET in result and pd.to_numeric(result[TARGET], errors="coerce").notna().any():
        actual = pd.to_numeric(result[TARGET], errors="coerce"); valid = actual.notna()
        result.loc[valid, "residual_nm"] = actual[valid] - prediction[valid]
        result.loc[valid, "absolute_error_nm"] = result.loc[valid, "residual_nm"].abs()
        metrics = {"r2": float(r2_score(actual[valid], prediction[valid])), "rmse_nm": float(mean_squared_error(actual[valid], prediction[valid]) ** .5), "mae_nm": float(mean_absolute_error(actual[valid], prediction[valid])), "n_evaluated": int(valid.sum())}
    if "nominal_cd_nm" in result:
        nominal = pd.to_numeric(result["nominal_cd_nm"], errors="coerce")
        if TARGET in result: result["cd_deviation_nm"] = pd.to_numeric(result[TARGET], errors="coerce") - nominal
        result["predicted_cd_deviation_nm"] = result["predicted_resist_line_cd_nm"] - nominal
    return result, metrics


def doe_candidates(reference_evidence: dict, available_columns: list[str]) -> pd.DataFrame:
    rows = [{
        "Priority": "P1", "Hypothesis": "PR tone에 따라 관찰된 dose–CD 방향이 다르다.",
        "Evidence": f"Positive/Negative slope {reference_evidence['positive_slope']:+.3f}/{reference_evidence['negative_slope']:+.3f} nm/%p; 반복 방향 {reference_evidence['positive_direction_count']}/30, {reference_evidence['negative_direction_count']}/30",
        "Alternative explanation": "Tool·Lot 배치, 입력 오류, tone별 다른 recipe 구성",
        "Variable to change": "normalized_dose_pct · 수치 수준은 Engineer input required",
        "Variables to hold constant": "PR tone별 분리, Tool block, Focus·coat·Bake·develop 조건",
        "Expected observation": "Positive와 Negative에서 방향 차이가 반복 관찰되는지 확인",
        "What result would reject the hypothesis": "통제 DOE에서 tone별 slope 방향이 재현되지 않거나 불확실구간이 0을 포함",
    }]
    if "focus_um" in available_columns:
        rows.append({"Priority":"P2","Hypothesis":"Focus–CD 관계가 단순 직선보다 비선형일 수 있다.","Evidence":"기존 EDA에서 선형 상관만으로 관계 부재를 확정하지 않음; Model 3 확장이 일관된 Validation 개선을 보이지 않음","Alternative explanation":"Dose·Tool·tone 구성 또는 입력 오류 후보","Variable to change":"focus_um · 수치 수준은 Engineer input required","Variables to hold constant":"Tone, Tool, dose, coat, Bake, develop","Expected observation":"중심 주변 곡률·비대칭 또는 산포 변화 확인","What result would reject the hypothesis":"통제 범위에서 곡률과 산포 차이가 재현되지 않음"})
    if "coat_thickness_nm" in available_columns:
        rows.append({"Priority":"P3","Hypothesis":"Coat thickness가 기준 Model 2에 추가 예측가치를 줄 수 있다.","Evidence":"STEP 5 thickness 확장은 단순 모델 대비 일관된 Validation 개선이 확인되지 않음","Alternative explanation":"Thickness가 Tool·Lot·recipe와 함께 움직이는 교란","Variable to change":"coat_thickness_nm · 수치 수준은 Engineer input required","Variables to hold constant":"Tone, Tool, dose, Focus, Bake, develop","Expected observation":"반복 DOE에서 Model 2 residual과 thickness 수준의 구조적 관계 확인","What result would reject the hypothesis":"반복 조건에서 residual·CD 차이가 재현되지 않음"})
    return pd.DataFrame(rows[:3])
