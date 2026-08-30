#!/usr/bin/env python3
"""Build every figure and the random-example block from committed result files.

Nothing here re-runs a model or re-derives a claim: each figure reads the same
`*_results.jsonl` the write-up quotes, so a figure cannot disagree with the
table beside it. Paired contrasts are recomputed here rather than read out of
the summary JSONs, for the same reason.

    python make_figures.py --results results --out figures

Figures
-------
fig1_wrapper_ladder   thirteen wrappers around one unchanged paragraph.
fig2_warning_channel  five ways of warning the model off, one baseline.
fig3_cross_model      the same ladder in Gemma 4 and Qwen 3.6.
fig4_speech_act       the stipulability account, and its falsification.

figures/random_examples.md holds prompts ordered by a hash of `sample_id`,
drawn from the delimiter run -- the experiment the write-up leads with.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# --- palette -------------------------------------------------------------
# Light-surface steps from the validated reference palette. Two categorical
# slots (the two relations) plus a de-emphasis gray for reference marks; the
# sign of a bar carries polarity, so no diverging ramp is needed.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#8a8984"
GRID = "#e4e3df"
S1 = "#2a78d6"  # blue   -- element symbols
S2 = "#eb6834"  # orange -- country capitals
ANCHOR = "#4a3aa7"  # violet -- the meaningless-tag reference

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.size": 10.5,
        "font.family": "DejaVu Sans",
        "text.color": INK,
        "axes.labelcolor": INK_2,
        "axes.edgecolor": GRID,
        "xtick.color": INK_2,
        "ytick.color": INK_2,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
    }
)

RELATIONS = [("element_symbol", "element symbols", S1), ("country_capital", "country capitals", S2)]


# --- data helpers --------------------------------------------------------


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open() as handle:
        return [json.loads(line) for line in handle if line.strip()]


def live(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [r for r in rows if r.get("cell_id") != "screen"]


def paired(
    rows: Sequence[Mapping[str, Any]],
    treatment: Callable[[Mapping[str, Any]], bool],
    control: Callable[[Mapping[str, Any]], bool],
) -> tuple[float, int]:
    """Mean within-fact difference in margin. Facts missing either side drop."""
    a = {r["fact_id"]: r["context_minus_parametric_logprob_margin"] for r in rows if treatment(r)}
    b = {r["fact_id"]: r["context_minus_parametric_logprob_margin"] for r in rows if control(r)}
    keys = sorted(set(a) & set(b))
    if not keys:
        return float("nan"), 0
    return float(np.mean([a[k] - b[k] for k in keys])), len(keys)


def cluster_ci(
    rows: Sequence[Mapping[str, Any]],
    treatment: Callable[[Mapping[str, Any]], bool],
    control: Callable[[Mapping[str, Any]], bool],
    replicates: int = 2000,
    seed: int = 20260816,
) -> tuple[float, float, float]:
    a = {r["fact_id"]: r["context_minus_parametric_logprob_margin"] for r in rows if treatment(r)}
    b = {r["fact_id"]: r["context_minus_parametric_logprob_margin"] for r in rows if control(r)}
    keys = sorted(set(a) & set(b))
    if not keys:
        return float("nan"), float("nan"), float("nan")
    deltas = np.array([a[k] - b[k] for k in keys])
    rng = np.random.default_rng(seed)
    draws = [deltas[rng.integers(0, len(keys), len(keys))].mean() for _ in range(replicates)]
    return float(deltas.mean()), float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def repaired_label(row: Mapping[str, Any]) -> str:
    """Undo the Gemma thought-channel leak before classifying a generation.

    Some runs emit the answer with a stray character glued on (`-Zn`, `-W-`,
    `aMajuro`). The margin is teacher-forced and unaffected, but the greedy
    label is not. Accept a repair only on an EXACT match to a candidate, so the
    rule can never invent an answer; anything else stays unresolved and is
    excluded from the rate rather than counted against either side.
    """
    raw = str(row["generated_answer_stripped"])
    options = [("contextual", str(row["context_answer"])), ("parametric", str(row["parametric_answer"]))]
    for label, answer in options:
        if raw == answer:
            return label
    trimmed = raw.strip().strip("-+. ").strip()
    for label, answer in options:
        if trimmed == answer:
            return label
    if len(trimmed) > 1:
        for label, answer in options:
            if trimmed[1:] == answer:
                return label
    return "unresolved"


def paragraph_rate(rows: Sequence[Mapping[str, Any]], repair: bool = False) -> float:
    """Share of answers taken from the paragraph, i.e. the false answer."""
    if not rows:
        return float("nan")
    if not repair:
        return float(np.mean([r["observed_knowledge_source"] == "contextual" for r in rows]))
    labels = [repaired_label(r) for r in rows]
    kept = [l for l in labels if l != "unresolved"]
    return float(np.mean([l == "contextual" for l in kept])) if kept else float("nan")


def grouped_barh(
    ax: Any,
    labels: Sequence[str],
    series: Sequence[tuple[str, str, Sequence[float]]],
    bar_h: float = 0.36,
) -> None:
    """Horizontal grouped bars, thin marks, 2px surface gap between neighbours."""
    y = np.arange(len(labels))
    offset = bar_h / 2 + 0.012
    # The y-axis is inverted below, so the FIRST series must be placed at the
    # smaller coordinate to end up drawn on top of its group.
    for index, (name, color, values) in enumerate(series):
        shift = offset if index == 0 else -offset
        ax.barh(
            y - shift,
            values,
            height=bar_h,
            color=color,
            label=name,
            linewidth=0.8,
            edgecolor=SURFACE,
            zorder=3,
        )
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    # Guard the flip: with sharey=True a second call on a linked axis would undo
    # the first and silently reverse the row order.
    low, high = ax.get_ylim()
    if low < high:
        ax.invert_yaxis()
    ax.axvline(0, color=INK_2, linewidth=1.0, zorder=4)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)


# --- figure 1: the wrapper ladder ---------------------------------------

WRAPPER_LABEL = {
    "inline": "no wrapper",
    "blankline": "blank lines only",
    "quotes": '"""  fence',
    "dashes": "---  fence",
    "tag_untrusted": "<untrusted_content>",
    "tag_unreliable": "<unreliable_source>",
    "tag_nonsense": "<qzx_block>",
    "tag_empty": "<>  (no name)",
    "label_document": "Document:",
    "label_untrusted": "Untrusted content:",
    "label_search": "Search result:",
    "tag_passage": "<passage>",
    "tag_document": "<document>",
    "tag_trusted": "<trusted_content>",
}
LADDER_ORDER = [
    "blankline",
    "tag_untrusted",
    "label_untrusted",
    "quotes",
    "dashes",
    "tag_unreliable",
    "tag_empty",
    "tag_nonsense",
    "label_document",
    "label_search",
    "tag_passage",
    "tag_document",
    "tag_trusted",
]


