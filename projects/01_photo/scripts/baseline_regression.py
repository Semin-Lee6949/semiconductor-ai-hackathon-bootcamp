"""STEP 4 interpretable baseline regressions using A/train.csv only.

The script deliberately does not read holdout_features.csv. Post-CD quality
outcomes are prohibited predictors. All imputations and feature centers are
learned from the training partition only.
"""

import os
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT / "outputs" / ".matplotlib-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


INPUT = PROJECT / "data" / "A" / "train.csv"
OUTPUT = PROJECT / "outputs" / "modeling"
FIGURES = OUTPUT / "figures"
TARGET = "resist_line_cd_nm"
RANDOM_STATE = 42
VALIDATION_FRACTION = 0.30
FORBIDDEN_POST_CD = {
    "cdu_3sigma_nm", "ler_nm", "scum_probability",
    "pattern_collapse_probability", "defect_probability", "spec_pass",
}
CONTINUOUS = [
    "normalized_dose_pct", "focus_um", "coat_thickness_nm", "develop_time_s",
    "peb_temp_c", "softbake_temp_c", "developer_concentration_pct",
]
FLAGGED_SAMPLE_IDS = {"S00160", "S00748", "S00475", "S00634", "S00636"}
FLAG_REASONS = {
    "S00160": "focus_um=0.933515; operating cluster 대비 축 왜곡/소수점 입력 의심",
    "S00748": "coat_thickness_nm=9.465512; 관측 군집 대비 약 1/10, 단위/소수점 입력 의심",
    "S00475": "softbake_temp_c=9.979035; 감사 물리 검토 하한 50 C 미만",
    "S00634": "developer_concentration_pct=12.21005; 관측 군집 대비 약 5배",
    "S00636": "normalized_dose_pct=9.908105; 같은 행 exposure dose와 10배 차이",
}

# Broad, explicit review rules derived from the five obvious decimal/unit-entry
# suspects documented in STEP 2/3. These flag rows for review; they do not edit data.
SUSPECT_INPUT_RULES = {
    "normalized_dose_pct": (lambda s: s < 50, "below 50%; decimal-place/unit entry suspect"),
    "focus_um": (lambda s: s.abs() > 0.5, "absolute focus above 0.5 um; decimal-place entry suspect"),
    "coat_thickness_nm": (lambda s: s < 50, "below 50 nm; about one tenth of observed operating cluster"),
    "softbake_temp_c": (lambda s: s < 50, "below 50 C physical review bound"),
    "developer_concentration_pct": (lambda s: s > 5, "above 5%; far outside observed operating cluster"),
}

MODEL_FEATURES = {
    "Model 1": ["dose_centered", "pr_tone_NEGATIVE", "pr_tone_MISSING",
                "dose_x_pr_tone_NEGATIVE", "dose_x_pr_tone_MISSING"],
    "Model 2": ["dose_centered", "pr_tone_NEGATIVE", "pr_tone_MISSING",
                "dose_x_pr_tone_NEGATIVE", "dose_x_pr_tone_MISSING", "tool_id_T02", "tool_id_T03"],
    "Model 3": ["dose_centered", "pr_tone_NEGATIVE", "pr_tone_MISSING",
                "dose_x_pr_tone_NEGATIVE", "dose_x_pr_tone_MISSING", "tool_id_T02", "tool_id_T03",
                "focus_um", "focus_um_squared", "coat_thickness_nm", "develop_time_s",
                "peb_temp_c", "softbake_temp_c", "developer_concentration_pct"],
}


def clean_category(series: pd.Series) -> pd.Series:
    value = series.astype("string").str.strip().str.upper()
    return value.where(value.notna() & value.ne(""), "MISSING")


