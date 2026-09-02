#!/usr/bin/env python3
"""E9: is the leakage gradient about atomic numbers, or about weakly-held facts?
"""

from __future__ import annotations

import argparse
import collections
import csv
from pathlib import Path
from typing import Any, Mapping, Sequence

from common import (
    cluster_bootstrap,
    json_safe,
    read_jsonl,
    write_json_atomic,
)


ANALYSIS_VERSION = "1.0.0"
DEFAULT_CELLS = ("bare", "assert_r1", "explicit_stipulation")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--results",
        nargs="+",
        required=True,
        metavar="NAME=PATH",
        help="One or more labelled injection results files, e.g. "
        "gemma=.../conventionality_results.jsonl",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--policy",
        default="neutral",
        help="Which instruction condition to measure the gradient under, "
        "matched against policy_id in the results file.",
    )
    parser.add_argument("--cells", default=",".join(DEFAULT_CELLS))
    parser.add_argument(
        "--bins",
        type=int,
        default=2,
        help="Strength bins per relation, split at that relation's own quantiles.",
    )
    parser.add_argument(
        "--overlap-quantile",
        type=float,
        default=0.10,
        help="T1 calls two relations overlapping when the stronger one's lower "
        "quantile falls below the weaker one's upper quantile at this level.",
    )
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260816)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def load_models(specs: Sequence[str]) -> dict[str, list[dict[str, Any]]]:
    models: dict[str, list[dict[str, Any]]] = {}
    for spec in specs:
        if "=" not in spec:
            raise ValueError(f"--results entries must look like NAME=PATH, got {spec!r}")
        name, _, path = spec.partition("=")
        rows = read_jsonl(Path(path))
        if not any(r.get("cell_id") == "screen" for r in rows):
            raise ValueError(
                f"{path} has no `screen` rows, so knowledge strength cannot be "
                "measured. Re-run E8 without --skip-screening."
            )
        models[name] = rows
    return models


