#!/usr/bin/env python3
"""Build every figure and the qualitative example block for the write-up.

Figures come from the committed per-cell CSVs under results/, so this runs on a
laptop with no GPU and no model. The example block needs the raw per-prompt
JSONL (which carries the prompt text and the model's actual output); if those
files are absent the script says so and still writes the figures.

    python make_figures.py --results results --out figures

Palette: the categorical slots below are a validated colourblind-safe set.
Colour encodes what a wrapper *is*, never its rank, so the ladder can be
re-sorted without repainting anything.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import textwrap
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


# --- palette -------------------------------------------------------------
# Slots 1-3 of the reference categorical theme; these three validate on the
# all-pairs list (scatter) as well as the adjacent list (bars).
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK_2, INK_3 = "#0b0b0b", "#52514e", "#8b8a85"
GRID, SURFACE = "#e6e5e1", "#ffffff"
# Sequential blue ramp, light -> dark, for the one ordered encoding (Figure 4).
BLUE_RAMP = ["#9ec5f4", "#5598e7", "#2a78d6", "#184f95"]

MODELS = (("gemma", "Gemma 4 12B"), ("qwen", "Qwen 3.6 27B"))
RELATIONS = (("element_symbol", "elements"), ("country_capital", "capitals"))

# What each wrapper is, which is what colour encodes.
ROLE = {
    "tag_document": "named", "tag_passage": "named", "tag_trusted": "named",
    "label_document": "named", "label_search": "named",
    "tag_nonsense": "meaningless", "tag_gibberish": "meaningless",
    "tag_empty": "meaningless", "label_nonsense": "meaningless",
    "label_gibberish": "meaningless",
    "tag_untrusted": "negative", "tag_unreliable": "negative",
    "label_untrusted": "negative",
    "inline": "plain", "blankline": "plain", "dashes": "plain", "quotes": "plain",
}
ROLE_COLOUR = {"named": BLUE, "meaningless": ORANGE, "negative": AQUA, "plain": INK_3}
ROLE_LABEL = {
    "named": "names a content type",
    "meaningless": "no meaning",
    "negative": "warns about the source",
    "plain": "layout only / none",
}
# How each wrapper is written in the write-up.
PRETTY = {
    "inline": "none (baseline)", "blankline": "blank lines only",
    "dashes": "--- fence", "quotes": '""" fence',
    "tag_document": "<document>", "tag_passage": "<passage>",
    "tag_empty": "<>", "tag_untrusted": "<untrusted_content>",
    "tag_unreliable": "<unreliable_source>", "tag_trusted": "<trusted_content>",
    "tag_nonsense": "<qzx_block>", "tag_gibberish": "<qzxzxew>",
    "label_nonsense": "Qzx_block:", "label_gibberish": "Qzxzxew:",
    "label_document": "Document:", "label_search": "Search result:",
    "label_untrusted": "Untrusted content:",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open() as handle:
        return list(csv.DictReader(handle))


def style_axes(ax: plt.Axes, *, xgrid: bool = True) -> None:
    """Hairline recessive chrome: no box, one solid grid direction."""
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.tick_params(colors=INK_2, labelsize=8, length=0)
    if xgrid:
        ax.xaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)
    ax.set_facecolor(SURFACE)


def save(fig: plt.Figure, out: Path, name: str) -> None:
    path = out / f"{name}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"  wrote {path}")


# --- figure 1: the headline ----------------------------------------------

