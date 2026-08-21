---
name: semiconductor-process-analysis
description: Reproducibly analyze new semiconductor process datasets from decision definition through audit, hypothesis-led EDA, interpretable baselines, leakage-aware validation, and bounded reporting. Use for projects under this repository; do not reuse one process's observed directions or metrics as universal process laws.
---

# Semiconductor Process Analysis

## Outcome and boundaries

Build evidence that supports a named engineering decision while preserving raw data, evaluation separation, uncertainty, and an audit trail. Generalize the **procedure**, never a direction, threshold, coefficient, metric, or mechanism observed in another process project.

Before acting, read the target project's `PLAN.md`, repository `AGENTS.md`, and any project-specific `SKILL_NOTES.md`. Record unclear requirements and assumptions. Use only data placed in scope, and never expose actual company data, internal specifications, personal information, credentials, or API keys.

## Workflow

### 1. Define the decision

- **Purpose:** Tie analysis to a real user, decision, KPI, scope, and security boundary.
- **AI:** Read `PLAN.md`; summarize known facts, unknowns, inputs, units, and completion criteria. Ask only for missing information that materially changes the work.
- **Human:** Confirm the user, decision, acceptable evidence, and whether the data is safe to use.
- **Stop when:** Data meaning, provenance, KPI, units, or permission cannot be established.

### 2. Protect data and evaluation boundaries

- **Purpose:** Keep results reproducible and prevent silent contamination.
- **AI:** Treat raw inputs as read-only; identify train, validation, holdout, target, post-process outcomes, identifiers, and prohibited predictors. Log every exclusion or correction in code and outputs.
- **Human:** Confirm the authoritative source and approve any proposed correction to source records.
- **Stop when:** Raw files would need destructive edits, secrets are present, or the train/holdout boundary is ambiguous.

### 3. Audit before analysis

- **Purpose:** Establish whether the dataset is fit for interpretation or modeling.
- **AI:** Check schema, type, unit, missingness, duplicates, range and outlier candidates, category levels, Lot/Tool/time imbalance, target availability, and leakage. Save machine-readable summaries under `outputs/data_audit/`.
- **Human:** Distinguish plausible process excursions from entry, unit, measurement, or transfer errors.
- **Stop when:** Required columns are absent, units conflict, leakage cannot be removed, or unexplained defects invalidate the intended conclusion.

### 4. Handle anomalies as review candidates

- **Purpose:** Avoid converting a convenient cleaning choice into an unsupported fact.
- **AI:** Retain anomalies in the primary analysis unless they are proven duplicates or invalid records; create explicitly labeled sensitivity analyses for candidate exclusions.
- **Human:** Decide whether evidence supports correction, exclusion, retention, or escalation to the data owner.
- **Stop when:** A conclusion depends on silently deleting or correcting rows.

### 5. Separate physically distinct groups

- **Purpose:** Prevent aggregation from hiding opposite or subgroup-specific relationships.
- **AI:** Check whether chemistry, recipe family, product, tool, chamber, Lot, time period, or other process context requires stratified EDA or interactions before pooling.
- **Human:** Confirm which groups are physically comparable and which differences are decision-relevant.
- **Stop when:** Group definitions are unknown or a pooled result reverses/materially changes within-group behavior without explanation.

### 6. Write hypotheses before EDA

- **Purpose:** Separate prior engineering expectations from observed patterns.
- **AI:** Record a primary hypothesis, at least one alternative hypothesis, likely confounders, expected direction only where justified, and evidence that would contradict each claim.
- **Human:** Check domain plausibility, process order, mechanisms, and missing variables.
- **Stop when:** The proposed claim cannot be falsified with available or obtainable evidence.

### 7. Perform hypothesis-led EDA

- **Purpose:** Test whether observations are consistent with the stated hypotheses and expose counterexamples.
- **AI:** Produce appropriate distributions, subgroup plots, association summaries, and sensitivity views under `outputs/eda/`. Treat weak linear correlation as inconclusive when nonlinearity, interactions, or a narrow process window are plausible.
- **Human:** Inspect axes, units, sample sizes, imbalance, physically implausible patterns, and alternative explanations.
- **Stop when:** A graph is dominated by unresolved entry errors, sparse groups, or misleading scales.

### 8. Build a simple baseline first

