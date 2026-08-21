"""STEP 5 stability validation for the interpretable Model 2.

Uses only projects/01_photo/data/A/train.csv. Holdout and B data are never read.
No Random Forest or other nonlinear ML model is fitted.
"""

import os
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT / "outputs" / ".matplotlib-cache"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold

from baseline_regression import (
    CONTINUOUS,
    FLAGGED_SAMPLE_IDS,
    FORBIDDEN_POST_CD,
    MODEL_FEATURES,
    TARGET,
    TrainOnlyFeatureBuilder,
    clean_category,
)


INPUT = PROJECT / "data" / "A" / "train.csv"
OUTPUT = PROJECT / "outputs" / "validation"
FIGURES = OUTPUT / "figures"
SEEDS = list(range(30))
VALIDATION_FRACTION = 0.30
LOT_FOLDS = 8
MODEL2 = MODEL_FEATURES["Model 2"]
MODEL2_THICKNESS = MODEL2 + ["coat_thickness_nm"]


def prepare_data() -> pd.DataFrame:
    raw = pd.read_csv(INPUT)
    if len(raw) != 805:
        raise ValueError(f"Expected audited 805 A/train rows, found {len(raw)}")
    used = {"normalized_dose_pct", "pr_tone", "tool_id", "coat_thickness_nm"}
    if used & FORBIDDEN_POST_CD:
        raise AssertionError("Post-CD outcome leakage detected")
    duplicate_mask = raw.duplicated(keep="first")
    if duplicate_mask.sum() != 5:
        raise ValueError(f"Expected 5 extra exact duplicates, found {duplicate_mask.sum()}")
    data = raw.loc[~duplicate_mask].copy().reset_index(drop=True)
    if len(data) != 800:
        raise ValueError("Deduplicated analysis data must contain 800 rows")
    data["pr_tone_group"] = clean_category(data["pr_tone"])
    data["tool_id_group"] = clean_category(data["tool_id"])
    return data


def repeated_split(frame: pd.DataFrame, seed: int):
    """Approximately 70/30 within each PR-tone × tool stratum."""
    rng = np.random.default_rng(seed)
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
    mask = frame.index.isin(validation_indices)
    return frame.loc[~mask].copy(), frame.loc[mask].copy()


def fit_and_score(train, validation, columns):
    builder = TrainOnlyFeatureBuilder().fit(train)
    x_train = builder.transform(train)[columns]
    x_validation = builder.transform(validation)[columns]
    model = LinearRegression().fit(x_train, train[TARGET])
    prediction = model.predict(x_validation)
    coef = dict(zip(columns, model.coef_))
    positive_slope = coef["dose_centered"]
    negative_slope = positive_slope + coef["dose_x_pr_tone_NEGATIVE"]
    return {
        "validation_r2": r2_score(validation[TARGET], prediction),
        "validation_rmse_nm": mean_squared_error(validation[TARGET], prediction) ** 0.5,
        "validation_mae_nm": mean_absolute_error(validation[TARGET], prediction),
        "positive_dose_slope_nm_per_pct_point": positive_slope,
        "negative_dose_slope_nm_per_pct_point": negative_slope,
    }, prediction


def repeated_validation(data):
    rows = []
    thickness_rows = []
    for seed in SEEDS:
        train, validation = repeated_split(data, seed)
        base, _ = fit_and_score(train, validation, MODEL2)
        thick, _ = fit_and_score(train, validation, MODEL2_THICKNESS)
        for model_name, result in [("Model 2", base), ("Model 2 + thickness", thick)]:
            rows.append({"random_state": seed, "model": model_name, "n_train": len(train),
                         "n_validation": len(validation), **result})
        thickness_rows.append({
            "random_state": seed,
            **{f"model2_{k}": v for k, v in base.items() if k.startswith("validation_")},
            **{f"model2_plus_thickness_{k}": v for k, v in thick.items() if k.startswith("validation_")},
            "delta_r2_thickness_minus_model2": thick["validation_r2"] - base["validation_r2"],
            "delta_rmse_nm_thickness_minus_model2": thick["validation_rmse_nm"] - base["validation_rmse_nm"],
            "delta_mae_nm_thickness_minus_model2": thick["validation_mae_nm"] - base["validation_mae_nm"],
            "thickness_improved_r2": thick["validation_r2"] > base["validation_r2"],
            "thickness_improved_rmse": thick["validation_rmse_nm"] < base["validation_rmse_nm"],
            "thickness_improved_mae": thick["validation_mae_nm"] < base["validation_mae_nm"],
        })
    repeated = pd.DataFrame(rows)
    metrics = ["validation_r2", "validation_rmse_nm", "validation_mae_nm",
               "positive_dose_slope_nm_per_pct_point", "negative_dose_slope_nm_per_pct_point"]
    summary = (repeated.groupby("model")[metrics].agg(["mean", "std", "min", "max"])
               .stack(level=0, future_stack=True).reset_index().rename(columns={"level_1": "metric"}))
    summary = summary[["model", "metric", "mean", "std", "min", "max"]]
    return repeated, summary, pd.DataFrame(thickness_rows)


