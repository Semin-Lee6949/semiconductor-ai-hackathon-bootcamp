"""Fixed Model 2 reference artifact helpers.

The serialized Pipeline is trained only by train_reference_model.py on A/train.
Uploaded data is evaluated or scored with the frozen artifact; it is never fit here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline

from baseline_regression import CONTINUOUS, TARGET, TrainOnlyFeatureBuilder, clean_category
from model_validation import MODEL2


class Model2FeatureTransformer(BaseEstimator, TransformerMixin):
    """Sklearn-compatible wrapper around the validated train-only builder."""

    def fit(self, x, y=None):
        frame = prepare_model_frame(x)
        self.builder_ = TrainOnlyFeatureBuilder().fit(frame)
        self.feature_names_out_ = list(MODEL2)
        return self

    def transform(self, x):
        frame = prepare_model_frame(x)
        return self.builder_.transform(frame)[MODEL2]

    def get_feature_names_out(self, input_features=None):
        return np.asarray(self.feature_names_out_, dtype=object)


def prepare_model_frame(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if "pr_tone_group" not in result and "pr_tone" in result:
        result["pr_tone_group"] = clean_category(result["pr_tone"])
    if "tool_id_group" not in result and "tool_id" in result:
        result["tool_id_group"] = clean_category(result["tool_id"])
    for column in CONTINUOUS:
        if column not in result: result[column] = np.nan
        result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


@dataclass
class ReferenceBundle:
    pipeline: Pipeline | None
    metrics: dict
    schema: dict
    parameters: dict

    name: str = "Reference Model 2"
    target: str = TARGET
    inputs: tuple = ("normalized_dose_pct", "pr_tone", "tool_id")
    interaction: bool = True

    @property
    def coefficients(self) -> pd.DataFrame:
        return pd.DataFrame({"term": ["intercept", *MODEL2], "coefficient": [self.parameters["intercept"], *self.parameters["coefficients"]]})

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        if self.pipeline is not None: return self.pipeline.predict(frame)
        features = frozen_model2_features(frame, self.parameters)
        return self.parameters["intercept"] + features.to_numpy() @ np.asarray(self.parameters["coefficients"])

    @property
    def builder(self):
        bundle = self
        class ArtifactBuilder:
            feature_names = list(MODEL2)
            ranges = {column: (values["min"], values["max"]) for column, values in bundle.schema["reference_ranges"].items()}
            medians = {column: values["median"] for column, values in bundle.schema["reference_ranges"].items()}
            levels = {"pr_tone": bundle.schema["allowed_pr_tone"], "tool_id": bundle.schema["known_tool_id"]}
            @staticmethod
            def transform(frame):
                if bundle.pipeline is not None: return bundle.pipeline.named_steps["features"].transform(frame)
                return frozen_model2_features(frame, bundle.parameters)
            @staticmethod
            def unseen_categories(frame):
                result = {}
                for column, allowed in [("pr_tone", bundle.schema["allowed_pr_tone"]), ("tool_id", bundle.schema["known_tool_id"])]:
                    values = set(clean_category(frame[column])) if column in frame else set()
                    unseen = sorted(values.difference(allowed))
                    if unseen: result[column] = unseen
                return result
        return ArtifactBuilder()


def load_reference_bundle(project: Path) -> ReferenceBundle:
    artifacts = project / "artifacts"
    metrics = json.loads((artifacts / "reference_metrics.json").read_text(encoding="utf-8"))
    schema = json.loads((artifacts / "schema_contract.json").read_text(encoding="utf-8"))
    parameters = json.loads((artifacts / "model2_parameters.json").read_text(encoding="utf-8"))
    pipeline = None
    try:
        import joblib
        pipeline = joblib.load(artifacts / "model2_pipeline.joblib")
    except Exception:
        # Cross-version sklearn pickle incompatibility must not take down the app.
        # The frozen JSON carries the exact fitted medians, center, and coefficients.
        pipeline = None
    return ReferenceBundle(pipeline, metrics, schema, parameters)


def frozen_model2_features(frame: pd.DataFrame, parameters: dict) -> pd.DataFrame:
    prepared = prepare_model_frame(frame)
    dose = pd.to_numeric(prepared["normalized_dose_pct"], errors="coerce").fillna(parameters["dose_median"])
    dose_centered = dose - parameters["dose_center"]
    tone = clean_category(prepared["pr_tone"]); tool = clean_category(prepared["tool_id"])
    result = pd.DataFrame(index=prepared.index)
    result["dose_centered"] = dose_centered
    result["pr_tone_NEGATIVE"] = tone.eq("NEGATIVE").astype(float)
    result["pr_tone_MISSING"] = tone.eq("MISSING").astype(float)
    result["dose_x_pr_tone_NEGATIVE"] = dose_centered * result["pr_tone_NEGATIVE"]
    result["dose_x_pr_tone_MISSING"] = dose_centered * result["pr_tone_MISSING"]
    result["tool_id_T02"] = tool.eq("T02").astype(float)
    result["tool_id_T03"] = tool.eq("T03").astype(float)
    return result[MODEL2]