def tag_runs(results: Path, model: str) -> list[Mapping[str, Any]]:
    """Every `analysis/delimiter*` run, each row tagged with the run it came from.

    The committed results predate the consolidation and live in two directories
    (`delimiter`, `delimiter_valence`) because the valence wrappers were added
    in a second pass; `cmds.sh` now writes one. Both layouts load here, and the
    run tag is what stops a wrapper from one run being paired against the
    `inline` of another -- those are separate GPU runs, and while their cell
    means agree to <=0.07 logits, joining them is an assumption rather than a
    measurement.
    """
    base = results / model / "analysis"
    out: list[Mapping[str, Any]] = []
    for directory in sorted(base.glob("delimiter*")):
        for row in live(load_jsonl(directory / "delimiter_results.jsonl")):
            out.append({**row, "_run": directory.name})
    return out


def wrapper_delta(rows: Sequence[Mapping[str, Any]], relation: str, wrapper: str, cell: str = "assert_r1") -> float:
    """Paired against the `inline` scored in the SAME run as this wrapper."""
    for run_tag in sorted({str(r.get("_run")) for r in rows}):
        subset = [
            r
            for r in rows
            if r.get("_run") == run_tag and r["relation_id"] == relation and r["cell_id"] == cell
        ]
        if any(r["wrapper"] == wrapper for r in subset):
            delta, _ = paired(subset, lambda r: r["wrapper"] == wrapper, lambda r: r["wrapper"] == "inline")
            return delta
    return float("nan")


