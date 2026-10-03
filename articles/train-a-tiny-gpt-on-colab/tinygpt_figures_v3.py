"""Render P1 teaching figures, explicit-legend revision from the unchanged T4 receipt; no training.

Requires matplotlib and Pillow. Exports standalone PNG/SVG and article WebP.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D
from PIL import Image

HERE = Path(__file__).resolve().parent
RECEIPT = HERE / "receipts/colab/tinygpt-full-20261003.json"
SLUG = "train-a-tiny-gpt-on-colab"
INK, GREEN, RED, BLUE = "#242522", "#206d59", "#b13929", "#305d99"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False, "svg.fonttype": "none", "svg.hashsalt": "profrod-p1-v1"})


def export(fig, number: int, out: Path) -> dict:
    stem = f"{SLUG}--figure-{number}"
    fig.savefig(out / f"{stem}.svg", bbox_inches="tight", facecolor="white", metadata={"Date": None})
    svg = out / f"{stem}.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    fig.savefig(out / f"{stem}.png", dpi=240, bbox_inches="tight", facecolor="white")
    with Image.open(out / f"{stem}.png") as im:
        im.convert("RGB").save(out / f"{stem}.webp", quality=95, method=6)
    plt.close(fig)
    return {name: hashlib.sha256((out / f"{stem}.{name}").read_bytes()).hexdigest() for name in ("svg", "png", "webp")}


def matrix(out: Path) -> dict:
    fig, ax = plt.subplots(figsize=(4.8, 4.9))
    ax.set(xlim=(-1.1, 3.7), ylim=(-2.4, 3.9))
    ax.axis("off")
    ax.text(1.5, 3.6, "Keys (columns)", ha="center", weight="bold", color=INK)
    for j in range(3):
        ax.text(j + 0.5, 3.1, f"k{j + 1}", ha="center", color=INK)
    for i in range(3):
        y = 2 - i
        ax.text(-0.2, y + 0.5, f"q{i + 1}", ha="right", va="center", color=INK)
        for j in range(3):
            masked = j > i
            fill = "#eeeeeb" if masked else ("#f6d5cf" if j == 0 and i > 0 else "#d5e9e3")
            ax.add_patch(Rectangle((j, y), 1, 1, facecolor=fill, edgecolor="white", linewidth=2))
            label = "masked" if masked else f"S{i + 1}{j + 1}"
            ax.text(j + 0.5, y + 0.5, label, ha="center", va="center", color=INK, fontsize=13)
    # Outlines, not animated arrows: row 1 versus column 1 is the dependency.
    ax.add_patch(Rectangle((0.03, 2.03), 0.94, 0.94, fill=False, edgecolor=GREEN, linewidth=3))
    ax.add_patch(Rectangle((-0.02, -0.02), 1.04, 3.04, fill=False, edgecolor=RED, linewidth=2, linestyle="--"))
    ax.text(-1.02, 1.5, "Queries", rotation=90, va="center", color=INK)
    ax.text(0, -0.42, "Correct q1: row 1 (green)", color=GREEN, weight="bold", fontsize=12)
    ax.text(0, -0.84, "Wrong q1: column 1 (dashed)", color=RED, weight="bold", fontsize=12)
    ax.text(0, -1.75, "Future token 3 changes q3 and S31.\nS31 enters q1’s wrong denominator.", color=INK, fontsize=12)
    return export(fig, 1, out)


def curves(receipt: dict, out: Path) -> dict:
    steps = receipt["healthy"]["evalSteps"]
    band = receipt["healthy"]["band"]
    refs = [r for r in receipt["runs"] if r["runId"].startswith("healthy-")]
    controls = [r for r in receipt["runs"] if r["runId"].startswith("control-")]
    assert len(refs) == 5 and len(controls) == 3
    fig, all_axes = plt.subplots(5, 1, figsize=(5.6, 10.2), gridspec_kw={"height_ratios": [1, 1, 1, 1, 0.48]}, layout="constrained")
    axes = all_axes[:4]
    legend_ax = all_axes[4]
    legend_ax.axis("off")
    legend_ax.legend(handles=[
        Line2D([], [], color=RED, label="Faulty runs (3)"),
        Line2D([], [], color=GREEN, lw=1.5, label="Healthy mean"),
        Patch(facecolor=GREEN, alpha=0.16, label="95% prediction band"),
        Line2D([], [], color=BLUE, ls="--", label="Heldout controls (3)"),
        Line2D([], [], color=RED, marker="o", ls="none", label="Original flag dots"),
    ], loc="center", ncol=2, fontsize=13, frameon=False)
    fig.suptitle("Same task, four different loss curves", fontsize=14, weight="bold")
    for index, ax in enumerate(axes):
        ax.fill_between(steps, band["piLow"], band["piHigh"], color=GREEN, alpha=0.16)
        for i, r in enumerate(refs):
            ax.plot(r["evalSteps"], r["valLoss"], color=GREEN, alpha=0.45, lw=0.9, label="Reference (5)" if i == 0 else None)
        for i, r in enumerate(controls):
            ax.plot(r["evalSteps"], r["valLoss"], color=BLUE, ls="--", lw=1, alpha=0.85, label="Held out (3)" if i == 0 else None)
        ax.set_ylabel("Loss (nats)", fontsize=16)
        ax.tick_params(labelsize=18)
        ax.grid(alpha=0.2)
        if index == 0:
            ax.set_title("Healthy variation: steps 500–1,000", loc="left", fontsize=16)
            ax.set_xlim(500, 1000)
            ax.set_ylim(2.24, 2.72)
            ax.plot(steps, band["mean"], color=GREEN, lw=1.5)
            continue
        bug = ("no_causal_mask", "softmax_wrong_dim", "no_zero_grad")[index - 1]
        title = ("No mask: access to later values", "Wrong axis: later queries\nin the denominator", "No zero_grad: carried\ngradient buffer")[
            index - 1
        ]
        ax.set_title(title, loc="left", fontsize=16)
        for r in [r for r in receipt["runs"] if r["bug"] == bug]:
            ax.plot(r["evalSteps"], r["valLoss"], color=RED, lw=1.2, alpha=0.8)
            row = next(x for x in receipt["bugs"][bug]["perSeed"] if x["seed"] == r["seed"])
            if row["flag"]:
                step = row["flag"]["step"]
                ax.scatter([step], [r["valLoss"][r["evalSteps"].index(step)]], s=27, color=RED, zorder=5)
        ax.set_xlim(0, 1000)
        if index < 3:
            ax.set_yscale("log")
            ax.set_ylim(0.01, 10)
            ax.set_yticks([0.01, 0.1, 1, 10], labels=["0.01", "0.1", "1", "10"])
        else:
            ax.set_ylim(2.2, 8.7)
        ax.plot(steps, band["mean"], color=GREEN, lw=1.5)
    axes[-1].set_xlabel("Training step (evaluated every 50)", fontsize=15)
    fig.get_layout_engine().set(h_pad=0.12)
    return export(fig, 2, out)


def intervals(receipt: dict, out: Path) -> dict:
    band = receipt["healthy"]["band"]
    ci = [band["ciLow"][-1], band["ciHigh"][-1]]
    pi = [band["piLow"][-1], band["piHigh"][-1]]
    controls = [r for r in receipt["runs"] if r["runId"].startswith("control-")]
    fig, ax = plt.subplots(figsize=(5.6, 3.5), layout="constrained")
    ax.axvspan(*pi, color=GREEN, alpha=0.10)
    ax.axvspan(*ci, color=GREEN, alpha=0.25)
    ax.plot(pi, [4.2, 4.2], color=GREEN, linewidth=6, solid_capstyle="butt")
    ax.plot(ci, [3.3, 3.3], color=INK, linewidth=6, solid_capstyle="butt")
    ax.plot([band["mean"][-1]], [3.3], "o", color="white", markersize=4)
    for i, r in enumerate(controls):
        value = r["finalValLoss"]
        ax.plot([value], [2.3 - i * 0.8], "D", color=BLUE, markersize=7)
        ax.annotate(f"{value:.4f}", (value, 2.3 - i * 0.8), xytext=(7, 0), textcoords="offset points", va="center", fontsize=15)
        assert pi[0] < value < pi[1]
    assert sum(not ci[0] < r["finalValLoss"] < ci[1] for r in controls) == 2
    ax.set_yticks([4.2, 3.3, 2.3, 1.5, 0.7], labels=["New-run PI", "Mean CI", "Seed 10", "Seed 11", "Seed 12"])
    ax.set(xlim=(2.244, 2.286), ylim=(0.2, 4.8), xlabel="Final validation loss (nats)")
    ax.set_xticks([2.25, 2.26, 2.27, 2.28])
    ax.set_title("Two controls outside mean CI,\nall inside PI", loc="left", fontsize=17, weight="bold")
    ax.spines[["left", "right", "top"]].set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=16)
    ax.tick_params(axis="x", labelsize=16)
    ax.set_xlabel("Final validation loss (nats)", fontsize=16)
    ax.grid(axis="x", alpha=0.2)
    return export(fig, 3, out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    raw = RECEIPT.read_bytes()
    receipt = json.loads(raw)
    manifest = {
        "generator": "tinygpt_figures_v3.py",
        "source": RECEIPT.name,
        "sourceSha256": hashlib.sha256(raw).hexdigest(),
        "newTraining": False,
        "figures": {"1": matrix(args.output), "2": curves(receipt, args.output), "3": intervals(receipt, args.output)},
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
