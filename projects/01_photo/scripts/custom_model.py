"""Reusable linear-model workbench helpers for the Photo Streamlit app.

This module never reads Holdout data. All imputations, category levels, centers,
and ranges are learned from the supplied training partition only.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from baseline_regression import TARGET, TrainOnlyFeatureBuilder
from model_validation import MODEL2, repeated_split


NUMERIC_INPUTS = [
    "normalized_dose_pct", "focus_um", "coat_thickness_nm", "softbake_temp_c",
    "peb_temp_c", "develop_time_s", "developer_concentration_pct",
]
CATEGORICAL_INPUTS = ["pr_tone", "tool_id"]
ALLOWED_INPUTS = NUMERIC_INPUTS + CATEGORICAL_INPUTS
DEFAULT_INPUTS = ["normalized_dose_pct", "pr_tone", "tool_id"]
FORBIDDEN_CD_INPUTS = {
    "cdu_3sigma_nm", "ler_nm", "scum_probability", "pattern_collapse_probability",
    "defect_probability", "spec_pass", TARGET,
}


def _clean_category(series: pd.Series) -> pd.Series:
    value = series.astype("string").str.strip().str.upper()
    return value.where(value.notna() & value.ne(""), "MISSING")


class CustomFeatureBuilder:
    def __init__(self, inputs: list[str], dose_tone_interaction: bool):
        invalid = set(inputs).difference(ALLOWED_INPUTS)
        if invalid or set(inputs) & FORBIDDEN_CD_INPUTS:
            raise ValueError(f"Disallowed inputs: {sorted(invalid | (set(inputs) & FORBIDDEN_CD_INPUTS))}")
        if not inputs:
            raise ValueError("Select at least one process input")
        self.inputs = list(inputs)
        self.dose_tone_interaction = bool(
            dose_tone_interaction and {"normalized_dose_pct", "pr_tone"}.issubset(inputs)
        )

    def fit(self, train: pd.DataFrame) -> "CustomFeatureBuilder":
        self.numeric = [column for column in self.inputs if column in NUMERIC_INPUTS]
        self.categorical = [column for column in self.inputs if column in CATEGORICAL_INPUTS]
        self.medians = {column: float(pd.to_numeric(train[column], errors="coerce").median()) for column in self.numeric}
        if any(np.isnan(value) for value in self.medians.values()):
            raise ValueError("A selected numeric input has no valid training values")
        self.ranges = {
            column: (
                float(pd.to_numeric(train[column], errors="coerce").min()),
                float(pd.to_numeric(train[column], errors="coerce").max()),
            )
            for column in self.numeric
        }
        self.dose_center = self.medians.get("normalized_dose_pct", 0.0)
        preferred = {
            "pr_tone": ["POSITIVE", "NEGATIVE", "MISSING"],
            "tool_id": ["T01", "T02", "T03", "MISSING"],
        }
        self.levels = {}
        for column in self.categorical:
            observed = list(_clean_category(train[column]).drop_duplicates())
            ordered = [level for level in preferred[column] if level in observed]
            ordered += sorted(set(observed).difference(ordered))
            self.levels[column] = ordered
        self.feature_names = list(self.transform(train).columns)
        return self

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame(index=frame.index)
        for column in self.numeric:
            values = pd.to_numeric(frame[column], errors="coerce").fillna(self.medians[column])
            out["dose_centered" if column == "normalized_dose_pct" else column] = (
                values - self.dose_center if column == "normalized_dose_pct" else values
            )
        category_values = {}
        for column in self.categorical:
            values = _clean_category(frame[column])
            category_values[column] = values
            for level in self.levels[column][1:]:
                out[f"{column}_{level}"] = values.eq(level).astype(float)
        if self.dose_tone_interaction:
            dose = out["dose_centered"]
            for level in self.levels["pr_tone"][1:]:
                out[f"dose_x_pr_tone_{level}"] = dose * category_values["pr_tone"].eq(level).astype(float)
        return out

    def unseen_categories(self, frame: pd.DataFrame) -> dict[str, list[str]]:
        result = {}
        for column in self.categorical:
            unseen = sorted(set(_clean_category(frame[column])).difference(self.levels[column]))
            if unseen:
                result[column] = unseen
        return result


@dataclass
class FittedLinearModel:
    name: str
    target: str
    inputs: list[str]
    interaction: bool
    builder: object
    model: LinearRegression
    metrics: dict[str, float]
    coefficients: pd.DataFrame

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        unseen = self.builder.unseen_categories(frame) if hasattr(self.builder, "unseen_categories") else {}
        if unseen:
            raise ValueError(f"Unseen categories: {unseen}")
        return self.model.predict(self.builder.transform(frame)[self.builder.feature_names])


def _metrics(model: LinearRegression, builder, train: pd.DataFrame, validation: pd.DataFrame, target: str):
    train_prediction = model.predict(builder.transform(train)[builder.feature_names])
    validation_prediction = model.predict(builder.transform(validation)[builder.feature_names])
    return {
        "train_r2": r2_score(train[target], train_prediction),
        "validation_r2": r2_score(validation[target], validation_prediction),
        "validation_rmse_nm": mean_squared_error(validation[target], validation_prediction) ** 0.5,
        "validation_mae_nm": mean_absolute_error(validation[target], validation_prediction),
        "n_train": len(train), "n_validation": len(validation),
    }


def _coefficient_table(model: LinearRegression, names: list[str]) -> pd.DataFrame:
    rows = [{"term": "intercept", "coefficient": float(model.intercept_)}]
    rows.extend({"term": term, "coefficient": float(value)} for term, value in zip(names, model.coef_))
    return pd.DataFrame(rows)


def fit_custom_model(
    data: pd.DataFrame,
    inputs: list[str],
    dose_tone_interaction: bool,
    target: str = TARGET,
    seed: int = 42,
) -> FittedLinearModel:
    frame = data[data[target].notna()].copy()
    train, validation = repeated_split(frame, seed)
    builder = CustomFeatureBuilder(inputs, dose_tone_interaction).fit(train)
    model = LinearRegression().fit(builder.transform(train)[builder.feature_names], train[target])
    return FittedLinearModel(
        "Custom Model", target, list(inputs), builder.dose_tone_interaction, builder, model,
        _metrics(model, builder, train, validation, target),
        _coefficient_table(model, builder.feature_names),
    )


def fit_fixed_model2(data: pd.DataFrame, seed: int = 42) -> FittedLinearModel:
    frame = data[data[TARGET].notna()].copy()
    train, validation = repeated_split(frame, seed)
    legacy_builder = TrainOnlyFeatureBuilder().fit(train)

    class Model2Builder:
        feature_names = MODEL2
        ranges = {
            "normalized_dose_pct": (
                float(pd.to_numeric(train["normalized_dose_pct"], errors="coerce").min()),
                float(pd.to_numeric(train["normalized_dose_pct"], errors="coerce").max()),
            )
        }
        medians = {"normalized_dose_pct": legacy_builder.medians["normalized_dose_pct"]}
        levels = {"pr_tone": ["POSITIVE", "NEGATIVE", "MISSING"], "tool_id": ["T01", "T02", "T03"]}

        @staticmethod
        def transform(part):
            return legacy_builder.transform(part)

        @staticmethod
        def unseen_categories(part):
            result = {}
            for column, suffix in [("pr_tone", "pr_tone_group"), ("tool_id", "tool_id_group")]:
                values = set(part[suffix]) if suffix in part else set(_clean_category(part[column]))
                unseen = sorted(values.difference(Model2Builder.levels[column]))
                if unseen:
                    result[column] = unseen
            return result

    builder = Model2Builder()
    model = LinearRegression().fit(builder.transform(train)[MODEL2], train[TARGET])
    return FittedLinearModel(
        "Model 2", TARGET, ["normalized_dose_pct", "pr_tone", "tool_id"], True,
        builder, model, _metrics(model, builder, train, validation, TARGET),
        _coefficient_table(model, MODEL2),
    )


def explain_term(term: str) -> str:
    if term == "intercept":
        return "모든 기준 범주와 중심값에서의 예측 절편"
    if term == "dose_centered":
        return "다른 조건이 같을 때 normalized dose 1%p 변화와 관련된 예측 CD 변화"
    if term.startswith("dose_x_pr_tone_"):
        return "기준 PR 대비 해당 PR tone의 dose–CD 기울기 차이"
    if term.startswith("tool_id_"):
        return "기준 Tool(T01) 대비 해당 Tool의 조건부 예측 CD 차이"
    if term.startswith("pr_tone_"):
        return "기준 PR(POSITIVE) 대비 중심 dose에서의 조건부 예측 CD 차이"
    return f"다른 선택 조건이 같을 때 {term} 1단위 변화와 관련된 예측 CD 변화"