def figure_wrapper_ladder(results: Path, out: Path) -> None:
    rows = tag_runs(results, "gemma4_12b_conflict")
    if not rows:
        print("skip fig1: no delimiter results")
        return
    present = {r["wrapper"] for r in rows}
    order = [w for w in LADDER_ORDER if w in present]
    labels = [WRAPPER_LABEL[w] for w in order]
    series = []
    for relation, name, color in RELATIONS:
        series.append((name, color, [wrapper_delta(rows, relation, w) for w in order]))

    fig, ax = plt.subplots(figsize=(10.6, 6.6))
    grouped_barh(ax, labels, series)

    anchor = float(np.mean([wrapper_delta(rows, r, "tag_nonsense") for r, _, _ in RELATIONS]))
    ax.axvline(anchor, color=ANCHOR, linewidth=1.6, linestyle=(0, (5, 3)), zorder=5)
    ax.annotate(
        "<qzx_block>: a tag that names nothing",
        xy=(anchor - 1.2, -0.78),
        ha="right",
        va="center",
        fontsize=9.5,
        color=ANCHOR,
    )

    # The rate, printed beside each row. Without it a reader has to translate
    # logits into behaviour in their head, and the two numbers in the text are
    # measured against different baselines -- this column is on neither, it is
    # just what the model did.
    rate_x = 54.5
    ax.annotate(
        "answers taken\nfrom the paragraph",
        xy=(rate_x, -0.95),
        ha="center",
        va="center",
        fontsize=9,
        color=INK_2,
    )
    offset = 0.36 / 2 + 0.012
    for index, (relation, _, color) in enumerate(RELATIONS):
        shift = offset if index == 0 else -offset
        for row, wrapper in enumerate(order):
            cell = [
                r
                for r in rows
                if r["relation_id"] == relation
                and r["cell_id"] == "assert_r1"
                and r["wrapper"] == wrapper
            ]
            ax.annotate(
                f"{100 * paragraph_rate(cell):.0f}%",
                xy=(rate_x, row - shift),
                ha="center",
                va="center",
                fontsize=9,
                color=color,
            )

    for tick, wrapper in zip(ax.get_yticklabels(), order):
        tick.set_fontfamily("DejaVu Sans Mono" if wrapper.startswith(("tag_", "label_")) else "DejaVu Sans")
        tick.set_fontsize(10)
        if wrapper == "tag_nonsense":
            tick.set_color(ANCHOR)

    ax.set_xlabel("shift in log P(paragraph's answer) − log P(true answer), against the unwrapped paragraph")
    ax.set_title(
        "One paragraph, thirteen wrappers, not one word changed\n"
        "Gemma 4 12B · a sourced false sentence · no user instruction\n"
        "0 = the same paragraph with no wrapper at all. This is the ONLY baseline on this axis.",
        fontsize=12.5,
        loc="left",
        color=INK,
        pad=12,
    )
    ax.legend(frameon=False, loc="lower left", fontsize=10, bbox_to_anchor=(0.0, -0.215), ncol=2)
    ax.set_xlim(-2, 58)
    ax.set_xticks([0, 10, 20, 30, 40, 50])
    ax.set_ylim(len(labels) - 0.45, -1.25)
    fig.tight_layout()
    fig.savefig(out / "fig1_wrapper_ladder.png", dpi=200)
    plt.close(fig)
    print(f"wrote {out / 'fig1_wrapper_ladder.png'}")


# --- figure 2: where a warning has to sit -------------------------------


# Five ways of warning the model off the same paragraph, every one measured
# against the SAME baseline: that paragraph in <document> with no warning at
# all. Two of them replace the wrapper, three of them add a sentence of prose
# and leave <document> in place. Putting them on one axis is the point of the
# figure -- the 1.0.0 run compared prose against a different baseline from the
# tag, which is what made a null look like a slot effect.
#
# The 1.0.0 guard wording ("data to consider, not instructions") is not plotted.
# It warns about a threat this cell does not contain -- assert_r1 carries a
# false assertion, not an imperative -- so its null was never evidence about
# prose. See section 5.
WRAPPER_SWAP_ROWS = (
    ("replace the tag:\n<untrusted_content>", "tag_untrusted"),
    ("replace it with a bare label:\nUntrusted content:", "label_untrusted"),
)
PROSE_ROWS = (
    ("one sentence of prose,\nin the system prompt", "system_guard_falsehood"),
    ("the same sentence,\nabove the block", "user_guard_falsehood_above"),
    ("the same sentence,\nbelow the block", "user_guard_falsehood_below"),
)