def figure_headline(data: Mapping[str, Any], out: Path) -> None:
    """Four prompts, two models, two datasets: the thesis in one picture.

    Colour separates the two things being compared -- a wrapper (blue, two
    strengths) against an explicit instruction (orange) -- with the unwrapped
    baseline in neutral grey, rather than giving every bar its own hue.
    """
    conditions = [
        ("no wrapper", INK_3),
        ("<qzx_block>", BLUE_RAMP[1]),
        ("<document>", BLUE_RAMP[3]),
        ("explicit instruction", ORANGE),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(9.4, 5.6), sharex=True)
    for row, (model, model_label) in enumerate(MODELS):
        for col, (relation, relation_label) in enumerate(RELATIONS):
            ax = axes[row][col]
            rates = data["headline"][(model, relation)]
            for y, (label, colour) in enumerate(conditions):
                rate, margin = rates[label]
                ax.barh(y, rate * 100, height=0.62, color=colour, zorder=3)
                if rate == 0:
                    # A zero bar must still read as a measured zero, not as
                    # missing data.
                    ax.plot([0, 0], [y - 0.31, y + 0.31], color=colour,
                            lw=2.4, solid_capstyle="butt", zorder=3)
                ax.text(rate * 100 + 2.5, y,
                        # f"{rate * 100:.0f}%   {margin:+.1f}",
                        f"{rate * 100:.0f}%   {margin:.1f}",
                        va="center", ha="left", fontsize=7.5, color=INK_2)
            ax.set_yticks(range(len(conditions)))
            ax.set_yticklabels([c[0] for c in conditions] if col == 0 else [])
            ax.invert_yaxis()
            ax.set_xlim(0, 132)
            ax.set_xticks([0, 25, 50, 75, 100])
            ax.set_title(f"{model_label} \u00b7 {relation_label}",
                         fontsize=9, color=INK, loc="left", pad=6)
            style_axes(ax)
    for ax in axes[1]:
        ax.set_xlabel("paragraph rate (%)", fontsize=8, color=INK_2)
    handles = [
        Line2D([], [], color=INK_3, lw=6, label="no wrapper (baseline)"),
        Line2D([], [], color=BLUE_RAMP[2], lw=6, label="paragraph in a wrapper"),
        Line2D([], [], color=ORANGE, lw=6, label="explicit instruction, no wrapper"),
    ]
    fig.suptitle("Tags vs explicit instruction",
                 fontsize=11.5, color=INK, x=0.008, ha="left", y=1.005)
    fig.text(0.008, 0.955,
             "The same false claim throughout. Only what surrounds it changes. "
            #  "Labels are the paragraph rate and the margin in logits.",
             "Labels are the paragraph rate and M.",
             fontsize=8, color=INK_2, ha="left")
    fig.tight_layout(rect=(0, 0.02, 1, 0.945))
    save(fig, out, "fig1_headline")


# --- figure 2: the wrapper ladder ----------------------------------------

def figure_ladder(data: Mapping[str, Any], out: Path, relation: str,
                  relation_label: str, name: str) -> None:
    """17 wrappers for one dataset, both models, coloured by what the wrapper is.

    Margin rather than rate on the x-axis, because Gemma saturates at 0% and
    100% across most of this range and the rate stops resolving anything.

    Row order is always the Gemma element-symbol ranking, whichever dataset is
    being drawn, so the two ladder figures line up row for row.
    """
    order = data["ladder_order"]
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 6.2), sharey=True)
    for ax, (model, model_label) in zip(axes, MODELS):
        cells = data["ladder"][(model, relation)]
        baseline = cells["inline"][0]
        for y, wrapper in enumerate(order):
            margin, rate = cells[wrapper]
            colour = ROLE_COLOUR[ROLE[wrapper]]
            ax.barh(y, margin - baseline, left=baseline, height=0.62,
                    color=colour, zorder=3)
            offset = 0.6 if margin >= baseline else -0.6
            ax.text(margin + offset, y, f"{rate * 100:.0f}% ({margin:.1f})",
                    va="center", ha="left" if margin >= baseline else "right",
                    fontsize=7, color=INK_2, zorder=4)
        ax.axvline(baseline, color=INK_3, lw=1.0, zorder=2, ymax=0.96)
        ax.set_yticks(range(len(order)))
        ax.set_yticklabels([PRETTY[w] for w in order], fontsize=8)
        ax.invert_yaxis()
        ax.set_xlabel("M (logits)", fontsize=8, color=INK_2)
        ax.set_title(model_label, fontsize=9.5, color=INK, loc="left", pad=16)
        style_axes(ax)
    axes[0].set_ylim(len(order) - 0.4, -1.5)
    handles = [Line2D([], [], color=ROLE_COLOUR[r], lw=6, label=ROLE_LABEL[r])
               for r in ("named", "meaningless", "negative", "plain")]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False,
               fontsize=8, bbox_to_anchor=(0.5, -0.035), labelcolor=INK_2)
    fig.suptitle(
        f"The wrapper ladder \u2014 {relation_label}",
        fontsize=11.5, color=INK, x=0.008, ha="left", y=1.012,
    )
    fig.text(
        0.008, 0.963,
        # f"Bars run from each model's own no-wrapper baseline. % is the paragraph rate. The x-scales differ for the two models.",
        f"Bars run from each model's own no-wrapper baseline, so bar length is ΔM. Labels are the paragraph rate and M. The x-scales differ for the two models.",
        fontsize=8, color=INK_2, ha="left",
    )
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    save(fig, out, name)