- **Purpose:** Establish the minimum predictive and explanatory reference before complex ML.
- **AI:** Compare a naive baseline with an interpretable model using only allowed predictors. Fit imputers, encoders, centers, and scalers on Train only. Save features, coefficients, metrics, and data changes under `outputs/modeling/`.
- **Human:** Confirm that features exist at decision time and coefficients are interpreted conditionally, not causally.
- **Stop when:** The model uses post-outcome variables, Validation-derived preprocessing, or undocumented feature engineering.

### 9. Validate against realistic structure

- **Purpose:** Estimate generalization without leakage from related observations.
- **AI:** Keep Train and Validation separate; choose group/time-aware splits when Lot, Tool, wafer, batch, or chronology creates dependence. Report R² or classification metrics alongside error scales and group residuals.
- **Human:** Decide whether the split matches the intended deployment decision.
- **Stop when:** The same protected group crosses Train and Validation in a way that inflates performance.

### 10. Repeat validation

- **Purpose:** Distinguish a fortunate split from a stable result.
- **AI:** Run multiple documented seeds or folds, summarize mean, spread, range, sign/direction stability, and failure cases under `outputs/validation/`.
- **Human:** Decide which aspect matters: predictive accuracy, relationship direction, operational risk, or all three.
- **Stop when:** Only the best split is being selected or instability is hidden by one aggregate metric.

### 11. Test data-quality sensitivity

- **Purpose:** Determine whether conclusions depend on unresolved data issues.
- **AI:** Compare the primary dataset with clearly labeled review scenarios, changing only documented candidate rows or fields. Do not present improvement after exclusion as proof that a row is erroneous.
- **Human:** Prioritize source verification when a few records materially change performance or conclusions.
- **Stop when:** Sensitivity scenarios cannot be traced to explicit audit findings.

### 12. Justify complexity

- **Purpose:** Add ML complexity only for measurable, decision-relevant value.
- **AI:** Compare each complex model with the fixed simple baseline using the same splits, leakage guards, metrics, and stability checks. Include interpretability and maintenance cost.
- **Human:** Approve complexity only when the gain is repeatable and useful for the decision.
- **Stop when:** Complexity merely improves Train performance, obscures data-quality problems, or lacks a fair baseline comparison.

### 13. Preserve the holdout

- **Purpose:** Keep one unbiased final evaluation.
- **AI:** Do not inspect, tune on, merge, or repeatedly score holdout data before analysis and model choices are frozen.
- **Human:** Authorize the final one-time evaluation and interpret it against predefined acceptance criteria.
- **Stop when:** Holdout results have influenced feature, model, threshold, or narrative selection; redefine the evaluation boundary before claiming final performance.

### 14. Save reproducible evidence

- **Purpose:** Make every result traceable and rerunnable.
- **AI:** Store executable code in `scripts/`; save stage-specific tables and figures in `outputs/<stage>/`; use repository-relative paths; verify deterministic reruns where applicable.
- **Human:** Review diffs, source-to-output lineage, and whether documentation matches actual commands.
- **Stop when:** A reported value cannot be traced to a script and source artifact.

### 15. Record failures and decisions

- **Purpose:** Make AI assistance and engineering judgment auditable.
- **AI:** Update `AI_USAGE.md` with generated code, calculations, graphs, models, validation, failures, and corrections.
- **Human:** Record problem framing, exclusions, subgroup choices, alternative explanations, model-selection decisions, and final interpretation.
- **Stop when:** AI output is presented as human-verified without a documented check.

### 16. Report results, limits, and next experiment

- **Purpose:** Convert analysis into bounded engineering action.
- **AI:** Report the problem, data, method, baseline comparison, validation distribution, failure analysis, data-quality impact, alternative hypotheses, limitations, and proposed DOE or next check.
- **Human:** Own the final claim strength, operational recommendation, uncertainty, and experiment priority.
- **Stop when:** Correlation is written as causation, a process-specific observation is generalized beyond its data, or limitations/holdout status are omitted.

## Completion check

Confirm that local build and relevant tests pass; input changes update the app's result, risk, and recommendation; baseline and evaluation performance are visible; `AI_USAGE.md` separates AI work from human decisions; README commands and limitations match the implementation; protected inputs, credentials, and holdout boundaries remain intact.
