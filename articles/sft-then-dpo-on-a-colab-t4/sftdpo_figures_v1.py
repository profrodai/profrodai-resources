"""P2 figures from the unchanged operator T4 aggregate receipt; no training or inferred item data.

Requires matplotlib and Pillow. PNG/SVG exports can be shared independently of the article.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
from sftdpo_mechanism_v1 import load_receipt

HERE = Path(__file__).resolve().parent
RECEIPT = HERE/"receipts/colab/sftdpo-full-20261003.json"
SLUG = "sft-then-dpo-on-a-colab-t4"
GREEN, BLUE, INK = "#206d59", "#305d99", "#242522"
plt.rcParams.update({"font.size": 14, "axes.spines.top": False, "axes.spines.right": False,
                     "svg.fonttype": "none", "svg.hashsalt": "profrod-p2-v1"})


def export(fig, n: int, out: Path) -> dict:
    stem = f"{SLUG}--figure-{n}"
    fig.savefig(out/f"{stem}.svg", bbox_inches="tight", facecolor="white", metadata={"Date": None})
    svg = out/f"{stem}.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines())+"\n")
    fig.savefig(out/f"{stem}.png", dpi=240, bbox_inches="tight", facecolor="white")
    with Image.open(out/f"{stem}.png") as im:
        im.convert("RGB").save(out/f"{stem}.webp", quality=95, method=6)
    plt.close(fig)
    return {e: hashlib.sha256((out/f"{stem}.{e}").read_bytes()).hexdigest() for e in ("svg", "png", "webp")}


def seeds(r: dict, out: Path) -> dict:
    fig, ax = plt.subplots(figsize=(5.6, 4.8), layout="constrained")
    a, b = [r["results"]["arms"][arm]["accuracyPerSeed"] for arm in ("sft", "dpo")]
    for seed, (x,y) in enumerate(zip(a,b)):
        ax.plot([100*x,100*y], [seed,seed], color=INK, lw=1.7)
        ax.scatter([100*x], [seed], color=GREEN, marker="o", s=70, label="SFT" if seed==0 else None, zorder=4)
        ax.scatter([100*y], [seed], color=BLUE, marker="D", s=55, label="DPO" if seed==0 else None, zorder=4)
        ax.text(100*x-0.14,seed-0.21,f"{100*x:.1f}",ha="right",fontsize=15,color=GREEN)
        ax.text(100*y+0.14,seed+0.21,f"{100*y:.1f}",ha="left",fontsize=15,color=BLUE)
    ax.set_yticks([0,1,2], labels=["Seed 0", "Seed 1", "Seed 2"])
    ax.set(xlim=(78,84), ylim=(-0.65,2.65), xlabel="Test accuracy (%)")
    ax.invert_yaxis()
    ax.set_title("Three paired training seeds",loc="left",fontsize=17,weight="bold")
    ax.legend(loc="lower right",frameon=False,ncol=2)
    ax.grid(axis="x",alpha=0.2)
    ax.tick_params(labelsize=16)
    fig.supxlabel("Same 1,000 test items; points have no error bars",fontsize=12)
    return export(fig,1,out)


def comparisons(r: dict, out: Path) -> dict:
    fig, axes = plt.subplots(4,1,figsize=(5.6,7.1),layout="constrained")
    names = [("dpo vs sft", "DPO − SFT"), ("trap-promptloss vs sft", "Prompt loss − SFT"),
             ("trap-sysprompt vs sft", "Added system prompt − SFT"), ("trap-nogenprompt vs sft", "No assistant opening − SFT")]
    for ax,(key,title) in zip(axes,names):
        c = r["results"]["comparisons"][key]
        lo,hi,d = [100*c[k] for k in ("lo", "hi", "diff")]
        ax.axvline(0,color=INK,lw=1,ls="--",alpha=0.6)
        ax.plot([lo,hi],[0,0],color=BLUE,lw=3)
        ax.scatter([d],[0],color=BLUE,s=45,zorder=3)
        ax.text(lo,0.36,f"{lo:+.2f}",ha="center",fontsize=14)
        ax.text(hi,0.36,f"{hi:+.2f}",ha="center",fontsize=14)
        ax.set_title(title,loc="left",fontsize=16)
        ax.set(xlim=(-4.7,2.2),ylim=(-0.65,0.8),yticks=[])
        ax.spines[["left", "top", "right"]].set_visible(False)
        ax.tick_params(labelsize=15)
    axes[-1].set_xlabel("Accuracy difference (percentage points)",fontsize=14)
    fig.suptitle("95% intervals over test items",fontsize=17,weight="bold")
    fig.supxlabel("Conditional on the three fixed training seeds",fontsize=13)
    return export(fig,2,out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    r = load_receipt(RECEIPT)
    manifest = {"generator":"sftdpo_figures_v1.py", "sourceSha256":hashlib.sha256(RECEIPT.read_bytes()).hexdigest(),
                "sourceScope":"Recorded aggregate T4 accuracies and paired item-bootstrap intervals. No raw item reconstruction or seed-bootstrap interval.",
                "figures":{"1":seeds(r,args.output), "2":comparisons(r,args.output)}}
    (args.output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")


if __name__ == "__main__":
    main()