def lot_group_validation(data, n_splits=LOT_FOLDS):
    splitter = GroupKFold(n_splits=n_splits, shuffle=True, random_state=42)
    rows, oof_rows = [], []
    for fold, (train_idx, validation_idx) in enumerate(splitter.split(data, groups=data["lot_id"]), start=1):
        train, validation = data.iloc[train_idx].copy(), data.iloc[validation_idx].copy()
        train_lots, validation_lots = set(train["lot_id"]), set(validation["lot_id"])
        if train_lots & validation_lots:
            raise AssertionError("Lot leakage between Train and Validation")
        result, prediction = fit_and_score(train, validation, MODEL2)
        rows.append({"fold": fold, "n_train": len(train), "n_validation": len(validation),
                     "n_train_lots": len(train_lots), "n_validation_lots": len(validation_lots),
                     "validation_lots": ";".join(sorted(validation_lots)), **result})
        fold_oof = validation[["sample_id", "lot_id", "pr_tone_group", "tool_id_group",
                               "normalized_dose_pct", "focus_um", TARGET]].copy()
        fold_oof["fold"] = fold
        fold_oof["prediction"] = prediction
        fold_oof["residual_actual_minus_predicted_nm"] = fold_oof[TARGET] - prediction
        oof_rows.append(fold_oof)
    oof = pd.concat(oof_rows).sort_index()
    if len(oof) != len(data) or oof.index.nunique() != len(data):
        raise AssertionError("Every deduplicated row must receive exactly one Lot-OOF prediction")
    return pd.DataFrame(rows), oof


def data_quality_sensitivity(data, flagged_sample_ids=None):
    flagged_sample_ids = FLAGGED_SAMPLE_IDS if flagged_sample_ids is None else set(flagged_sample_ids)
    rows = []
    for condition, frame in [("A_including_flagged", data),
                             (f"B_excluding_{len(flagged_sample_ids)}_flagged_rows",
                              data[~data["sample_id"].isin(flagged_sample_ids)].copy())]:
        for seed in SEEDS:
            train, validation = repeated_split(frame, seed)
            result, _ = fit_and_score(train, validation, MODEL2)
            rows.append({"condition": condition, "random_state": seed, "n_total": len(frame),
                         "n_train": len(train), "n_validation": len(validation), **result})
    detail = pd.DataFrame(rows)
    metrics = ["validation_r2", "validation_rmse_nm", "validation_mae_nm",
               "positive_dose_slope_nm_per_pct_point", "negative_dose_slope_nm_per_pct_point"]
    summary = (detail.groupby("condition")[metrics].agg(["mean", "std", "min", "max"])
               .stack(level=0, future_stack=True).reset_index().rename(columns={"level_1": "metric"}))
    summary = summary[["condition", "metric", "mean", "std", "min", "max"]]
    return detail, summary


