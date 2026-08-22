"""Build the frozen A/train Model 2 artifact and its reproducibility metadata."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline

from baseline_regression import CONTINUOUS, TARGET, detect_suspected_input_errors
from model_validation import MODEL2, repeated_split
from reference_model import Model2FeatureTransformer, prepare_model_frame

PROJECT = Path(__file__).resolve().parents[1]
INPUT = PROJECT / "data" / "A" / "train.csv"
ARTIFACTS = PROJECT / "artifacts"


def clean_reference() -> pd.DataFrame:
    frame = pd.read_csv(INPUT).drop_duplicates(keep="first").reset_index(drop=True)
    frame = prepare_model_frame(frame)
    return frame[frame[TARGET].notna()].copy()


def pipeline() -> Pipeline:
    return Pipeline([("features", Model2FeatureTransformer()), ("regression", LinearRegression())])


def main() -> None:
    data = clean_reference(); train, validation = repeated_split(data, 42)
    validation_pipeline = pipeline().fit(train, train[TARGET])
    train_prediction = validation_pipeline.predict(train); validation_prediction = validation_pipeline.predict(validation)
    metrics = {
        "artifact_training_source": "projects/01_photo/data/A/train.csv",
        "artifact_fit_rows": int(len(data)), "random_state": 42,
        "features": MODEL2,
        "train_r2": float(r2_score(train[TARGET], train_prediction)),
        "validation_r2": float(r2_score(validation[TARGET], validation_prediction)),
        "validation_rmse_nm": float(mean_squared_error(validation[TARGET], validation_prediction) ** .5),
        "validation_mae_nm": float(mean_absolute_error(validation[TARGET], validation_prediction)),
        "n_train": int(len(train)), "n_validation": int(len(validation)),
    }
    assert round(metrics["validation_r2"], 3) == .679
    assert round(metrics["validation_rmse_nm"], 3) == 1.661
    assert round(metrics["validation_mae_nm"], 3) == 1.140
    final_pipeline = pipeline().fit(data, data[TARGET])
    feature_step = final_pipeline.named_steps["features"].builder_
    regression = final_pipeline.named_steps["regression"]
    parameters = {
        "format_version": 1,
        "feature_names": MODEL2,
        "dose_median": float(feature_step.medians["normalized_dose_pct"]),
        "dose_center": float(feature_step.dose_center),
        "intercept": float(regression.intercept_),
        "coefficients": [float(value) for value in regression.coef_],
        "runtime_note": "Version-stable fallback for sklearn Pipeline artifact loading.",
    }
    ranges = {}
    for column in CONTINUOUS:
        values = pd.to_numeric(data[column], errors="coerce").dropna()
        ranges[column] = {"min": float(values.min()), "max": float(values.max()), "q01": float(values.quantile(.01)), "q99": float(values.quantile(.99)), "median": float(values.median())}
    schema = {
        "contract_version": 1,
        "required_model_columns": ["normalized_dose_pct", "pr_tone", "tool_id"],
        "target_column": TARGET,
        "allowed_pr_tone": ["POSITIVE", "NEGATIVE", "MISSING"],
        "known_tool_id": sorted(data["tool_id_group"].dropna().unique().tolist()),
        "numeric_process_columns": CONTINUOUS,
        "reference_ranges": ranges,
        "range_note": "Observed A/train reference range; not an industry specification.",
        "suspected_input_rows": int(detect_suspected_input_errors(data)["sample_id"].nunique()),
    }
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_pipeline, ARTIFACTS / "model2_pipeline.joblib")
    (ARTIFACTS / "model2_parameters.json").write_text(json.dumps(parameters, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (ARTIFACTS / "reference_metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (ARTIFACTS / "schema_contract.json").write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__": main()