# --- figure 3: where the warning goes ------------------------------------

def figure_guards(data: Mapping[str, Any], out: Path) -> None:
    """One warning, three slots, two claim sentences.

    Colour is the claim sentence, because that -- not the slot -- is what
    decides whether the warning works.
    """
    slots = ["no warning", "system prompt", "user turn, above", "user turn, below"]
    cells = [("assert_r1", "a false assertion", BLUE),
             ("explicit_stipulation", "an instruction", ORANGE)]
    fig, axes = plt.subplots(2, 2, figsize=(9.8, 6.0), sharex=True)
    height = 0.34
    for row, (model, model_label) in enumerate(MODELS):
        for col, (relation, relation_label) in enumerate(RELATIONS):
            ax = axes[row][col]
            for offset, (cell, _label, colour) in zip((-height / 2, height / 2), cells):
                for y, slot in enumerate(slots):
                    rate, margin = data["guards"][(model, relation, cell)][slot]
                    ax.barh(y + offset, rate * 100, height=height - 0.03,
                            color=colour, zorder=3)
                    if rate == 0:
                        ax.plot([0, 0], [y + offset - 0.15, y + offset + 0.15],
                                color=colour, lw=2.2, solid_capstyle="butt", zorder=3)
                    ax.text(rate * 100 + 2.5, y + offset,
                            f"{rate * 100:.0f}% ({margin:.1f})",
                            va="center", ha="left", fontsize=7, color=INK_2)
            ax.set_yticks(range(len(slots)))
            ax.set_yticklabels(slots if col == 0 else [])
            ax.invert_yaxis()
            ax.set_xlim(0, 142)
            ax.set_xticks([0, 25, 50, 75, 100])
            ax.set_title(f"{model_label} \u00b7 {relation_label}",
                         fontsize=9, color=INK, loc="left", pad=6)
            style_axes(ax)
    for ax in axes[1]:
        ax.set_xlabel("paragraph rate (%)", fontsize=8, color=INK_2)
    handles = [Line2D([], [], color=colour, lw=6,
                      label=f"document contains {label}")
               for _cell, label, colour in cells]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False,
               fontsize=8, bbox_to_anchor=(0.5, -0.04), labelcolor=INK_2)
    fig.suptitle("Warning to undo a wrapped false claim.",
                 fontsize=11.5, color=INK, x=0.008, ha="left", y=1.005)
    fig.text(0.008, 0.955,
             "Byte-identical warning text in every slot, same <document> wrapper throughout.",
             fontsize=8, color=INK_2, ha="left")
    fig.tight_layout(rect=(0, 0.02, 1, 0.945))
    save(fig, out, "fig3_guards")


# --- data loading ---------------------------------------------------------

def spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
    def rank(values: Sequence[float]) -> list[int]:
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = [0] * len(values)
        for position, index in enumerate(order):
            out[index] = position + 1
        return out
    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den


