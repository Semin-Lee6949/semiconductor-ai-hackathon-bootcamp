#!/usr/bin/env python3
"""Visual explanation of synthetic positive/negative PR process behavior."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


DEFAULT_INPUT = Path("datasets/student/01_photo/A/train.csv")
DEFAULT_OUTPUT = Path("artifacts/photo_pr/photo_pr_process_gallery.png")


def visualization_view(data: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "pr_tone",
        "normalized_dose_pct",
        "coat_thickness_nm",
        "peb_temp_c",
        "develop_time_s",
        "resist_line_cd_nm",
        "scum_probability",
        "pattern_collapse_probability",
    ]
    view = data[columns].dropna().drop_duplicates().copy()
    view = view[
        view["normalized_dose_pct"].between(70, 130)
        & view["coat_thickness_nm"].between(60, 170)
        & view["peb_temp_c"].between(90, 125)
        & view["develop_time_s"].between(25, 80)
        & view["resist_line_cd_nm"].between(35, 70)
    ]
    return view


def binned_surface(data: pd.DataFrame, x: str, y: str, value: str) -> pd.DataFrame:
    working = data.copy()
    working["x_bin"] = pd.cut(working[x], bins=7)
    working["y_bin"] = pd.cut(working[y], bins=7)
    return working.pivot_table(index="y_bin", columns="x_bin", values=value, aggfunc="median", observed=True)


def draw_process_principle(axis: plt.Axes) -> None:
    axis.set_xlim(0, 10)
    axis.set_ylim(0, 6)
    axis.axis("off")
    axis.set_title("PR tone: what remains after development")
    for y, title, left, right in (
        (4.0, "Positive PR", "UNEXPOSED remains", "EXPOSED removed"),
        (1.2, "Negative PR", "UNEXPOSED removed", "EXPOSED remains"),
    ):
        axis.text(0.2, y + 0.65, title, weight="bold")
        axis.add_patch(plt.Rectangle((0.4, y), 4.0, 0.55, color="#4361ee", alpha=0.78))
        axis.add_patch(plt.Rectangle((5.4, y), 4.0, 0.55, color="#f72585", alpha=0.78))
        axis.text(2.4, y + 0.27, left, ha="center", va="center", color="white", fontsize=9)
        axis.text(7.4, y + 0.27, right, ha="center", va="center", color="white", fontsize=9)
    axis.text(0.2, 0.15, "Synthetic retained-line convention; mask/feature tone must be stated.", fontsize=8)


def draw_gallery(data: pd.DataFrame, output: Path) -> None:
    sns.set_theme(style="whitegrid")
    figure, axes = plt.subplots(2, 3, figsize=(17, 9), constrained_layout=True)
    draw_process_principle(axes[0, 0])

    palette = {"POSITIVE": "#4361ee", "NEGATIVE": "#f72585"}
    for tone, group in data.groupby("pr_tone"):
        sns.regplot(
            data=group,
            x="normalized_dose_pct",
            y="resist_line_cd_nm",
            scatter_kws={"alpha": 0.22, "s": 16},
            line_kws={"label": tone},
            color=palette[tone],
            ax=axes[0, 1],
        )
    axes[0, 1].legend()
    axes[0, 1].set_title("Retained-line CD response differs by PR tone")

    sns.scatterplot(
        data=data,
        x="coat_thickness_nm",
        y="resist_line_cd_nm",
        hue="pr_tone",
        palette=palette,
        alpha=0.45,
        ax=axes[0, 2],
    )
    axes[0, 2].set_title("Thickness effect needs tone/process context")

    positive = data[data["pr_tone"] == "POSITIVE"]
    positive_surface = binned_surface(positive, "normalized_dose_pct", "develop_time_s", "scum_probability")
    sns.heatmap(positive_surface, cmap="magma", ax=axes[1, 0])
    axes[1, 0].set_title("Positive PR: median scum risk")
    axes[1, 0].set_xlabel("normalized dose bin")
    axes[1, 0].set_ylabel("develop-time bin")

    negative = data[data["pr_tone"] == "NEGATIVE"]
    negative_surface = binned_surface(negative, "coat_thickness_nm", "peb_temp_c", "resist_line_cd_nm")
    sns.heatmap(negative_surface, cmap="viridis", ax=axes[1, 1])
    axes[1, 1].set_title("Negative PR: thickness × PEB median CD")
    axes[1, 1].set_xlabel("coat-thickness bin")
    axes[1, 1].set_ylabel("PEB-temperature bin")

    working = data.assign(aspect_proxy=data["coat_thickness_nm"] / data["resist_line_cd_nm"])
    sns.scatterplot(
        data=working,
        x="aspect_proxy",
        y="pattern_collapse_probability",
        hue="pr_tone",
        palette=palette,
        alpha=0.48,
        ax=axes[1, 2],
    )
    axes[1, 2].set_title("Collapse risk: thickness/CD proxy")

    figure.suptitle("Synthetic Photo PR process problem-solving map", fontsize=16)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=150)
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    raw = pd.read_csv(args.input)
    view = visualization_view(raw)
    draw_gallery(view, args.output)
    print(f"raw_rows={len(raw)} visual_rows={len(view)}")
    print(f"figure={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
