#!/usr/bin/env python3
"""E6: which part of the paragraph carries the deference swing?
"""

from __future__ import annotations

import argparse
import collections
import csv
import time
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping, Sequence

from build_conflict_awareness_dataset import (
    TEMPLATE_BUNDLES,
    TemplateBundle,
    build_experiment_prompt,
    relation_specs,
    stable_digest,
)
from common import (
    answer_matches,
    append_jsonl,
    cluster_bootstrap,
    CODE_VERSION,
    finalize_jsonl,
    generate_batch,
    is_one_orthographic_word,
    json_safe,
    load_config,
    load_model_bundle,
    normalize_answer,
    read_jsonl,
    runtime_fingerprint,
    score_continuations,
    seed_everything,
    write_json_atomic,
)


ANALYSIS_VERSION = "1.1.0"

# The four things that differ between bundles under the neutral policy. The
# policy wording is a fifth factor but is an empty string when no instruction
# is given, so it only matters for --include-policy-endpoints.
FACTORS = ("claim", "filler", "question", "constraint")
FACTOR_FIELD = {
    "claim": "claim_template_index",
    "filler": "filler_index",
    "question": "question_template_index",
    "constraint": "response_constraint_index",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument(
        "--behavior",
        type=Path,
        required=True,
        help="behavior_results.jsonl -- supplies the measured margins the "
        "endpoints must reproduce, and the false answer for each fact.",
    )
    parser.add_argument(
        "--experiment",
        type=Path,
        default=None,
        help="The dataset's experiment.jsonl. Optional but strongly recommended: "
        "it carries raw_prompt, which lets this script prove its rebuilt "
        "endpoint prompts are byte-identical to the originals. "
        "behavior_results.jsonl does not store prompts, so without this the "
        "check is skipped.",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--design",
        default="swap",
        choices=("swap", "full"),
        help="'swap' = 10 cells/fact (endpoints + single swaps both ways). "
        "'full' = all 3^4 = 81 combinations, about 8x the compute.",
    )
    parser.add_argument(
        "--high-bundle",
        default=None,
        help="Force the high-deference endpoint. Default: detected per relation "
        "from the behaviour file's mean margin.",
    )
    parser.add_argument("--low-bundle", default=None, help="Force the low endpoint.")
    parser.add_argument(
        "--include-policy-endpoints",
        action="store_true",
        help="Also score endpoints A and B under the context and parametric "
        "instructions, so the paraphrase and instruction effects are measured "
        "on the same facts in the same run.",
    )
    parser.add_argument("--relations", default="country_capital,element_symbol")
    parser.add_argument("--max-facts", type=int, default=None, help="Pilot cap per relation.")
    parser.add_argument("--generation-batch-size", type=int, default=None)
    parser.add_argument("--scoring-batch-size", type=int, default=None)
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    parser.add_argument(
        "--reproduction-tolerance",
        type=float,
        default=0.25,
        help="Warn if an endpoint margin differs from the cached step-02 value "
        "by more than this. BF16 batch-width effects make exact equality "
        "unrealistic; a large drift means something is genuinely wrong.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Build and check every prompt without loading the model.",
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Skip the model entirely and re-analyse an existing "
        "decomposition_results.jsonl. Use this to change --bootstrap-replicates "
        "or regenerate the report without repeating GPU work.",
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Cell construction
# ---------------------------------------------------------------------------


def bundle_indices(bundle: TemplateBundle) -> dict[str, int]:
    return {factor: getattr(bundle, FACTOR_FIELD[factor]) for factor in FACTORS}


def make_bundle(reference: TemplateBundle, indices: Mapping[str, int]) -> TemplateBundle:
    """A bundle with the given per-factor indices, everything else inherited."""
    return replace(
        reference,
        **{FACTOR_FIELD[factor]: int(indices[factor]) for factor in FACTORS},
    )


def swap_cells(
    high: TemplateBundle, low: TemplateBundle
) -> list[tuple[str, dict[str, int]]]:
    """Endpoints, plus one-factor swaps in each direction."""
    a, b = bundle_indices(high), bundle_indices(low)
    cells: list[tuple[str, dict[str, int]]] = [
        ("endpoint_high", dict(a)),
        ("endpoint_low", dict(b)),
    ]
    for factor in FACTORS:
        sufficiency = dict(b)
        sufficiency[factor] = a[factor]
        cells.append((f"low_plus_{factor}", sufficiency))

        necessity = dict(a)
        necessity[factor] = b[factor]
        cells.append((f"high_minus_{factor}", necessity))
    return cells


def full_cells(n_levels: int = 3) -> list[tuple[str, dict[str, int]]]:
    import itertools

    cells = []
    for combo in itertools.product(range(n_levels), repeat=len(FACTORS)):
        indices = dict(zip(FACTORS, combo))
        cells.append(("x".join(str(v) for v in combo), indices))
    return cells


def build_records(
    args: argparse.Namespace,
    facts: Sequence[Mapping[str, Any]],
    endpoints: Mapping[str, tuple[TemplateBundle, TemplateBundle]],
    specs: Mapping[str, Any],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for fact in facts:
        relation = str(fact["relation_id"])
        spec = specs[relation]
        high, low = endpoints[relation]
        cells = swap_cells(high, low) if args.design == "swap" else full_cells()

        policy_plan = [("neutral", cells)]
        if args.include_policy_endpoints:
            endpoint_only = [
                ("endpoint_high", bundle_indices(high)),
                ("endpoint_low", bundle_indices(low)),
            ]
            policy_plan.append(("context", endpoint_only))
            policy_plan.append(("parametric", endpoint_only))

        for policy_id, plan in policy_plan:
            for cell_id, indices in plan:
                reference = high if cell_id != "endpoint_low" else low
                bundle = make_bundle(reference, indices)
                prompt, spans, semantic_positions = build_experiment_prompt(
                    spec=spec,
                    bundle=bundle,
                    policy_id=policy_id,
                    claim_subject=str(fact["query_subject"]),
                    claim_answer=str(fact["claim_answer"]),
                    query_subject=str(fact["query_subject"]),
                )
                sample_id = "dec-" + stable_digest(
                    fact["fact_id"], cell_id, policy_id, prompt
                )
                records.append(
                    {
                        "sample_id": sample_id,
                        "raw_prompt": prompt,
                        "messages": [{"role": "user", "content": prompt}],
                        "semantic_positions": semantic_positions,
                        "fact_id": fact["fact_id"],
                        "relation_id": relation,
                        "fact_split": fact["fact_split"],
                        "query_subject": fact["query_subject"],
                        "claim_answer": fact["claim_answer"],
                        "context_candidate_answer": fact["claim_answer"],
                        "acceptable_world_true_answers": list(
                            fact["acceptable_world_true_answers"]
                        ),
                        "parametric_candidate_answer": fact["world_true_answer"],
                        "policy_id": policy_id,
                        "cell_id": cell_id,
                        "template_indices": dict(indices),
                        "matches_original_bundle": next(
                            (
                                b.bundle_id
                                for b in TEMPLATE_BUNDLES
                                if bundle_indices(b) == dict(indices)
                            ),
                            None,
                        ),
                    }
                )
    return records


# ---------------------------------------------------------------------------
# Behaviour classification (mirrors classify_generation in 02_collect_model_data)
# ---------------------------------------------------------------------------


def classify(record: Mapping[str, Any], text: str) -> str:
    if not is_one_orthographic_word(text):
        return "unparseable"
    matches_parametric = answer_matches(
        text, list(record["acceptable_world_true_answers"])
    )
    matches_context = normalize_answer(text) == normalize_answer(
        record["context_candidate_answer"]
    )
    if matches_parametric and matches_context:
        return "shared_parametric_and_context"
    if matches_parametric:
        return "parametric"
    if matches_context:
        return "contextual"
    return "other"


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def paired_cell_delta(
    margins: Mapping[tuple[str, str], float],
    facts: Sequence[str],
    cell_a: str,
    cell_b: str,
    replicates: int,
    seed: int,
) -> dict[str, Any]:
    """Mean margin(cell_a) - margin(cell_b), paired within fact."""
    import numpy as np

    usable = [
        f
        for f in facts
        if (f, cell_a) in margins
        and (f, cell_b) in margins
        and np.isfinite(margins[(f, cell_a)])
        and np.isfinite(margins[(f, cell_b)])
    ]
    if not usable:
        return {"delta": float("nan"), "ci95": [float("nan"), float("nan")], "n": 0}
    deltas = np.asarray(
        [margins[(f, cell_a)] - margins[(f, cell_b)] for f in usable], dtype=np.float64
    )
    low, high = cluster_bootstrap(
        usable, lambda picked: float(np.mean(deltas[picked])), replicates, seed
    )
    return {"delta": float(np.mean(deltas)), "ci95": [low, high], "n": len(usable)}


def main() -> None:
    import numpy as np

    started = time.time()
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    results_path = args.out / "decomposition_results.jsonl"
    partial_path = args.out / "decomposition_results.jsonl.partial"
    report_path = args.out / "decomposition_report.md"
    # --analyze-only reads this file and never writes it, so the guard must not
    # fire there; --validate-only writes nothing at all.
    if (
        results_path.exists()
        and not args.overwrite
        and not args.validate_only
        and not args.analyze_only
    ):
        raise FileExistsError(f"Refusing to overwrite {results_path}; pass --overwrite")
    if args.analyze_only and args.validate_only:
        raise ValueError("--analyze-only and --validate-only are mutually exclusive")

    config = load_config(args.config)
    relations = [r.strip() for r in args.relations.split(",") if r.strip()]
    specs = relation_specs()
    behaviour = read_jsonl(args.behavior)

    # ---- endpoints and facts, taken from the run we are explaining ---------
    source_rows = [
        r
        for r in behaviour
        if str(r["condition_id"]) == "false_relevant"
        and str(r["policy_id"]) == "neutral"
        and str(r["relation_id"]) in relations
    ]
    if not source_rows:
        raise ValueError("No false_relevant/neutral rows found for the requested relations")

    by_bundle: dict[tuple[str, str], list[float]] = collections.defaultdict(list)
    for row in source_rows:
        value = row.get("context_minus_parametric_logprob_margin")
        if value is not None:
            by_bundle[(str(row["relation_id"]), str(row["template_bundle_id"]))].append(
                float(value)
            )
    bundle_by_id = {b.bundle_id: b for b in TEMPLATE_BUNDLES}
    endpoints: dict[str, tuple[TemplateBundle, TemplateBundle]] = {}
    print("Endpoint selection (mean context-minus-parametric margin, neutral policy):")
    for relation in relations:
        means = {
            bundle: float(np.mean(values))
            for (rel, bundle), values in by_bundle.items()
            if rel == relation
        }
        if len(means) < 2:
            raise ValueError(f"Relation {relation} has fewer than two bundles to compare")
        for bundle, value in sorted(means.items(), key=lambda kv: -kv[1]):
            print(f"  {relation:17s} {bundle:22s} {value:8.2f}")
        high_id = args.high_bundle or max(means, key=means.get)
        low_id = args.low_bundle or min(means, key=means.get)
        if high_id == low_id:
            raise ValueError(f"High and low endpoints coincide for {relation}")
        endpoints[relation] = (bundle_by_id[high_id], bundle_by_id[low_id])
        print(f"  -> {relation}: high={high_id}, low={low_id}\n")

    facts: list[dict[str, Any]] = []
    seen: set[str] = set()
    per_relation: collections.Counter = collections.Counter()
    for row in source_rows:
        fact_id = str(row["fact_id"])
        if fact_id in seen:
            continue
        relation = str(row["relation_id"])
        if args.max_facts is not None and per_relation[relation] >= args.max_facts:
            continue
        seen.add(fact_id)
        per_relation[relation] += 1
        facts.append(
            {
                "fact_id": fact_id,
                "relation_id": relation,
                "fact_split": row["fact_split"],
                "query_subject": row["query_subject"],
                "claim_answer": row["claim_answer"],
                "world_true_answer": row["world_true_answer"],
                "acceptable_world_true_answers": row["acceptable_world_true_answers"],
            }
        )
    print(f"facts: {dict(per_relation)}")

    records = build_records(args, facts, endpoints, specs)
    if not records:
        raise ValueError(
            "No cells were built. Check --relations and --max-facts against the "
            "false_relevant/neutral rows in the behaviour file."
        )
    print(f"cells/fact: {len(records) / max(1, len(facts)):.1f}   prompts: {len(records)}")

    # ---- validation --------------------------------------------------------
    # The endpoints must reconstruct the ORIGINAL prompts byte for byte. If they
    # do not, the templates or the assembly have drifted and no comparison to
    # the cached run is meaningful.
    experiment_prompts: dict[tuple[str, str, str], str] = {}
    prompt_source = read_jsonl(args.experiment) if args.experiment else behaviour
    for row in prompt_source:
        if str(row.get("condition_id")) != "false_relevant":
            continue
        if "raw_prompt" not in row:
            continue
        key = (str(row["fact_id"]), str(row["template_bundle_id"]), str(row["policy_id"]))
        experiment_prompts[key] = str(row["raw_prompt"])

    mismatches = 0
    checked = 0
    for record in records:
        bundle_id = record["matches_original_bundle"]
        if bundle_id is None:
            continue
        key = (str(record["fact_id"]), str(bundle_id), str(record["policy_id"]))
        expected = experiment_prompts.get(key)
        if expected is None:
            continue
        checked += 1
        if expected != record["raw_prompt"]:
            mismatches += 1
            if mismatches <= 3:
                print("\nPROMPT MISMATCH")
                print(f"  expected: {expected!r}")
                print(f"  rebuilt : {record['raw_prompt']!r}")
    if checked:
        print(f"prompt reconstruction: {checked - mismatches}/{checked} identical")
        if mismatches:
            raise RuntimeError(
                "Rebuilt prompts differ from the original run. The generator "
                "templates have drifted; fix that before running the model."
            )
    else:
        print(
            "prompt reconstruction: SKIPPED -- no raw_prompt available.\n"
            "  behavior_results.jsonl does not store prompts. Pass the dataset's\n"
            "  experiment.jsonl via --experiment to enable this check. Without it\n"
            "  you are trusting that the templates have not drifted since step 02."
        )

    if args.validate_only:
        print("\n--- example cells for one fact ---")
        example_fact = records[0]["fact_id"]
        for record in [r for r in records if r["fact_id"] == example_fact][:12]:
            print(f"\n[{record['cell_id']} | {record['policy_id']}] "
                  f"{record['template_indices']}")
            print(record["raw_prompt"])
        print(f"\nvalidate-only: {len(records)} prompts would be evaluated")
        return

    # ---- run ---------------------------------------------------------------
    if args.analyze_only:
        if not results_path.is_file():
            raise FileNotFoundError(f"--analyze-only needs an existing {results_path}")
        rows = read_jsonl(results_path)
        fingerprint = {"note": "analyze-only; the model was not loaded this run"}
        print(f"analyze-only: reusing {len(rows)} scored prompts")
        analyze(
            args, config, rows, source_rows, endpoints, relations, facts,
            report_path, started,
            extra={"runtime": fingerprint},
        )
        return

    seed_everything(int(config["project"]["seed"]))
    done: set[str] = set()
    if partial_path.exists() and not args.overwrite:
        done = {str(r["sample_id"]) for r in read_jsonl(partial_path)}
        print(f"resuming: {len(done)} prompts already scored")
    elif partial_path.exists():
        partial_path.unlink()

    pending = [r for r in records if r["sample_id"] not in done]
    bundle = load_model_bundle(config)
    # runtime_fingerprint hashes the inputs a run depended on, so the provenance
    # record names this script's actual sources rather than the step-01/02 ones.
    dataset_files: dict[str, Any] = {"behavior": args.behavior}
    if args.experiment is not None:
        dataset_files["experiment"] = args.experiment
    fingerprint = runtime_fingerprint(config, bundle, dataset_files)
    generation_batch = args.generation_batch_size or int(
        config["collection"]["generation_batch_size"]
    )
    scoring_batch = args.scoring_batch_size or int(config["collection"]["scoring_batch_size"])
    max_input = int(config["chat"]["max_input_tokens"])

    from common import render_dataset_record

    for start in range(0, len(pending), generation_batch):
        chunk = pending[start : start + generation_batch]
        rendered = [render_dataset_record(bundle.processor, r, config) for r in chunk]
        texts = [r.rendered_text for r in rendered]
        generations = generate_batch(bundle.model, bundle.tokenizer, texts, config)

        requests: list[dict[str, str]] = []
        for index, record in enumerate(chunk):
            requests.append(
                {
                    "key": f"{index}|context",
                    "rendered_text": texts[index],
                    "continuation": str(record["context_candidate_answer"]),
                }
            )
            for alias_index, answer in enumerate(record["acceptable_world_true_answers"]):
                requests.append(
                    {
                        "key": f"{index}|parametric|{alias_index}",
                        "rendered_text": texts[index],
                        "continuation": str(answer),
                    }
                )
        scores = score_continuations(
            bundle.model, bundle.tokenizer, requests, scoring_batch, max_input
        )
        by_key = {s.key: s for s in scores}

        output: list[dict[str, Any]] = []
        for index, record in enumerate(chunk):
            context_score = by_key[f"{index}|context"]
            parametric_candidates = [
                by_key[f"{index}|parametric|{alias_index}"]
                for alias_index in range(len(record["acceptable_world_true_answers"]))
            ]
            best_parametric = max(parametric_candidates, key=lambda s: s.sum_logprob)
            generation = generations[index]
            text = generation["text"]
            # Classify the answer with any reasoning preamble removed, as E8 and
            # later scripts do. Gemma leaks one on unusual prompts, and
            # classifying the raw decode put up to 41% of rows in "other" here
            # while E8 saw 0% on the same model. Margins are teacher-forced and
            # were never affected; only the rates were.
            answer = str(generation.get("answer_text") or text)
            output.append(
                {
                    "code_version": CODE_VERSION,
                    "analysis_version": ANALYSIS_VERSION,
                    "sample_id": record["sample_id"],
                    "fact_id": record["fact_id"],
                    "relation_id": record["relation_id"],
                    "fact_split": record["fact_split"],
                    "cell_id": record["cell_id"],
                    "policy_id": record["policy_id"],
                    "template_indices": record["template_indices"],
                    "matches_original_bundle": record["matches_original_bundle"],
                    "raw_prompt": record["raw_prompt"],
                    "generated_answer": text,
                    "generated_answer_stripped": answer,
                    "had_reasoning_preamble": bool(
                        generation.get("had_reasoning_preamble", False)
                    ),
                    "format_compliant": is_one_orthographic_word(text),
                    "observed_knowledge_source": classify(record, answer),
                    "context_answer": record["context_candidate_answer"],
                    "parametric_answer": best_parametric.continuation,
                    "context_answer_sequence_logprob": context_score.sum_logprob,
                    "parametric_answer_sequence_logprob": best_parametric.sum_logprob,
                    "context_minus_parametric_logprob_margin": (
                        context_score.sum_logprob - best_parametric.sum_logprob
                    ),
                }
            )
        append_jsonl(partial_path, output)
        if (start // generation_batch) % 10 == 0:
            print(
                f"  {start + len(chunk)}/{len(pending)} "
                f"({time.time() - started:7.1f}s)"
            )

    rows = read_jsonl(partial_path)
    finalize_jsonl(partial_path, results_path)
    print(f"\nscored {len(rows)} prompts")
    analyze(
        args, config, rows, source_rows, endpoints, relations, facts,
        report_path, started, extra={"runtime": fingerprint},
    )


def analyze(
    args: argparse.Namespace,
    config: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    source_rows: Sequence[Mapping[str, Any]],
    endpoints: Mapping[str, Any],
    relations: Sequence[str],
    facts: Sequence[Mapping[str, Any]],
    report_path: Path,
    started: float,
    extra: Mapping[str, Any] | None = None,
) -> None:
    """Everything downstream of scoring. Split out so --analyze-only can
    re-run it against an existing results file without a GPU.
    """
    import numpy as np

    # ---- analysis ----------------------------------------------------------
    report: dict[str, Any] = {
        "analysis_version": ANALYSIS_VERSION,
        "design": args.design,
        "endpoints": {
            relation: {"high": high.bundle_id, "low": low.bundle_id}
            for relation, (high, low) in endpoints.items()
        },
    }
    report.update(dict(extra or {}))

    cached_margin = {
        (str(r["fact_id"]), str(r["template_bundle_id"])): r[
            "context_minus_parametric_logprob_margin"
        ]
        for r in source_rows
    }
    reproduction: list[dict[str, Any]] = []
    for relation, (high, low) in endpoints.items():
        for cell_id, endpoint in (("endpoint_high", high), ("endpoint_low", low)):
            deltas = []
            for row in rows:
                if (
                    row["relation_id"] != relation
                    or row["cell_id"] != cell_id
                    or row["policy_id"] != "neutral"
                ):
                    continue
                cached = cached_margin.get((str(row["fact_id"]), endpoint.bundle_id))
                if cached is None:
                    continue
                deltas.append(
                    float(row["context_minus_parametric_logprob_margin"]) - float(cached)
                )
            if deltas:
                entry = {
                    "relation": relation,
                    "cell": cell_id,
                    "bundle": endpoint.bundle_id,
                    "mean_abs_delta": float(np.mean(np.abs(deltas))),
                    "max_abs_delta": float(np.max(np.abs(deltas))),
                    "n": len(deltas),
                }
                reproduction.append(entry)
    report["endpoint_reproduction"] = reproduction
    print("\n" + "=" * 78)
    print("R0  endpoint reproduction against the cached step-02 margins")
    print("=" * 78)
    for entry in reproduction:
        flag = "" if entry["max_abs_delta"] <= args.reproduction_tolerance else "  <-- CHECK"
        print(
            f"  {entry['relation']:17s} {entry['cell']:15s} "
            f"mean|d|={entry['mean_abs_delta']:6.3f} max|d|={entry['max_abs_delta']:7.3f}"
            f"{flag}"
        )
    if any(e["max_abs_delta"] > args.reproduction_tolerance for e in reproduction):
        print(
            "\n  Endpoints do not reproduce the cached run within tolerance.\n"
            "  Check the model revision, transformers version, and chat template\n"
            "  before interpreting anything below."
        )

    margins = {
        (str(r["fact_id"]), str(r["cell_id"])): float(
            r["context_minus_parametric_logprob_margin"]
        )
        for r in rows
        if r["policy_id"] == "neutral"
    }
    contributions: list[dict[str, Any]] = []
    print("\n" + "=" * 78)
    print("R1  per-factor decomposition of the endpoint gap (margin, logits)")
    print("=" * 78)
    for relation in relations:
        relation_facts = sorted(
            {str(r["fact_id"]) for r in rows if r["relation_id"] == relation}
        )
        total = paired_cell_delta(
            margins, relation_facts, "endpoint_high", "endpoint_low",
            args.bootstrap_replicates, int(config["project"]["seed"]),
        )
        print(f"\n--- {relation} ---")
        print(
            f"  TOTAL high - low            {total['delta']:8.2f}  "
            f"[{total['ci95'][0]:+.2f}, {total['ci95'][1]:+.2f}]  n={total['n']}"
        )
        contributions.append({"relation": relation, "factor": "TOTAL", "kind": "total", **total})

        if args.design != "swap":
            continue
        sufficiency_sum = 0.0
        print(f"  {'factor':12s}{'sufficiency':>14s}{'95% CI':>22s}"
              f"{'necessity':>13s}{'95% CI':>22s}")
        for factor in FACTORS:
            suff = paired_cell_delta(
                margins, relation_facts, f"low_plus_{factor}", "endpoint_low",
                args.bootstrap_replicates, int(config["project"]["seed"]),
            )
            nec = paired_cell_delta(
                margins, relation_facts, "endpoint_high", f"high_minus_{factor}",
                args.bootstrap_replicates, int(config["project"]["seed"]),
            )
            sufficiency_sum += suff["delta"] if suff["delta"] == suff["delta"] else 0.0
            contributions.append(
                {"relation": relation, "factor": factor, "kind": "sufficiency", **suff}
            )
            contributions.append(
                {"relation": relation, "factor": factor, "kind": "necessity", **nec}
            )
            suff_lo, suff_hi = suff["ci95"]
            nec_lo, nec_hi = nec["ci95"]
            suff_interval = f"[{suff_lo:+.2f}, {suff_hi:+.2f}]"
            nec_interval = f"[{nec_lo:+.2f}, {nec_hi:+.2f}]"
            print(
                f"  {factor:12s}{suff['delta']:>14.2f}{suff_interval:>22}"
                f"{nec['delta']:>13.2f}{nec_interval:>22}"
            )
        residual = total["delta"] - sufficiency_sum
        print(
            f"\n  additivity: single swaps sum to {sufficiency_sum:.2f} vs total "
            f"{total['delta']:.2f} (residual {residual:+.2f})"
        )
        if abs(residual) > 0.25 * abs(total["delta"]):
            print(
                "  -> the factors INTERACT. A single-factor story is wrong here;\n"
                "     consider --design full before claiming one component owns it."
            )
        contributions.append(
            {
                "relation": relation,
                "factor": "ADDITIVITY_RESIDUAL",
                "kind": "residual",
                "delta": float(residual),
                "ci95": [float("nan"), float("nan")],
                "n": total["n"],
            }
        )
    report["contributions"] = contributions

    # ---- behaviour per cell ------------------------------------------------
    cell_summary: list[dict[str, Any]] = []
    for relation in relations:
        for cell_id in sorted({str(r["cell_id"]) for r in rows}):
            subset = [
                r
                for r in rows
                if r["relation_id"] == relation
                and r["cell_id"] == cell_id
                and r["policy_id"] == "neutral"
            ]
            if not subset:
                continue
            counts = collections.Counter(r["observed_knowledge_source"] for r in subset)
            n = len(subset)
            cell_summary.append(
                {
                    "relation": relation,
                    "cell": cell_id,
                    "n": n,
                    "context_rate": counts.get("contextual", 0) / n,
                    "parametric_rate": counts.get("parametric", 0) / n,
                    "other_rate": (counts.get("other", 0) + counts.get("unparseable", 0)) / n,
                    "mean_margin": float(
                        np.mean([r["context_minus_parametric_logprob_margin"] for r in subset])
                    ),
                }
            )
    report["cell_summary"] = cell_summary

    # ---- paraphrase versus instruction, same facts -------------------------
    if args.include_policy_endpoints:
        print("\n" + "=" * 78)
        print("R2  paraphrase effect vs instruction effect, same facts, same run")
        print("=" * 78)
        policy_margins = {
            (str(r["fact_id"]), str(r["cell_id"]), str(r["policy_id"])): float(
                r["context_minus_parametric_logprob_margin"]
            )
            for r in rows
        }
        comparison: list[dict[str, Any]] = []
        for relation in relations:
            relation_facts = sorted(
                {str(r["fact_id"]) for r in rows if r["relation_id"] == relation}
            )
            paraphrase = paired_cell_delta(
                margins, relation_facts, "endpoint_high", "endpoint_low",
                args.bootstrap_replicates, int(config["project"]["seed"]),
            )
            for endpoint in ("endpoint_high", "endpoint_low"):
                flat = {
                    (f, policy): policy_margins[(f, endpoint, policy)]
                    for f in relation_facts
                    for policy in ("neutral", "context", "parametric")
                    if (f, endpoint, policy) in policy_margins
                }
                instruction = paired_cell_delta(
                    flat, relation_facts, "context", "neutral",
                    args.bootstrap_replicates, int(config["project"]["seed"]),
                )
                comparison.append(
                    {
                        "relation": relation,
                        "endpoint": endpoint,
                        "paraphrase_effect": paraphrase["delta"],
                        "paraphrase_ci95": paraphrase["ci95"],
                        "instruction_effect": instruction["delta"],
                        "instruction_ci95": instruction["ci95"],
                        "n": instruction["n"],
                    }
                )
                print(
                    f"  {relation:17s} {endpoint:15s} "
                    f"paraphrase={paraphrase['delta']:7.2f} "
                    f"[{paraphrase['ci95'][0]:+.2f}, {paraphrase['ci95'][1]:+.2f}]   "
                    f"instruction={instruction['delta']:7.2f} "
                    f"[{instruction['ci95'][0]:+.2f}, {instruction['ci95'][1]:+.2f}]"
                )
        report["paraphrase_vs_instruction"] = comparison

    # ---- outputs -----------------------------------------------------------
    write_json_atomic(args.out / "decomposition_summary.json", json_safe(report))
    csv_path = args.out / "decomposition_cells.csv"
    if cell_summary:
        with csv_path.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(cell_summary[0].keys()))
            writer.writeheader()
            writer.writerows(cell_summary)
    else:
        print("  (no cells summarised; skipping the CSV)")

    lines: list[str] = ["# E6: which part of the paragraph carries the swing?\n"]
    lines.append(
        f"Design `{args.design}`, {len(rows)} prompts, "
        f"{len(facts)} facts, neutral policy unless noted.\n"
    )
    lines.append("## Endpoint reproduction\n")
    lines.append("| Relation | Cell | Bundle | mean abs delta | max abs delta | n |")
    lines.append("|---|---|---|---:|---:|---:|")
    for entry in reproduction:
        lines.append(
            f"| {entry['relation']} | {entry['cell']} | `{entry['bundle']}` | "
            f"{entry['mean_abs_delta']:.3f} | {entry['max_abs_delta']:.3f} | {entry['n']} |"
        )
    lines.append("\n## Per-factor decomposition (margin, logits)\n")
    lines.append("| Relation | Factor | Kind | Delta | 95% CI | n |")
    lines.append("|---|---|---|---:|---:|---:|")
    for entry in contributions:
        low, high = entry["ci95"]
        interval = (
            f"[{low:+.2f}, {high:+.2f}]" if low == low else "--"
        )
        lines.append(
            f"| {entry['relation']} | {entry['factor']} | {entry['kind']} | "
            f"{entry['delta']:.2f} | {interval} | {entry['n']} |"
        )
    lines.append("\n## Behaviour per cell\n")
    lines.append("| Relation | Cell | n | Context | Parametric | Other | Mean margin |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for entry in cell_summary:
        lines.append(
            f"| {entry['relation']} | `{entry['cell']}` | {entry['n']} | "
            f"{100 * entry['context_rate']:.1f}% | {100 * entry['parametric_rate']:.1f}% | "
            f"{100 * entry['other_rate']:.1f}% | {entry['mean_margin']:.2f} |"
        )
    lines.append("\n## How to read this\n")
    lines.append(
        "- **Endpoint reproduction gates everything.** These two cells were "
        "already measured in step 02. If they do not come back, the run is not "
        "comparable and nothing else in this file means anything.\n"
        "- **Sufficiency** is `low + one factor` minus `low`: does this component "
        "alone move the model? **Necessity** is `high` minus `high with that "
        "component reverted`: does removing it collapse the effect? A component "
        "that owns the effect scores high on both.\n"
        "- **Additivity.** If the four sufficiency effects sum to roughly the "
        "endpoint gap, the factors act independently and this table is the whole "
        "story. A large residual means they interact, and the single-factor "
        "reading is wrong -- say so rather than picking the biggest bar.\n"
        "- **`claim` winning** is the interesting outcome: the two wordings differ "
        "in whether the false binding reads as a stipulation or an assertion, "
        "which is a claim about pragmatics, not about brittleness. Read the two "
        "prompts before asserting that interpretation -- the wording difference "
        "has to be one a person would actually describe that way.\n"
        "- **`constraint` winning** would mean output-format pressure drives "
        "apparent source-trust. That is a smaller mechanism but a sharper warning "
        "for anyone building context-faithfulness evals.\n"
        "- Cells are per-fact paired throughout, and intervals resample facts, so "
        "item difficulty cannot manufacture any of these differences.\n"
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"\nwrote {args.out / 'decomposition_results.jsonl'}")
    print(f"wrote {args.out / 'decomposition_summary.json'}")
    print(f"wrote {csv_path}")
    print(f"wrote {report_path}")
    print(f"elapsed {time.time() - started:.1f}s")


if __name__ == "__main__":
    main()