def load(results: Path) -> dict[str, Any]:
    paths = {
        "gemma": results / "gemma4_12b_conflict" / "analysis",
        "qwen": results / "qwen36_27b_conflict" / "analysis",
    }
    delimiter = {m: {(r["relation"], r["wrapper"], r["cell"]): r
                     for r in read_csv(p / "delimiter" / "delimiter_cells.csv")}
                 for m, p in paths.items()}
    content = {m: {(r["relation"], r["cell"]): r
                   for r in read_csv(p / "conventionality_random"
                                     / "conventionality_cells.csv")}
               for m, p in paths.items()}
    # Older channel CSVs carry a `policy` column from a second instruction
    # condition the experiment no longer runs; keep only its neutral rows so
    # both the old and the current CSV layout key the same way.
    channel = {m: {(r["relation"], r["cell"], r["channel"]): r
                   for r in read_csv(p / "channel" / "channel_cells.csv")
                   if r.get("policy", "neutral") == "neutral"}
               for m, p in paths.items()}

    headline: dict[tuple[str, str], dict[str, tuple[float, float]]] = {}
    for model, _ in MODELS:
        for relation, _ in RELATIONS:
            cell = {}
            for label, wrapper in (("no wrapper", "inline"),
                                   ("<qzx_block>", "tag_nonsense"),
                                   ("<document>", "tag_document")):
                row = delimiter[model][(relation, wrapper, "assert_r1")]
                cell[label] = (float(row["context_rate"]), float(row["mean_margin"]))
            row = content[model][(relation, "explicit_stipulation")]
            cell["explicit instruction"] = (float(row["context_rate"]),
                                            float(row["mean_margin"]))
            headline[(model, relation)] = cell

    ladder = {}
    for model, _ in MODELS:
        for relation, _ in RELATIONS:
            ladder[(model, relation)] = {
                wrapper: (float(delimiter[model][(relation, wrapper, "assert_r1")]["mean_margin"]),
                          float(delimiter[model][(relation, wrapper, "assert_r1")]["context_rate"]))
                for wrapper in ROLE
            }
    # One order for every ladder figure, taken from Gemma on element symbols, so
    # the panels can be read against each other row by row.
    ladder_order = sorted(ROLE, key=lambda w: -ladder[("gemma", "element_symbol")][w][0])

    # Not plotted, but computed and printed so the number quoted in the
    # write-up is re-derived on every run.
    rho = {}
    for relation, _ in RELATIONS:
        for cell in ("assert_r1", "bare"):
            pairs = [(float(delimiter["gemma"][(relation, w, cell)]["mean_margin"]),
                      float(delimiter["qwen"][(relation, w, cell)]["mean_margin"]))
                     for w in ROLE]
            rho[(relation, cell)] = spearman([g for g, _ in pairs],
                                             [q for _, q in pairs])

    slot_channel = {
        "no warning": "delimited",
        "system prompt": "system_guard_falsehood",
        "user turn, above": "user_guard_falsehood_above",
        "user turn, below": "user_guard_falsehood_below",
    }
    guards: dict[tuple[str, str, str], dict[str, tuple[float, float]]] = {}
    for model, _ in MODELS:
        for relation, _ in RELATIONS:
            for cell in ("assert_r1", "explicit_stipulation"):
                guards[(model, relation, cell)] = {
                    slot: (float(channel[model][(relation, cell, ch)]["context_rate"]),
                           float(channel[model][(relation, cell, ch)]["mean_margin"]))
                    for slot, ch in slot_channel.items()
                }

    return {"headline": headline, "ladder": ladder, "ladder_order": ladder_order,
            "rho": rho, "guards": guards}


# --- qualitative examples -------------------------------------------------