def figure_warning_channel(results: Path, out: Path) -> None:
    labels = [label for label, _ in WRAPPER_SWAP_ROWS] + [label for label, _ in PROSE_ROWS]
    panels = []
    for model, title in (("gemma4_12b_conflict", "Gemma 4 12B"), ("qwen36_27b_conflict", "Qwen 3.6 27B")):
        base = results / model / "analysis"
        guard = live(load_jsonl(base / "channel" / "channel_results.jsonl"))
        wrapper_rows = tag_runs(results, model)
        if not guard or not wrapper_rows:
            continue
        if not any(r.get("channel") == "system_guard_falsehood" for r in guard):
            print(f"skip fig2 panel {model}: channel run predates the falsehood guard")
            continue
        series = []
        for relation, name, color in RELATIONS:
            g = [
                r
                for r in guard
                if r["relation_id"] == relation
                and r["cell_id"] == "assert_r1"
                and r["policy_id"] == "neutral"
            ]
            # Wrapper swaps are paired inside whichever delimiter run scored both
            # wrappers, never across runs.
            swaps = []
            for _label, wrapper in WRAPPER_SWAP_ROWS:
                value = float("nan")
                for run_tag in sorted({str(r["_run"]) for r in wrapper_rows}):
                    subset = [
                        r
                        for r in wrapper_rows
                        if r["_run"] == run_tag
                        and r["relation_id"] == relation
                        and r["cell_id"] == "assert_r1"
                    ]
                    if {r["wrapper"] for r in subset} >= {wrapper, "tag_document"}:
                        value = paired(
                            subset,
                            lambda r, w=wrapper: r["wrapper"] == w,
                            lambda r: r["wrapper"] == "tag_document",
                        )[0]
                        break
                swaps.append(value)
            prose = [
                paired(
                    g,
                    lambda r, ch=channel: r["channel"] == ch,
                    lambda r: r["channel"] == "delimited",
                )[0]
                for _label, channel in PROSE_ROWS
            ]
            series.append((name, color, swaps + prose))
        panels.append((title, series))
    if not panels:
        print("skip fig2: needs a channel run with the falsehood guard")
        return

    fig, axes = plt.subplots(1, len(panels), figsize=(12.4, 4.6), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, (title, series) in zip(axes, panels):
        grouped_barh(ax, labels, series, bar_h=0.33)
        span = max(abs(v) for _, _, values in series for v in values if np.isfinite(v))
        ax.set_xlim(-span * 1.32, span * 0.30)
        ax.set_ylim(len(labels) - 0.4, -0.75)
        ax.set_title(title, fontsize=12, loc="left", color=INK, pad=8)
        # The two wrapper swaps and the three prose guards are different kinds
        # of intervention; the rule keeps a reader from reading the five as one
        # ordered ladder.
        ax.axhline(len(WRAPPER_SWAP_ROWS) - 0.5, color=GRID, linewidth=1.0, zorder=1)
        offset = 0.33 / 2 + 0.012
        for index, (_, _, values) in enumerate(series):
            shift = offset if index == 0 else -offset
            for row, value in enumerate(values):
                ax.annotate(
                    f"{value:+.1f}",
                    xy=(value + (span * 0.022 if value >= 0 else -span * 0.022), row - shift),
                    ha="left" if value >= 0 else "right",
                    va="center",
                    fontsize=9,
                    color=INK_2,
                )
        ax.set_xlabel("shift against the same paragraph\nin <document> with no warning")
    # Every bar in this figure is negative and long, so there is no empty corner
    # inside the axes; the legend sits under the title instead of over a row.
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        legend_labels,
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(0.006, 0.885),
        ncol=2,
        fontsize=9.5,
    )
    fig.suptitle(
        "Five ways to warn the model off. All five work, and the prose works best.\n"
        "Note the two panels use different scales; Qwen's whole effect is about a fifth of Gemma's.",
        fontsize=12.5,
        x=0.006,
        ha="left",
        color=INK,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.83))
    fig.savefig(out / "fig2_warning_channel.png", dpi=200)
    plt.close(fig)
    print(f"wrote {out / 'fig2_warning_channel.png'}")


# --- figure 3: the same ladder in two models ----------------------------

# Top to bottom: most trustworthy-sounding label first, so a monotone ladder
# reads as a staircase and a broken one is visible at a glance.
# Sorted by Gemma's own effect at render time, so a shared ordering that breaks
# in the second panel is visible as a broken staircase rather than hidden by a
# hand-picked row order.
CROSS_ORDER = [w for w in LADDER_ORDER]