def knowledge_strength(rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    """log P(true) - log P(false) with no paragraph present, per fact.

    The screen row stores the margin the other way round (context minus
    parametric), so this is its negation: higher means held more firmly.
    """
    return {
        str(r["fact_id"]): -float(r["context_minus_parametric_logprob_margin"])
        for r in rows
        if r.get("cell_id") == "screen"
    }


def leaked(row: Mapping[str, Any]) -> bool:
    return str(row.get("observed_knowledge_source")) == "contextual"


def rate_with_ci(
    rows: Sequence[Mapping[str, Any]], replicates: int, seed: int
) -> tuple[float, float, float]:
    import numpy as np

    if not rows:
        return float("nan"), float("nan"), float("nan")
    values = np.asarray([float(leaked(r)) for r in rows])
    facts = [str(r["fact_id"]) for r in rows]
    low, high = cluster_bootstrap(
        facts, lambda picked: float(values[picked].mean()), replicates, seed
    )
    return float(values.mean()), low, high


def paired_margin_delta(
    by_fact: Mapping[str, Mapping[str, float]],
    facts: Sequence[str],
    cell_a: str,
    cell_b: str,
    replicates: int,
    seed: int,
) -> dict[str, Any]:
    import numpy as np

    usable = [f for f in facts if cell_a in by_fact.get(f, {}) and cell_b in by_fact.get(f, {})]
    if not usable:
        return {"delta": float("nan"), "ci95": [float("nan"), float("nan")], "n": 0}
    deltas = np.asarray([by_fact[f][cell_a] - by_fact[f][cell_b] for f in usable])
    low, high = cluster_bootstrap(
        usable, lambda picked: float(deltas[picked].mean()), replicates, seed
    )
    return {"delta": float(deltas.mean()), "ci95": [low, high], "n": len(usable)}


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    import numpy as np

    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if len(x) < 3 or len(np.unique(y)) < 2 or len(np.unique(x)) < 2:
        return float("nan")

    def rank(values: Any) -> Any:
        order = np.argsort(values, kind="mergesort")
        ranks = np.empty(len(values), dtype=float)
        sorted_values = values[order]
        start = 0
        for index in range(1, len(values) + 1):
            if index == len(values) or sorted_values[index] != sorted_values[start]:
                ranks[order[start:index]] = (start + index - 1) / 2.0
                start = index
        return ranks

    return float(np.corrcoef(rank(x), rank(y))[0, 1])


def main() -> None:
    import numpy as np

    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    report_path = args.out / "knowledge_strength_report.md"
    if report_path.exists() and not args.overwrite:
        raise FileExistsError(f"Refusing to overwrite {report_path}; pass --overwrite")

    cells = [c.strip() for c in args.cells.split(",") if c.strip()]
    models = load_models(args.results)
    report: dict[str, Any] = {
        "analysis_version": ANALYSIS_VERSION,
        "policy": args.policy,
        "cells": cells,
        "knowledge_strength": "log P(true) - log P(false), context-free screening prompt",
    }
    lines = ["# E9: is the leakage gradient about a relation, or about fact strength?\n"]
    lines.append(
        f"Leakage is measured under the `{args.policy}` policy — the user "
        "instructing the model to ignore the paragraph. Knowledge strength is "
        "`log P(true) − log P(false)` on the context-free screening prompt, so "
        "it is measured before any manipulation touches the fact.\n"
    )

    all_t1: list[dict[str, Any]] = []
    all_t2: list[dict[str, Any]] = []
    all_t3: list[dict[str, Any]] = []
    all_t4: list[dict[str, Any]] = []

    for model, rows in models.items():
        strength = knowledge_strength(rows)
        live = [
            r for r in rows
            if r.get("cell_id") in cells
            and str(r.get("policy_id", "neutral")) == args.policy
            and str(r["fact_id"]) in strength
        ]
        neutral = [
            r for r in rows
            if r.get("cell_id") in cells
            and str(r.get("policy_id", "neutral")) == "neutral"
            and str(r["fact_id"]) in strength
        ]
        relations = sorted({str(r["relation_id"]) for r in live})

        # ---- T1: distributions and overlap -------------------------------
        print("=" * 82)
        print(f"T1  [{model}] knowledge strength by relation, and is there overlap?")
        print("=" * 82)
        print(f"{'relation':26s}{'n':>5s}{'median':>10s}{'q10':>9s}{'q90':>9s}")
        spans: dict[str, tuple[float, float, float]] = {}
        for relation in relations:
            values = np.asarray([
                strength[f] for f in {str(r["fact_id"]) for r in live if r["relation_id"] == relation}
            ])
            low_q = float(np.quantile(values, args.overlap_quantile))
            high_q = float(np.quantile(values, 1 - args.overlap_quantile))
            spans[relation] = (low_q, float(np.median(values)), high_q)
            all_t1.append({
                "model": model, "relation": relation, "n": int(values.size),
                "median": float(np.median(values)), "q_low": low_q, "q_high": high_q,
            })
            print(f"{relation:26s}{values.size:>5d}{np.median(values):>10.2f}"
                  f"{low_q:>9.2f}{high_q:>9.2f}")
        overlaps = []
        for i, a in enumerate(relations):
            for b in relations[i + 1:]:
                lo = max(spans[a][0], spans[b][0])
                hi = min(spans[a][2], spans[b][2])
                if lo < hi:
                    overlaps.append((a, b, lo, hi))
        if overlaps:
            print("\n  Overlapping ranges (a matched-strength comparison IS possible):")
            for a, b, lo, hi in overlaps:
                print(f"    {a} vs {b}: strength in [{lo:.2f}, {hi:.2f}]")
        else:
            print(
                "\n  NO OVERLAP. Relation and knowledge strength are fully confounded\n"
                "  in this dataset: the weakest fact of one relation is still stronger\n"
                "  than the strongest fact of another. T4 cannot run, and the strongest\n"
                "  available claim is the within-relation trend in T3."
            )

        # ---- T2: within-relation strength bins ----------------------------
        print("\n" + "=" * 82)
        print(f"T2  [{model}] the gradient inside each relation's own strength bins")
        print("=" * 82)
        header = "".join(f"{c[:14]:>16s}" for c in cells)
        print(f"{'relation':24s}{'bin':10s}{'n':>5s}{header}{'neutral(bare)':>16s}")
        for relation in relations:
            facts = sorted({str(r["fact_id"]) for r in live if r["relation_id"] == relation})
            values = np.asarray([strength[f] for f in facts])
            edges = np.quantile(values, np.linspace(0, 1, args.bins + 1))
            edges[0], edges[-1] = -np.inf, np.inf
            for index in range(args.bins):
                lo, hi = edges[index], edges[index + 1]
                members = {f for f in facts if lo <= strength[f] < hi}
                if len(members) < 5:
                    continue
                label = ["weak", "strong"][index] if args.bins == 2 else f"q{index + 1}"
                parts, entry_cells = [], {}
                for cell in cells:
                    subset = [
                        r for r in live
                        if r["relation_id"] == relation and r["cell_id"] == cell
                        and str(r["fact_id"]) in members
                    ]
                    rate, low, high = rate_with_ci(subset, args.bootstrap_replicates, args.seed)
                    entry_cells[cell] = {"rate": rate, "ci95": [low, high], "n": len(subset)}
                    parts.append(f"{100 * rate:>9.1f}% ")
                base = [
                    r for r in neutral
                    if r["relation_id"] == relation and r["cell_id"] == "bare"
                    and str(r["fact_id"]) in members
                ]
                base_rate = float(np.mean([leaked(r) for r in base])) if base else float("nan")
                all_t2.append({
                    "model": model, "relation": relation, "bin": label,
                    "n_facts": len(members),
                    "strength_median": float(np.median([strength[f] for f in members])),
                    "cells": entry_cells, "neutral_bare_rate": base_rate,
                })
                print(f"{relation:24s}{label:10s}{len(members):>5d}"
                      + "".join(f"{p:>16s}" for p in parts)
                      + f"{100 * base_rate:>15.1f}%")

        # ---- T3: continuous, no binning -----------------------------------
        print("\n" + "=" * 82)
        print(f"T3  [{model}] leakage vs strength, continuously")
        print("    Negative rho = firmly-held facts leak less. Consistent negatives")
        print("    inside every relation support strength over relation identity.")
        print("=" * 82)
        print(f"{'relation':26s}{'cell':22s}{'rho(strength, leak)':>21s}{'rho(strength, margin)':>23s}{'n':>6s}")
        for relation in relations + ["POOLED"]:
            for cell in cells:
                subset = [
                    r for r in live
                    if r["cell_id"] == cell
                    and (relation == "POOLED" or r["relation_id"] == relation)
                ]
                if len(subset) < 10:
                    continue
                s = [strength[str(r["fact_id"])] for r in subset]
                rho_leak = spearman(s, [float(leaked(r)) for r in subset])
                rho_margin = spearman(
                    s, [float(r["context_minus_parametric_logprob_margin"]) for r in subset]
                )
                all_t3.append({
                    "model": model, "relation": relation, "cell": cell,
                    "rho_leak": rho_leak, "rho_margin": rho_margin, "n": len(subset),
                })
                print(f"{relation:26s}{cell:22s}{rho_leak:>21.3f}{rho_margin:>23.3f}{len(subset):>6d}")

        # ---- T4: matched strength across relations ------------------------
        if overlaps:
            print("\n" + "=" * 82)
            print(f"T4  [{model}] MATCHED STRENGTH: do relations leak alike?")
            print("=" * 82)
            for a, b, lo, hi in overlaps:
                print(f"\n  strength window [{lo:.2f}, {hi:.2f}]   {a} vs {b}")
                for cell in cells:
                    row_line = []
                    for relation in (a, b):
                        subset = [
                            r for r in live
                            if r["relation_id"] == relation and r["cell_id"] == cell
                            and lo <= strength[str(r["fact_id"])] <= hi
                        ]
                        rate, _, _ = rate_with_ci(subset, args.bootstrap_replicates, args.seed)
                        row_line.append((relation, rate, len(subset)))
                        all_t4.append({
                            "model": model, "cell": cell, "relation": relation,
                            "window": [lo, hi], "rate": rate, "n": len(subset),
                        })
                    text = "   ".join(
                        f"{r}: {100 * v:.1f}% (n={n})" for r, v, n in row_line
                    )
                    print(f"    {cell:22s} {text}")

        # ---- the headline contrast, per relation and bin ------------------
        by_fact: dict[str, dict[str, float]] = collections.defaultdict(dict)
        for r in live:
            by_fact[str(r["fact_id"])][str(r["cell_id"])] = float(
                r["context_minus_parametric_logprob_margin"]
            )
        print("\n" + "=" * 82)
        print(f"    [{model}] bare − explicit margin gap (the gradient, graded)")
        print("=" * 82)
        for relation in relations:
            facts = sorted({str(r["fact_id"]) for r in live if r["relation_id"] == relation})
            values = np.asarray([strength[f] for f in facts])
            median = float(np.median(values))
            for label, members in (
                ("weak", [f for f in facts if strength[f] < median]),
                ("strong", [f for f in facts if strength[f] >= median]),
            ):
                result = paired_margin_delta(
                    by_fact, members, "bare", "explicit_stipulation",
                    args.bootstrap_replicates, args.seed,
                )
                low, high = result["ci95"]
                star = "***" if (low > 0 or high < 0) else "   "
                print(f"    {relation:24s}{label:8s}{result['delta']:>9.2f}"
                      f"  [{low:+.2f}, {high:+.2f}] {star}  n={result['n']}")
                all_t2.append({
                    "model": model, "relation": relation, "bin": label,
                    "contrast": "bare_minus_explicit_margin", **result,
                })
        print()

    report.update({
        "strength_distributions": all_t1,
        "binned_gradient": all_t2,
        "continuous": all_t3,
        "matched_strength": all_t4,
    })
    write_json_atomic(args.out / "knowledge_strength_summary.json", json_safe(report))

    if all_t2:
        keys = ["model", "relation", "bin", "n_facts", "strength_median", "neutral_bare_rate"]
        with (args.out / "knowledge_strength_bins.csv").open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(keys + [f"{c}_rate" for c in cells])
            for entry in all_t2:
                if "cells" not in entry:
                    continue
                writer.writerow(
                    [entry.get(k, "") for k in keys]
                    + [f"{entry['cells'][c]['rate']:.4f}" for c in cells]
                )

    lines.append("## Strength by relation\n")
    lines.append("| Model | Relation | n | Median strength | q10 | q90 |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for entry in all_t1:
        lines.append(
            f"| {entry['model']} | {entry['relation']} | {entry['n']} | "
            f"{entry['median']:.2f} | {entry['q_low']:.2f} | {entry['q_high']:.2f} |"
        )
    lines.append("\n## The gradient inside each relation's strength bins\n")
    lines.append("| Model | Relation | Bin | n | " + " | ".join(cells) + " | neutral (bare) |")
    lines.append("|---|---|---|---:|" + "---:|" * (len(cells) + 1))
    for entry in all_t2:
        if "cells" not in entry:
            continue
        lines.append(
            f"| {entry['model']} | {entry['relation']} | {entry['bin']} | {entry['n_facts']} | "
            + " | ".join(f"{100 * entry['cells'][c]['rate']:.1f}%" for c in cells)
            + f" | {100 * entry['neutral_bare_rate']:.1f}% |"
        )
    lines.append("\n## Leakage vs strength, continuously\n")
    lines.append("| Model | Relation | Cell | rho(strength, leak) | rho(strength, margin) | n |")
    lines.append("|---|---|---|---:|---:|---:|")
    for entry in all_t3:
        lines.append(
            f"| {entry['model']} | {entry['relation']} | {entry['cell']} | "
            f"{entry['rho_leak']:.3f} | {entry['rho_margin']:.3f} | {entry['n']} |"
        )
    lines.append("\n## How to read this\n")
    lines.append(
        "- **The question.** The bare > assert > explicit gradient was only "
        "visible on atomic numbers, because every other relation sat at 0% "
        "leakage. Is it a fact about atomic numbers, or about facts the model "
        "holds loosely?\n"
        "- **T1 gates T4.** If the relations' strength ranges do not overlap, "
        "relation and strength are confounded here and no matched comparison "
        "exists. Say that rather than implying one was made.\n"
        "- **T2** is the direct test: the gradient appearing in the weak half of "
        "symbols and capitals too would make it general. Note that a weak half "
        "is only weak *relative to its own relation* — if the weakest symbols "
        "are still firmly held, this test has no room to show anything, and T3 "
        "carries the argument instead.\n"
        "- **T3 needs no bins.** A consistently negative rho inside every "
        "relation says leakage falls with strength wherever it is measured, "
        "which supports strength over relation identity even without overlap.\n"
        "- **The confound.** `neutral (bare)` is the same cell without the user "
        "instruction. If weak facts simply defer more everywhere, that column "
        "shows it, and the gradient claim has to be stated relative to that "
        "baseline rather than absolutely.\n"
        "- Leakage is binary per fact, so the rates are what they are; the "
        "graded `bare − explicit` margin contrast printed to the console is the "
        "version with confidence intervals, clustered on facts.\n"
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out / 'knowledge_strength_summary.json'}")
    print(f"wrote {report_path}")


if __name__ == "__main__":
    main()