def detect_suspected_input_errors(frame: pd.DataFrame) -> pd.DataFrame:
    """Return review flags without altering or automatically excluding any row."""
    rows = []
    for column, (rule, reason) in SUSPECT_INPUT_RULES.items():
        if column not in frame:
            continue
        numeric = pd.to_numeric(frame[column], errors="coerce")
        for index in frame.index[rule(numeric).fillna(False)]:
            rows.append({
                "row_index": index,
                "sample_id": frame.at[index, "sample_id"] if "sample_id" in frame else f"ROW_{index}",
                "variable": column,
                "value": numeric.at[index],
                "reason": reason,
                "action": "review_only; included by default",
            })
    return pd.DataFrame(rows, columns=["row_index", "sample_id", "variable", "value", "reason", "action"])


def stratified_split(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Deterministically sample about 30% within each tone×tool stratum."""
    rng = np.random.default_rng(RANDOM_STATE)
    validation_indices = []
    strata = frame["pr_tone_group"] + "|" + frame["tool_id_group"]
    for _, indices in frame.groupby(strata, sort=True).groups.items():
        indices = np.asarray(list(indices))
        shuffled = rng.permutation(indices)
        n_validation = int(round(len(indices) * VALIDATION_FRACTION))
        if len(indices) > 1:
            n_validation = min(max(n_validation, 1), len(indices) - 1)
        else:
            n_validation = 0
        validation_indices.extend(shuffled[:n_validation].tolist())
    validation_mask = frame.index.isin(validation_indices)
    return frame.loc[~validation_mask].copy(), frame.loc[validation_mask].copy()


class TrainOnlyFeatureBuilder:
    """Small transparent transformer with train-only medians and centers."""

    def fit(self, train: pd.DataFrame) -> "TrainOnlyFeatureBuilder":
        self.medians = {col: float(train[col].median()) for col in CONTINUOUS}
        if any(np.isnan(v) for v in self.medians.values()):
            raise ValueError("A continuous feature has no observed training values")
        self.dose_center = self.medians["normalized_dose_pct"]
        return self

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        numeric = frame[CONTINUOUS].copy()
        for col, median in self.medians.items():
            numeric[col] = numeric[col].fillna(median)
        out = pd.DataFrame(index=frame.index)
        out["dose_centered"] = numeric["normalized_dose_pct"] - self.dose_center
        tone = frame["pr_tone_group"]
        tool = frame["tool_id_group"]
        for level in ["NEGATIVE", "MISSING"]:  # reference: POSITIVE
            out[f"pr_tone_{level}"] = tone.eq(level).astype(float)
            out[f"dose_x_pr_tone_{level}"] = out["dose_centered"] * out[f"pr_tone_{level}"]
        for level in ["T02", "T03"]:  # reference: T01
            out[f"tool_id_{level}"] = tool.eq(level).astype(float)
        out["focus_um"] = numeric["focus_um"]
        out["focus_um_squared"] = numeric["focus_um"] ** 2
        for col in ["coat_thickness_nm", "develop_time_s", "peb_temp_c",
                    "softbake_temp_c", "developer_concentration_pct"]:
            out[col] = numeric[col]
        return out


def metric_row(model_name, analysis, split_name, y_true, y_pred, n, n_features):
    return {
        "model": model_name, "analysis": analysis, "split": split_name, "n": n,
        "n_features": n_features, "r2": r2_score(y_true, y_pred),
        "rmse_nm": mean_squared_error(y_true, y_pred) ** 0.5,
        "mae_nm": mean_absolute_error(y_true, y_pred),
    }


def fit_models(train, validation, analysis):
    builder = TrainOnlyFeatureBuilder().fit(train)
    train_x_all, validation_x_all = builder.transform(train), builder.transform(validation)
    rows, coefficients, predictions, fitted = [], [], {}, {}
    y_train, y_validation = train[TARGET], validation[TARGET]

    baseline = DummyRegressor(strategy="mean").fit(np.zeros((len(train), 1)), y_train)
    baseline_preds = {
        "Train": baseline.predict(np.zeros((len(train), 1))),
        "Validation": baseline.predict(np.zeros((len(validation), 1))),
    }
    for split_name, actual, pred in [("Train", y_train, baseline_preds["Train"]),
                                      ("Validation", y_validation, baseline_preds["Validation"])]:
        rows.append(metric_row("Model 0", analysis, split_name, actual, pred, len(actual), 0))
    coefficients.append({"model": "Model 0", "analysis": analysis, "term": "intercept_mean_cd_nm",
                         "coefficient": float(np.asarray(baseline.constant_).ravel()[0]), "reference_or_unit": "nm"})
    predictions["Model 0"] = baseline_preds

    for model_name, columns in MODEL_FEATURES.items():
        model = LinearRegression().fit(train_x_all[columns], y_train)
        train_pred = model.predict(train_x_all[columns])
        validation_pred = model.predict(validation_x_all[columns])
        for split_name, actual, pred in [("Train", y_train, train_pred),
                                          ("Validation", y_validation, validation_pred)]:
            rows.append(metric_row(model_name, analysis, split_name, actual, pred, len(actual), len(columns)))
        coefficients.append({"model": model_name, "analysis": analysis, "term": "intercept",
                             "coefficient": model.intercept_,
                             "reference_or_unit": f"PR=POSITIVE, tool=T01, dose centered at train median {builder.dose_center:.6g}%"})
        for term, value in zip(columns, model.coef_):
            unit = "nm CD per feature unit"
            if term == "dose_centered": unit = "Positive: nm CD per normalized-dose percentage point"
            elif term == "dose_x_pr_tone_NEGATIVE": unit = "Negative minus Positive dose slope"
            elif term.startswith("pr_tone_"): unit = "difference from POSITIVE at centered dose=0"
            elif term.startswith("tool_id_"): unit = "difference from T01"
            elif term == "focus_um_squared": unit = "nm CD per um^2"
            coefficients.append({"model": model_name, "analysis": analysis, "term": term,
                                 "coefficient": value, "reference_or_unit": unit})
        coef_map = dict(zip(columns, model.coef_))
        coefficients.extend([
            {"model": model_name, "analysis": analysis, "term": "derived_dose_slope_POSITIVE",
             "coefficient": coef_map["dose_centered"], "reference_or_unit": "nm CD per normalized-dose percentage point"},
            {"model": model_name, "analysis": analysis, "term": "derived_dose_slope_NEGATIVE",
             "coefficient": coef_map["dose_centered"] + coef_map["dose_x_pr_tone_NEGATIVE"],
             "reference_or_unit": "main dose slope + NEGATIVE interaction"},
            {"model": model_name, "analysis": analysis, "term": "derived_dose_slope_MISSING",
             "coefficient": coef_map["dose_centered"] + coef_map["dose_x_pr_tone_MISSING"],
             "reference_or_unit": "descriptive only; MISSING tone is not a physical PR group"},
        ])
        predictions[model_name] = {"Train": train_pred, "Validation": validation_pred}
        fitted[model_name] = (model, columns, builder)
    return rows, coefficients, predictions, fitted


def split_summary(full, train, validation):
    rows = []
    for split_name, part in [("Analysis total", full), ("Train", train), ("Validation", validation)]:
        for grouping, columns in [("ALL", []), ("pr_tone", ["pr_tone_group"]),
                                  ("tool_id", ["tool_id_group"]),
                                  ("pr_tone_x_tool_id", ["pr_tone_group", "tool_id_group"])]:
            groups = [((), part)] if not columns else part.groupby(columns, dropna=False, sort=True)
            for key, group in groups:
                if not isinstance(key, tuple): key = (key,)
                value = "ALL" if not columns else "|".join(map(str, key))
                rows.append({"split": split_name, "grouping": grouping, "group": value,
                             "n": len(group), "pct_within_split": 100 * len(group) / len(part)})
    return pd.DataFrame(rows)


def ablation_analysis(train, validation):
    builder = TrainOnlyFeatureBuilder().fit(train)
    x_train, x_validation = builder.transform(train), builder.transform(validation)
    full_columns = MODEL_FEATURES["Model 3"]
    y_train, y_validation = train[TARGET], validation[TARGET]

    def score(columns):
        model = LinearRegression().fit(x_train[columns], y_train)
        pred = model.predict(x_validation[columns])
        return r2_score(y_validation, pred), mean_squared_error(y_validation, pred) ** .5, mean_absolute_error(y_validation, pred)

    full_r2, full_rmse, full_mae = score(full_columns)
    rows = [{"ablation": "none_full_model_3", "removed_terms": "", "validation_r2": full_r2,
             "validation_rmse_nm": full_rmse, "validation_mae_nm": full_mae,
             "delta_r2_vs_full": 0.0, "delta_rmse_nm_vs_full": 0.0}]
    tests = {
        "remove_focus_squared_only": ["focus_um_squared"],
        "remove_focus_linear_and_squared": ["focus_um", "focus_um_squared"],
        "remove_coat_thickness": ["coat_thickness_nm"],
        "remove_develop_time": ["develop_time_s"],
        "remove_peb_temp": ["peb_temp_c"],
        "remove_softbake_temp": ["softbake_temp_c"],
        "remove_developer_concentration": ["developer_concentration_pct"],
    }
    for label, removed in tests.items():
        cols = [c for c in full_columns if c not in removed]
        r2, rmse, mae = score(cols)
        rows.append({"ablation": label, "removed_terms": ";".join(removed), "validation_r2": r2,
                     "validation_rmse_nm": rmse, "validation_mae_nm": mae,
                     "delta_r2_vs_full": r2 - full_r2, "delta_rmse_nm_vs_full": rmse - full_rmse})
    return pd.DataFrame(rows)


def make_figures(comparison, validation, predictions):
    primary = comparison[comparison["analysis"].eq("original_including_flagged")]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    for ax, metric, label in zip(axes, ["r2", "rmse_nm", "mae_nm"], ["R²", "RMSE (nm)", "MAE (nm)"]):
        pivot = primary.pivot(index="model", columns="split", values=metric).reindex([f"Model {i}" for i in range(4)])
        pivot.plot.bar(ax=ax, color=["#4C78A8", "#F58518"])
        ax.set(title=label, xlabel="", ylabel=label); ax.tick_params(axis="x", rotation=0)
    fig.suptitle("Train vs validation model performance")
    fig.tight_layout(); fig.savefig(FIGURES / "model_performance.png", dpi=170); plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(10, 9), sharex=True, sharey=True)
    actual = validation[TARGET].to_numpy()
    limits = [actual.min() - 1, actual.max() + 1]
    for ax, model_name in zip(axes.flat, [f"Model {i}" for i in range(4)]):
        pred = predictions[model_name]["Validation"]
        ax.scatter(actual, pred, alpha=.55, s=22); ax.plot(limits, limits, "--", color="black", lw=1)
        ax.set(title=model_name, xlabel="Actual CD (nm)", ylabel="Predicted CD (nm)", xlim=limits, ylim=limits)
    fig.suptitle("Validation predicted vs actual")
    fig.tight_layout(); fig.savefig(FIGURES / "predicted_vs_actual.png", dpi=170); plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(10, 9), sharey=True)
    for ax, model_name in zip(axes.flat, [f"Model {i}" for i in range(4)]):
        pred = predictions[model_name]["Validation"]
        residual = validation[TARGET].to_numpy() - pred
        ax.scatter(pred, residual, alpha=.55, s=22); ax.axhline(0, ls="--", color="black", lw=1)
        ax.set(title=model_name, xlabel="Predicted CD (nm)", ylabel="Residual actual-predicted (nm)")
    fig.suptitle("Validation residual plots")
    fig.tight_layout(); fig.savefig(FIGURES / "residual_plot.png", dpi=170); plt.close(fig)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True); FIGURES.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(INPUT)
    if len(raw) != 805: raise ValueError(f"Expected 805 audited train rows, found {len(raw)}")
    if TARGET not in raw or FORBIDDEN_POST_CD.difference(raw.columns):
        raise ValueError("Target or expected prohibited post-CD columns missing")
    used_predictors = {"normalized_dose_pct", "pr_tone", "tool_id", *CONTINUOUS}
    if used_predictors & FORBIDDEN_POST_CD:
        raise AssertionError("Post-CD outcome leakage detected")

    raw = raw.copy(); raw["source_row_number"] = np.arange(2, len(raw) + 2)
    duplicate_mask = raw.drop(columns="source_row_number").duplicated(keep="first")
    duplicates = raw.loc[duplicate_mask].copy()
    data = raw.loc[~duplicate_mask].copy()
    if len(duplicates) != 5 or len(data) != 800:
        raise ValueError(f"Expected 5 extra exact duplicates and 800 analysis rows, got {len(duplicates)} and {len(data)}")
    data["pr_tone_group"] = clean_category(data["pr_tone"])
    data["tool_id_group"] = clean_category(data["tool_id"])
    data = data.reset_index(drop=True)
    train, validation = stratified_split(data)
    split_lookup = pd.Series("Train", index=train["sample_id"])
    split_lookup = pd.concat([split_lookup, pd.Series("Validation", index=validation["sample_id"])])

    changes = []
    for _, row in duplicates.iterrows():
        changes.append({"change_type": "exact_duplicate_removed", "sample_id": row["sample_id"],
                        "source_row_number": row["source_row_number"], "affected_variable": "ALL",
                        "primary_analysis_action": "removed extra copy before split",
                        "sensitivity_action": "same", "reason": "prevent identical-row Train/Validation leakage"})
    for sample_id in sorted(FLAGGED_SAMPLE_IDS):
        hit = data[data["sample_id"].eq(sample_id)].iloc[0]
        changes.append({"change_type": "suspected_input_unit_error", "sample_id": sample_id,
                        "source_row_number": int(hit["source_row_number"]), "affected_variable": "see reason",
                        "primary_analysis_action": "included; missing values still train-median imputed",
                        "sensitivity_action": f"entire row excluded from preassigned {split_lookup.loc[sample_id]} split",
                        "reason": FLAG_REASONS[sample_id]})
    changes.extend([
        {"change_type": "missing_value_handling", "sample_id": "ALL", "source_row_number": "",
         "affected_variable": ";".join(CONTINUOUS), "primary_analysis_action": "Train median imputation per numeric variable",
         "sensitivity_action": "same", "reason": "no Validation information used"},
        {"change_type": "categorical_missing_handling", "sample_id": "ALL", "source_row_number": "",
         "affected_variable": "pr_tone", "primary_analysis_action": "MISSING category retained",
         "sensitivity_action": "same", "reason": "do not drop complete rows"},
        {"change_type": "leakage_guard", "sample_id": "ALL", "source_row_number": "",
         "affected_variable": ";".join(sorted(FORBIDDEN_POST_CD)), "primary_analysis_action": "prohibited/not used",
         "sensitivity_action": "same", "reason": "post-CD quality outcomes"},
    ])
    pd.DataFrame(changes).to_csv(OUTPUT / "modeling_data_changes.csv", index=False, encoding="utf-8-sig")
    split_summary(data, train, validation).to_csv(OUTPUT / "train_validation_split_summary.csv", index=False, encoding="utf-8-sig")

    rows, coefs, predictions, _ = fit_models(train, validation, "original_including_flagged")
    clean_train = train[~train["sample_id"].isin(FLAGGED_SAMPLE_IDS)].copy()
    clean_validation = validation[~validation["sample_id"].isin(FLAGGED_SAMPLE_IDS)].copy()
    rows2, coefs2, _, _ = fit_models(clean_train, clean_validation, "flagged_rows_excluded_sensitivity")
    comparison = pd.DataFrame(rows + rows2)
    comparison.to_csv(OUTPUT / "model_comparison.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(coefs + coefs2).to_csv(OUTPUT / "coefficient_table.csv", index=False, encoding="utf-8-sig")
    ablation_analysis(train, validation).to_csv(OUTPUT / "model3_feature_ablation.csv", index=False, encoding="utf-8-sig")
    make_figures(comparison, validation, predictions)
    print(f"Modeling complete: raw=805, deduplicated=800, train={len(train)}, validation={len(validation)}; holdout not read")


if __name__ == "__main__":
    main()