def figure_cross_model(results: Path, out: Path) -> None:
    panels = []
    for model, title in (
        ("gemma4_12b_conflict", "Gemma 4 12B"),
        ("qwen36_27b_conflict", "Qwen 3.6 27B"),
    ):
        rows = tag_runs(results, model)
        if any(r["wrapper"] == "tag_nonsense" for r in rows):
            panels.append((title, rows))
    if panels:
        reference = panels[0][1]
        CROSS_ORDER.sort(
            key=lambda w: -float(
                np.nanmean([wrapper_delta(reference, rel, w) for rel, _, _ in RELATIONS])
            )
        )
    if len(panels) < 2:
        print("skip fig3: needs delimiter_valence for both models")
        return

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 6.6), sharey=True)
    for ax, (title, rows) in zip(axes, panels):
        series = []
        for relation, name, color in RELATIONS:
            series.append(
                (name, color, [wrapper_delta(rows, relation, w) for w in CROSS_ORDER])
            )
        grouped_barh(ax, [WRAPPER_LABEL[w] for w in CROSS_ORDER], series)
        ax.set_title(title, fontsize=12, loc="left", color=INK, pad=8)
        ax.set_xlim(-6, 54)
        ax.set_ylim(len(CROSS_ORDER) - 0.45, -0.7)
        offset = 0.36 / 2 + 0.012
        for index, (_, _, values) in enumerate(series):
            shift = offset if index == 0 else -offset
            for row, value in enumerate(values):
                ax.annotate(
                    f"{value:+.1f}",
                    xy=(value + (0.8 if value >= 0 else -0.8), row - shift),
                    ha="left" if value >= 0 else "right",
                    va="center",
                    fontsize=8.5,
                    color=INK_2,
                )
        for tick in ax.get_yticklabels():
            tick.set_fontfamily("DejaVu Sans Mono")
            tick.set_fontsize(10)
    axes[0].legend(frameon=False, loc="lower left", fontsize=9.5, bbox_to_anchor=(0.0, -0.20), ncol=2)
    axes[0].set_xlabel("shift vs no wrapper (logits)")
    axes[1].set_xlabel("shift vs no wrapper (logits)")
    fig.suptitle(
        "The wrapper effect replicates; only the warning half of the ordering does",
        fontsize=12.5,
        x=0.008,
        ha="left",
        color=INK,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out / "fig3_cross_model.png", dpi=200)
    plt.close(fig)
    print(f"wrote {out / 'fig3_cross_model.png'}")


# --- figure 4: the speech-act effect and its falsification --------------