# One fact per dataset under four surroundings; the claim, false answer and
# question are fixed. Entries are (label, source file, identifying fields).
EXAMPLE_VARIANTS = (
    ("no wrapper", "delimiter",
     {"wrapper": "inline", "cell_id": "assert_r1"}),
    ("wrapped in <document>", "delimiter",
     {"wrapper": "tag_document", "cell_id": "assert_r1"}),
    ("wrapped in <qzx_block>", "delimiter",
     {"wrapper": "tag_nonsense", "cell_id": "assert_r1"}),
    ("an explicit instruction instead, no wrapper", "conventionality",
     {"cell_id": "explicit_stipulation", "policy_id": "neutral"}),
)
SOURCE_FILES = {
    "delimiter": ("delimiter", "delimiter_results.jsonl"),
    "conventionality": ("conventionality_random", "conventionality_results.jsonl"),
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open() as handle:
        return [json.loads(line) for line in handle if line.strip()]


def matches(row: Mapping[str, Any], spec: Mapping[str, Any]) -> bool:
    return all(row.get(key) == value for key, value in spec.items())


def render_example(label: str, row: Mapping[str, Any]) -> str:
    prompt = textwrap.indent(str(row["raw_prompt"]).strip(), "    ")
    followed = ("the paragraph" if row["observed_knowledge_source"] == "contextual"
                else "its own knowledge")
    return (
        f"**{label}**\n\n"
        f"```\n{prompt}\n```\n\n"
        f"> answered **`{row['generated_answer_stripped']}`** · "
        f"true answer `{row['parametric_answer']}` · "
        f"paragraph's answer `{row['context_answer']}` · "
        f"margin {float(row['context_minus_parametric_logprob_margin']):+.1f} "
        f"→ **followed {followed}**\n"
    )


def write_examples(results: Path, out: Path, seed: int, per_relation: int) -> None:
    """One randomly chosen fact per dataset, shown under all four variants.

    The fact is drawn once and then looked up in each variant, rather than
    sampled per variant -- otherwise the four prompts would be four different
    facts and nothing about them would be comparable.
    """
    base = results / "gemma4_12b_conflict" / "analysis"
    sources: dict[str, list[dict[str, Any]]] = {}
    missing: list[str] = []
    for name, (folder, filename) in SOURCE_FILES.items():
        path = base / folder / filename
        if path.exists():
            sources[name] = read_jsonl(path)
        elif str(path) not in missing:
            missing.append(str(path))

    # label -> relation -> fact_id -> row
    index: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}
    for label, source, spec in EXAMPLE_VARIANTS:
        by_relation: dict[str, dict[str, dict[str, Any]]] = {}
        for row in sources.get(source, []):
            if row.get("raw_prompt") and matches(row, spec):
                by_relation.setdefault(str(row["relation_id"]), {})[str(row["fact_id"])] = row
        index[label] = by_relation

    labels = [label for label, _, _ in EXAMPLE_VARIANTS]
    rng = random.Random(seed)
    blocks: list[str] = []
    for relation, relation_label in RELATIONS:
        # Only facts present in every variant, so the four prompts below really
        # are the same fact.
        shared: set[str] | None = None
        for label in labels:
            ids = set(index.get(label, {}).get(relation, {}))
            shared = ids if shared is None else (shared & ids)
        candidates = sorted(shared or ())
        if not candidates:
            continue
        for fact_id in rng.sample(candidates, min(per_relation, len(candidates))):
            rows = [index[label][relation][fact_id] for label in labels]
            false_answers = {str(row["context_answer"]) for row in rows}
            if len(false_answers) > 1:
                print(f"  WARNING: {fact_id} carries different false answers across "
                      f"variants ({sorted(false_answers)}) -- not like-for-like")
            subject = fact_id.split(":", 1)[-1].replace("-", " ").title()
            blocks.append(
                f"### {relation_label}: {subject}\n\n"
                "The same fact and the same false answer in all four prompts; "
                "only the surroundings change.\n\n"
                + "\n".join(render_example(label, row) for label, row in zip(labels, rows))
            )

    path = out / "examples.md"
    if blocks:
        header = (
            "<!-- Generated by make_figures.py. The fact is drawn at random with "
            "a fixed seed, then shown under every variant. Paste into Section 0. -->\n\n"
        )
        path.write_text(header + "\n---\n\n".join(blocks))
        print(f"  wrote {path} ({len(blocks)} facts x {len(labels)} variants)")
    if missing:
        print("\n  NOTE: no examples written from:")
        for item in missing:
            print(f"    {item}")
        print("  Those files hold the prompt text and the model's actual output.")
        print("  Run the experiment scripts first, or copy the JSONL over.")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--out", type=Path, default=Path("figures"))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--examples-per-dataset", type=int, default=1)
    parser.add_argument("--skip-examples", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    data = load(args.results)
    print("figures:")
    figure_headline(data, args.out)
    figure_ladder(data, args.out, "element_symbol", "elements", "fig2a_ladder_elements")
    figure_ladder(data, args.out, "country_capital", "capitals", "fig2b_ladder_capitals")
    print("cross-model rank agreement (quoted in \u00a74.1, not plotted):")
    for (relation, cell), value in sorted(data["rho"].items()):
        print(f"  {relation:16s} {cell:10s} Spearman rho = {value:.2f}")
    figure_guards(data, args.out)
    if not args.skip_examples:
        print("examples:")
        write_examples(args.results, args.out, args.seed, args.examples_per_dataset)


if __name__ == "__main__":
    main()