def residual_summary(oof):
    frame = oof.copy()
    frame["normalized_dose_bin"] = pd.qcut(frame["normalized_dose_pct"], 5, duplicates="drop").astype("string").fillna("MISSING")
    frame["focus_bin"] = pd.qcut(frame["focus_um"], 5, duplicates="drop").astype("string").fillna("MISSING")
    rows = []
    groupings = {
        "pr_tone": "pr_tone_group", "tool": "tool_id_group", "lot": "lot_id",
        "normalized_dose_quintile": "normalized_dose_bin", "focus_quintile": "focus_bin",
    }
    residual_col = "residual_actual_minus_predicted_nm"
    for group_type, column in groupings.items():
        for value, group in frame.groupby(column, dropna=False, sort=True):
            residual = group[residual_col]
            mean_residual = residual.mean()
            if mean_residual >= 0.5:
                pattern = "underprediction_mean_at_least_0.5nm"
            elif mean_residual <= -0.5:
                pattern = "overprediction_mean_at_least_0.5nm"
            else:
                pattern = "no_large_mean_bias"
            rows.append({"group_type": group_type, "group_value": str(value), "n": len(group),
                         "mean_residual_nm": mean_residual, "median_residual_nm": residual.median(),
                         "rmse_nm": np.sqrt(np.mean(residual ** 2)), "mae_nm": np.mean(np.abs(residual)),
                         "pattern_flag": pattern})
    return pd.DataFrame(rows), frame


def lot_validation_summary(lot_results, oof):
    rows = []
    for metric in ["validation_r2", "validation_rmse_nm", "validation_mae_nm"]:
        values = lot_results[metric]
        rows.append({"scope": "fold_distribution", "metric": metric, "mean": values.mean(),
                     "std": values.std(), "min": values.min(), "max": values.max()})
    actual, prediction = oof[TARGET], oof["prediction"]
    pooled = {
        "validation_r2": r2_score(actual, prediction),
        "validation_rmse_nm": mean_squared_error(actual, prediction) ** .5,
        "validation_mae_nm": mean_absolute_error(actual, prediction),
    }
    for metric, value in pooled.items():
        rows.append({"scope": "pooled_out_of_fold", "metric": metric, "mean": value,
                     "std": np.nan, "min": np.nan, "max": np.nan})
    return pd.DataFrame(rows)