def act_effect(rows: Sequence[Mapping[str, Any]], relation: str, extra: Callable[[Mapping[str, Any]], bool] | None = None):
    keep = [
        r
        for r in rows
        if r["relation_id"] == relation
        and r.get("policy_id") == "neutral"
        and (extra is None or extra(r))
    ]
    by: dict[str, dict[str, float]] = collections.defaultdict(dict)
    for row in keep:
        by[row["fact_id"]][row["cell_id"]] = row["context_minus_parametric_logprob_margin"]
    need = ("stipulate_r1", "stipulate_r2", "assert_r1", "assert_r2")
    facts = [f for f, cells in by.items() if all(c in cells for c in need)]
    if not facts:
        return float("nan"), float("nan"), float("nan")
    values = np.array(
        [
            (by[f]["stipulate_r1"] + by[f]["stipulate_r2"]) / 2
            - (by[f]["assert_r1"] + by[f]["assert_r2"]) / 2
            for f in facts
        ]
    )
    rng = np.random.default_rng(20260816)
    draws = [values[rng.integers(0, len(facts), len(facts))].mean() for _ in range(2000)]
    return float(values.mean()), float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def figure_speech_act(results: Path, out: Path) -> None:
    conv = {
        model: live(
            load_jsonl(results / model / "analysis" / "conventionality_random" / "conventionality_results.jsonl")
        )
        for model in ("gemma4_12b_conflict", "qwen36_27b_conflict")
    }
    plaus = live(
        load_jsonl(results / "gemma4_12b_conflict" / "analysis" / "plausibility" / "plausibility_results.jsonl")
    )
    if not conv["gemma4_12b_conflict"] or not plaus:
        print("skip fig4: needs conventionality_random and plausibility")
        return

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.0))

    order = [
        ("element_symbol", "element symbol\n(stipulable)"),
        ("element_atomic_number", "atomic number\n(not stipulable)"),
        ("country_capital", "capital city\n(not stipulable)"),
    ]
    width = 0.36
    x = np.arange(len(order))
    for index, (model, name, color) in enumerate(
        (("gemma4_12b_conflict", "Gemma 4 12B", S1), ("qwen36_27b_conflict", "Qwen 3.6 27B", S2))
    ):
        stats = [act_effect(conv[model], relation) for relation, _ in order]
        mid = np.array([s[0] for s in stats])
        low = mid - np.array([s[1] for s in stats])
        high = np.array([s[2] for s in stats]) - mid
        axes[0].bar(
            x + (index - 0.5) * (width + 0.02),
            mid,
            width=width,
            color=color,
            label=name,
            linewidth=0.8,
            edgecolor=SURFACE,
            zorder=3,
        )
        axes[0].errorbar(
            x + (index - 0.5) * (width + 0.02),
            mid,
            yerr=[low, high],
            fmt="none",
            ecolor=INK_2,
            elinewidth=1.2,
            capsize=3,
            zorder=4,
        )
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([label for _, label in order], fontsize=9.5)
    axes[0].axhline(0, color=INK_2, linewidth=1.0, zorder=4)
    axes[0].yaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
    axes[0].set_axisbelow(True)
    axes[0].set_ylabel("“a source that adopts” − “a source that asserts”")
    axes[0].set_title(
        "Same 118 entities, opposite sign — so it is\nnot chemistry, familiarity, or stipulability",
        fontsize=11.5,
        loc="left",
        color=INK,
        pad=10,
    )
    axes[0].legend(frameon=False, fontsize=9.5, loc="lower left")

    distances = ["d1", "d2", "d5", "d20", "random"]
    stats = [
        act_effect(plaus, "element_atomic_number", lambda r, d=d: r.get("distance_id") == d)
        for d in distances
    ]
    mid = np.array([s[0] for s in stats])
    axes[1].errorbar(
        np.arange(len(distances)),
        mid,
        yerr=[mid - np.array([s[1] for s in stats]), np.array([s[2] for s in stats]) - mid],
        fmt="o-",
        color=S1,
        ecolor=INK_2,
        elinewidth=1.2,
        capsize=3,
        markersize=8,
        linewidth=2,
        markeredgecolor=SURFACE,
        markeredgewidth=1.2,
        zorder=3,
    )
    axes[1].set_xticks(np.arange(len(distances)))
    axes[1].set_xticklabels(["off by 1", "off by 2", "off by 5", "off by 20", "random"], fontsize=9.5)
    axes[1].axhline(0, color=INK_2, linewidth=1.0, zorder=4)
    axes[1].yaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
    axes[1].set_axisbelow(True)
    axes[1].set_xlabel("how far the false atomic number sits from the true one")
    axes[1].set_ylabel("same contrast, atomic numbers only")
    axes[1].set_title(
        "Negative at every distance, so the sign flip\nis not a near-miss artefact",
        fontsize=11.5,
        loc="left",
        color=INK,
        pad=10,
    )
    fig.tight_layout()
    fig.savefig(out / "fig4_speech_act.png", dpi=200)
    plt.close(fig)
    print(f"wrote {out / 'fig4_speech_act.png'}")


# --- randomly selected examples -----------------------------------------


def sample_examples(results: Path, out: Path, count: int = 6) -> None:
    """Prompts from the experiment the write-up leads with, ordered by hash."""
    rows = tag_runs(results, "gemma4_12b_conflict")
    if not rows:
        print("skip examples: needs delimiter_valence results")
        return
    rows.sort(key=lambda r: hashlib.sha256(str(r["sample_id"]).encode()).hexdigest())
    lines = [
        "# Randomly selected prompts\n",
        "From the wrapper experiment, ordered by SHA-256 of `sample_id`, first "
        f"{count} taken. Not chosen by outcome. Regenerated by `make_figures.py`.\n",
        "`answer` is the model's greedy one-word output. `margin` is "
        "log P(paragraph's answer) − log P(true answer); positive means the "
        "paragraph is winning.\n",
    ]
    for row in rows[:count]:
        lines.append(
            f"\n```\n[{row['relation_id']} · claim style: {row['cell_id']} · wrapper: {row['wrapper']}]\n\n"
            f"{row['raw_prompt']}\n\n"
            f"answer: {row['generated_answer_stripped']!r}   "
            f"(true: {row['parametric_answer']} · paragraph says: {row['context_answer']})   "
            f"margin {row['context_minus_parametric_logprob_margin']:+.2f}\n```\n"
        )
    (out / "random_examples.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out / 'random_examples.md'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--out", type=Path, default=Path("figures"))
    parser.add_argument("--examples", type=int, default=6)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    figure_wrapper_ladder(args.results, args.out)
    figure_warning_channel(args.results, args.out)
    figure_cross_model(args.results, args.out)
    figure_speech_act(args.results, args.out)
    sample_examples(args.results, args.out, args.examples)


if __name__ == "__main__":
    main()
