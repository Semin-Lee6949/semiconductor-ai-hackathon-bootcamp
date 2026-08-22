"""Fixed Model 2 reference artifact helpers.

The serialized Pipeline is trained only by train_reference_model.py on A/train.
Uploaded data is evaluated or scored with the frozen artifact; it is never fit here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
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
    pipeline: Pipeline
    metrics: dict
    schema: dict

    name: str = "Reference Model 2"
    target: str = TARGET
    inputs: tuple = ("normalized_dose_pct", "pr_tone", "tool_id")
    interaction: bool = True

    @property
    def coefficients(self) -> pd.DataFrame:
        regression = self.pipeline.named_steps["regression"]
        names = self.pipeline.named_steps["features"].get_feature_names_out()
        return pd.DataFrame({"term": ["intercept", *names], "coefficient": [float(regression.intercept_), *regression.coef_.astype(float)]})

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        return self.pipeline.predict(frame)

    @property
    def builder(self):
        bundle = self
        class ArtifactBuilder:
            feature_names = list(MODEL2)
            ranges = {column: (values["min"], values["max"]) for column, values in bundle.schema["reference_ranges"].items()}
            medians = {column: values["median"] for column, values in bundle.schema["reference_ranges"].items()}
            levels = {"pr_tone": bundle.schema["allowed_pr_tone"], "tool_id": bundle.schema["known_tool_id"]}
            @staticmethod
            def transform(frame): return bundle.pipeline.named_steps["features"].transform(frame)
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
    pipeline = joblib.load(artifacts / "model2_pipeline.joblib")
    metrics = json.loads((artifacts / "reference_metrics.json").read_text(encoding="utf-8"))
    schema = json.loads((artifacts / "schema_contract.json").read_text(encoding="utf-8"))
    return ReferenceBundle(pipeline, metrics, schema)