def make_figures(repeated, lot_results, thickness, residual_frame, residual_groups):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    metrics = [("validation_r2", "Validation R²"), ("validation_rmse_nm", "RMSE (nm)"),
               ("validation_mae_nm", "MAE (nm)")]
    model_order = ["Model 2", "Model 2 + thickness"]
    for ax, (metric, label) in zip(axes, metrics):
        ax.boxplot([repeated.loc[repeated["model"].eq(m), metric] for m in model_order], tick_labels=model_order)
        ax.set(title=label, ylabel=label); ax.tick_params(axis="x", rotation=10)
    fig.suptitle("30 repeated stratified splits")
    fig.tight_layout(); fig.savefig(FIGURES / "repeated_validation_performance.png", dpi=170); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    pos = repeated[repeated["model"].eq("Model 2")]
    ax.boxplot([pos["positive_dose_slope_nm_per_pct_point"], pos["negative_dose_slope_nm_per_pct_point"]],
               tick_labels=["POSITIVE", "NEGATIVE"])
    ax.axhline(0, color="black", ls="--", lw=1)
    ax.set(title="Model 2 dose slopes across 30 splits", ylabel="nm CD per dose percentage point")
    fig.tight_layout(); fig.savefig(FIGURES / "repeated_dose_slopes.png", dpi=170); plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    for ax, (metric, label) in zip(axes, metrics):
        ax.bar(lot_results["fold"].astype(str), lot_results[metric], color="#4C78A8")
        ax.axhline(lot_results[metric].mean(), color="#E45756", ls="--", label="fold mean")
        ax.set(title=label, xlabel="Lot fold", ylabel=label); ax.legend()
    fig.suptitle("Unseen-Lot Group Cross Validation")
    fig.tight_layout(); fig.savefig(FIGURES / "lot_group_validation_performance.png", dpi=170); plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    deltas = [("delta_r2_thickness_minus_model2", "Δ R²"),
              ("delta_rmse_nm_thickness_minus_model2", "Δ RMSE (nm)"),
              ("delta_mae_nm_thickness_minus_model2", "Δ MAE (nm)")]
    for ax, (column, label) in zip(axes, deltas):
        ax.bar(thickness["random_state"], thickness[column], color="#72B7B2")
        ax.axhline(0, color="black", lw=1); ax.set(title=label, xlabel="random_state", ylabel="thickness - Model 2")
    fig.suptitle("Effect of adding coat thickness")
    fig.tight_layout(); fig.savefig(FIGURES / "thickness_deltas.png", dpi=170); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
    for ax, (column, title) in zip(axes, [("pr_tone_group", "PR tone"), ("tool_id_group", "Tool")]):
        values = sorted(residual_frame[column].unique())
        ax.boxplot([residual_frame.loc[residual_frame[column].eq(v), "residual_actual_minus_predicted_nm"] for v in values],
                   tick_labels=values, showfliers=True)
        ax.axhline(0, color="black", ls="--", lw=1); ax.set(title=title, ylabel="Lot-OOF residual actual-predicted (nm)")
    fig.tight_layout(); fig.savefig(FIGURES / "residual_by_pr_tone_and_tool.png", dpi=170); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
    for ax, (column, title) in zip(axes, [("normalized_dose_pct", "Normalized dose"), ("focus_um", "Focus")]):
        pair = residual_frame[[column, "residual_actual_minus_predicted_nm"]].dropna()
        ax.scatter(pair[column], pair["residual_actual_minus_predicted_nm"], alpha=.45, s=18)
        ax.axhline(0, color="black", ls="--", lw=1); ax.set(title=title, xlabel=column, ylabel="Lot-OOF residual (nm)")
    fig.tight_layout(); fig.savefig(FIGURES / "residual_vs_dose_and_focus.png", dpi=170); plt.close(fig)

    lots = residual_groups[residual_groups["group_type"].eq("lot")].sort_values("mean_residual_nm")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(lots["group_value"], lots["mean_residual_nm"], color=np.where(lots["mean_residual_nm"] >= 0, "#4C78A8", "#E45756"))
    ax.axhline(0, color="black", lw=1); ax.axhline(.5, color="gray", ls="--"); ax.axhline(-.5, color="gray", ls="--")
    ax.set(title="Mean unseen-Lot residual by lot", xlabel="lot_id", ylabel="actual-predicted (nm)")
    ax.tick_params(axis="x", rotation=90)
    fig.tight_layout(); fig.savefig(FIGURES / "residual_mean_by_lot.png", dpi=170); plt.close(fig)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True); FIGURES.mkdir(parents=True, exist_ok=True)
    data = prepare_data()
    repeated, repeated_summary, thickness = repeated_validation(data)
    repeated.to_csv(OUTPUT / "repeated_validation.csv", index=False, encoding="utf-8-sig")
    repeated_summary.to_csv(OUTPUT / "repeated_validation_summary.csv", index=False, encoding="utf-8-sig")
    thickness.to_csv(OUTPUT / "thickness_comparison.csv", index=False, encoding="utf-8-sig")

    lot_results, oof = lot_group_validation(data)
    lot_results.to_csv(OUTPUT / "lot_group_validation.csv", index=False, encoding="utf-8-sig")
    oof.to_csv(OUTPUT / "lot_group_oof_predictions.csv", index=False, encoding="utf-8-sig")
    lot_validation_summary(lot_results, oof).to_csv(
        OUTPUT / "lot_group_validation_summary.csv", index=False, encoding="utf-8-sig")

    quality_detail, quality_summary = data_quality_sensitivity(data)
    quality_detail.to_csv(OUTPUT / "data_quality_sensitivity.csv", index=False, encoding="utf-8-sig")
    quality_summary.to_csv(OUTPUT / "data_quality_sensitivity_summary.csv", index=False, encoding="utf-8-sig")

    residual_groups, residual_frame = residual_summary(oof)
    residual_groups.to_csv(OUTPUT / "residual_group_summary.csv", index=False, encoding="utf-8-sig")
    residual_frame.assign(abs_residual_nm=residual_frame["residual_actual_minus_predicted_nm"].abs()).nlargest(
        20, "abs_residual_nm").to_csv(OUTPUT / "largest_lot_oof_residuals.csv", index=False, encoding="utf-8-sig")
    make_figures(repeated, lot_results, thickness, residual_frame, residual_groups)
    print(f"Validation complete: 30 repeated splits, {LOT_FOLDS} unseen-Lot folds, 800 deduplicated rows; holdout/B not read")


if __name__ == "__main__":
    main()
