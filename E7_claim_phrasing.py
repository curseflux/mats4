#!/usr/bin/env python3
"""E7: which PROPERTY of the claim sentence drives deference?
"""

from __future__ import annotations

import argparse
import collections
import csv
import itertools
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from build_conflict_awareness_dataset import RESPONSE_CONSTRAINTS, relation_specs, stable_digest
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
    render_dataset_record,
    runtime_fingerprint,
    score_continuations,
    seed_everything,
    write_json_atomic,
)


ANALYSIS_VERSION = "1.1.0"

FACTORS = ("act", "realization", "source", "persistence")

# The frame is the relation's E6 low endpoint, so the anchors below reproduce
# E6 cells exactly. Indices are into the generator's own template tables.
FRAME = {
    "element_symbol": {"filler": 2, "question": 2, "constraint": 2},
    "country_capital": {"filler": 1, "question": 1, "constraint": 1},
}

# Claim sentences. Written here rather than in the generator because they are a
# new manipulation, not a new dataset. `{s}` = query subject, `{a}` = claim answer.
SOURCES = {
    "element_symbol": {"high": "A university chemistry textbook", "low": "A classroom wall poster"},
    "country_capital": {"high": "A national geography textbook", "low": "A tourist brochure"},
}
PREDICATES = {
    # act -> realization -> verb phrase completing "{source} {adverb}<phrase>."
    "element_symbol": {
        "stipulate": {
            "r1": "uses {a} as the chemical symbol for {s}",
            "r2": "treats {a} as the chemical symbol for {s}",
        },
        "assert": {
            "r1": "states that the chemical symbol for {s} is {a}",
            "r2": "reports the chemical symbol for {s} to be {a}",
        },
    },
    "country_capital": {
        "stipulate": {
            "r1": "refers to {a} as the capital of {s}",
            "r2": "treats {a} as the capital of {s}",
        },
        "assert": {
            "r1": "states that the capital of {s} is {a}",
            "r2": "reports the capital of {s} to be {a}",
        },
    },
}
ADVERB = {"absent": "", "present": "consistently "}
BARE = {
    "element_symbol": "The chemical symbol for {s} is {a}.",
    "country_capital": "The capital of {s} is {a}.",
}
# The original E6 claim sentences, reproduced verbatim from the generator.
ORIGINAL_CLAIM_INDEX = {
    "element_symbol": {"orig_high": 1, "orig_low": 2},
    "country_capital": {"orig_high": 2, "orig_low": 1},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument("--behavior", type=Path, required=True)
    parser.add_argument(
        "--e6-results",
        type=Path,
        default=None,
        help="decomposition_results.jsonl. Enables the anchor checks: the two "
        "original claim cells must rebuild byte-identically and reproduce "
        "their margins.",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--relations", default="element_symbol,country_capital")
    parser.add_argument("--max-facts", type=int, default=None)
    parser.add_argument("--generation-batch-size", type=int, default=None)
    parser.add_argument("--scoring-batch-size", type=int, default=None)
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--analyze-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Prompt assembly (must match build_experiment_prompt under the neutral policy)
# ---------------------------------------------------------------------------


def assemble(relation: str, claim: str, subject: str) -> str:
    """context = "<claim> <filler>", then "\\n\\n", question, "\\n", constraint.

    Reproduces `build_experiment_prompt` for policy_id="neutral", where the
    policy string is empty and no policy line is emitted.
    """
    spec = relation_specs()[relation]
    frame = FRAME[relation]
    filler = spec.fillers[frame["filler"]]
    question = spec.question_templates[frame["question"]].format(query_subject=subject)
    constraint = RESPONSE_CONSTRAINTS[frame["constraint"]]
    return f"{claim} {filler}\n\n{question}\n{constraint}"


def claim_cells(relation: str) -> list[tuple[str, dict[str, str], str]]:
    """(cell_id, factor levels, claim template) for every cell."""
    spec = relation_specs()[relation]
    cells: list[tuple[str, dict[str, str], str]] = []
    for act, realization, source, persistence in itertools.product(
        ("stipulate", "assert"), ("r1", "r2"), ("high", "low"), ("absent", "present")
    ):
        phrase = PREDICATES[relation][act][realization]
        template = f"{SOURCES[relation][source]} {ADVERB[persistence]}{phrase}."
        cells.append(
            (
                f"{act}_{realization}_{source}_{persistence}",
                {
                    "act": act,
                    "realization": realization,
                    "source": source,
                    "persistence": persistence,
                },
                template,
            )
        )
    for name, index in ORIGINAL_CLAIM_INDEX[relation].items():
        cells.append(
            (name, {}, spec.claim_templates[index].replace(
                "{claim_answer}", "{a}").replace("{claim_subject}", "{s}"))
        )
    cells.append(("bare", {}, BARE[relation]))
    return cells


def build_records(
    args: argparse.Namespace, facts: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for fact in facts:
        relation = str(fact["relation_id"])
        subject = str(fact["query_subject"])
        answer = str(fact["claim_answer"])
        for cell_id, levels, template in claim_cells(relation):
            claim = template.format(s=subject, a=answer)
            prompt = assemble(relation, claim, subject)
            records.append(
                _record(fact, cell_id, levels, prompt, claim, answer, relevant=True)
            )
        # Specificity control: same acts, different entity. A lift here would
        # mean copying rather than conflict resolution.
        distractor = fact.get("distractor_subject")
        distractor_answer = fact.get("distractor_claim_answer")
        if distractor and distractor_answer:
            for act in ("stipulate", "assert"):
                phrase = PREDICATES[relation][act]["r1"]
                template = f"{SOURCES[relation]['high']} {phrase}."
                claim = template.format(s=distractor, a=distractor_answer)
                prompt = assemble(relation, claim, subject)
                records.append(
                    _record(
                        fact, f"irrelevant_{act}", {"act": act}, prompt, claim,
                        distractor_answer, relevant=False,
                    )
                )
    return records


def _record(
    fact: Mapping[str, Any],
    cell_id: str,
    levels: Mapping[str, str],
    prompt: str,
    claim: str,
    scored_answer: str,
    relevant: bool,
) -> dict[str, Any]:
    return {
        "sample_id": "phr-" + stable_digest(fact["fact_id"], cell_id, prompt),
        "raw_prompt": prompt,
        "messages": [{"role": "user", "content": prompt}],
        "semantic_positions": {"prompt_end": len(prompt)},
        "fact_id": fact["fact_id"],
        "relation_id": fact["relation_id"],
        "fact_split": fact["fact_split"],
        "cell_id": cell_id,
        "levels": dict(levels),
        "claim_sentence": claim,
        "claim_is_query_relevant": relevant,
        "context_candidate_answer": scored_answer,
        "acceptable_world_true_answers": list(fact["acceptable_world_true_answers"]),
        "parametric_candidate_answer": fact["world_true_answer"],
    }


def classify(record: Mapping[str, Any], text: str) -> str:
    """Mirrors classify_generation in 02_collect_model_data.py."""
    if not is_one_orthographic_word(text):
        return "unparseable"
    parametric = answer_matches(text, list(record["acceptable_world_true_answers"]))
    contextual = normalize_answer(text) == normalize_answer(
        record["context_candidate_answer"]
    )
    if parametric and contextual:
        return "shared_parametric_and_context"
    if parametric:
        return "parametric"
    if contextual:
        return "contextual"
    return "other"


def paired_mean_delta(
    values: Mapping[tuple[str, str], float],
    facts: Sequence[str],
    cells_a: Sequence[str],
    cells_b: Sequence[str],
    replicates: int,
    seed: int,
) -> dict[str, Any]:
    """mean(values over cells_a) - mean(over cells_b), paired within fact.

    Averaging over the other factors' levels before differencing is what makes
    this a main effect rather than one arbitrary slice.
    """
    import numpy as np

    usable, deltas = [], []
    for fact in facts:
        a = [values[(fact, c)] for c in cells_a if (fact, c) in values]
        b = [values[(fact, c)] for c in cells_b if (fact, c) in values]
        if not a or not b:
            continue
        usable.append(fact)
        deltas.append(float(np.mean(a) - np.mean(b)))
    if not usable:
        return {"delta": float("nan"), "ci95": [float("nan"), float("nan")], "n": 0}
    array = np.asarray(deltas)
    low, high = cluster_bootstrap(
        usable, lambda picked: float(np.mean(array[picked])), replicates, seed
    )
    return {"delta": float(array.mean()), "ci95": [low, high], "n": len(usable)}


def main() -> None:
    import numpy as np

    started = time.time()
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    results_path = args.out / "phrasing_results.jsonl"
    partial_path = args.out / "phrasing_results.jsonl.partial"
    report_path = args.out / "phrasing_report.md"
    if args.analyze_only and args.validate_only:
        raise ValueError("--analyze-only and --validate-only are mutually exclusive")
    if (
        results_path.exists()
        and not args.overwrite
        and not args.validate_only
        and not args.analyze_only
    ):
        raise FileExistsError(f"Refusing to overwrite {results_path}; pass --overwrite")

    config = load_config(args.config)
    relations = [r.strip() for r in args.relations.split(",") if r.strip()]
    behaviour = read_jsonl(args.behavior)

    # Facts, false answers and distractors all come from the run we are extending.
    distractor_by_fact: dict[str, tuple[str, str]] = {}
    for row in behaviour:
        if str(row["condition_id"]) == "false_irrelevant" and str(row["policy_id"]) == "neutral":
            distractor_by_fact[str(row["fact_id"])] = (
                str(row["claim_subject"]),
                str(row["claim_answer"]),
            )
    facts: list[dict[str, Any]] = []
    seen: set[str] = set()
    per_relation: collections.Counter = collections.Counter()
    for row in behaviour:
        if (
            str(row["condition_id"]) != "false_relevant"
            or str(row["policy_id"]) != "neutral"
            or str(row["relation_id"]) not in relations
            or str(row["fact_id"]) in seen
        ):
            continue
        relation = str(row["relation_id"])
        if args.max_facts is not None and per_relation[relation] >= args.max_facts:
            continue
        seen.add(str(row["fact_id"]))
        per_relation[relation] += 1
        distractor = distractor_by_fact.get(str(row["fact_id"]), (None, None))
        facts.append(
            {
                "fact_id": row["fact_id"],
                "relation_id": relation,
                "fact_split": row["fact_split"],
                "query_subject": row["query_subject"],
                "claim_answer": row["claim_answer"],
                "world_true_answer": row["world_true_answer"],
                "acceptable_world_true_answers": row["acceptable_world_true_answers"],
                "distractor_subject": distractor[0],
                "distractor_claim_answer": distractor[1],
            }
        )
    if not facts:
        raise ValueError("No facts matched; check --relations and the behaviour file")
    print(f"facts: {dict(per_relation)}")

    records = build_records(args, facts)
    print(f"cells/fact: {len(records) / len(facts):.1f}   prompts: {len(records)}")

    # ---- anchor check: the two original claims must rebuild exactly ---------
    e6_rows = read_jsonl(args.e6_results) if args.e6_results else []
    e6_prompt = {
        (str(r["fact_id"]), str(r["cell_id"])): str(r["raw_prompt"])
        for r in e6_rows
        if str(r["policy_id"]) == "neutral"
    }
    e6_margin = {
        (str(r["fact_id"]), str(r["cell_id"])): float(
            r["context_minus_parametric_logprob_margin"]
        )
        for r in e6_rows
        if str(r["policy_id"]) == "neutral"
    }
    anchor_to_e6 = {"orig_low": "endpoint_low", "orig_high": "low_plus_claim"}
    checked = mismatched = 0
    for record in records:
        e6_cell = anchor_to_e6.get(str(record["cell_id"]))
        if e6_cell is None:
            continue
        expected = e6_prompt.get((str(record["fact_id"]), e6_cell))
        if expected is None:
            continue
        checked += 1
        if expected != record["raw_prompt"]:
            mismatched += 1
            if mismatched <= 2:
                print(f"\nANCHOR MISMATCH ({record['cell_id']} vs E6 {e6_cell})")
                print(f"  E6 : {expected!r}")
                print(f"  E7 : {record['raw_prompt']!r}")
    if checked:
        print(f"anchor prompts: {checked - mismatched}/{checked} identical to E6")
        if mismatched:
            raise RuntimeError(
                "Anchor prompts differ from E6. The frame or assembly has drifted; "
                "the anchors would no longer be comparable."
            )
    else:
        print("anchor prompts: SKIPPED (pass --e6-results to enable)")

    if args.validate_only:
        for relation in relations:
            example = next(f for f in facts if f["relation_id"] == relation)
            print(f"\n{'=' * 78}\n{relation}: all claim sentences for {example['query_subject']}\n{'=' * 78}")
            for record in records:
                if record["fact_id"] != example["fact_id"]:
                    continue
                print(f"  [{record['cell_id']:34s}] {record['claim_sentence']}")
            print("\n  full prompt for one cell:\n")
            print(next(r["raw_prompt"] for r in records if r["fact_id"] == example["fact_id"]))
        print(f"\nvalidate-only: {len(records)} prompts would be evaluated")
        return

    # ---- run ---------------------------------------------------------------
    if args.analyze_only:
        if not results_path.is_file():
            raise FileNotFoundError(f"--analyze-only needs an existing {results_path}")
        rows = read_jsonl(results_path)
        fingerprint: Any = {"note": "analyze-only; the model was not loaded"}
        print(f"analyze-only: reusing {len(rows)} scored prompts")
    else:
        seed_everything(int(config["project"]["seed"]))
        done: set[str] = set()
        if partial_path.exists() and not args.overwrite:
            done = {str(r["sample_id"]) for r in read_jsonl(partial_path)}
            print(f"resuming: {len(done)} prompts already scored")
        elif partial_path.exists():
            partial_path.unlink()
        pending = [r for r in records if r["sample_id"] not in done]

        bundle = load_model_bundle(config)
        dataset_files: dict[str, Any] = {"behavior": args.behavior}
        if args.e6_results:
            dataset_files["e6_results"] = args.e6_results
        fingerprint = runtime_fingerprint(config, bundle, dataset_files)
        generation_batch = args.generation_batch_size or int(
            config["collection"]["generation_batch_size"]
        )
        scoring_batch = args.scoring_batch_size or int(
            config["collection"]["scoring_batch_size"]
        )
        max_input = int(config["chat"]["max_input_tokens"])

        # Duplicates E6's loop rather than importing it; E6 has already run
        # end to end and a refactor here costs a 12B model load per failure.
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
                for alias, answer in enumerate(record["acceptable_world_true_answers"]):
                    requests.append(
                        {
                            "key": f"{index}|parametric|{alias}",
                            "rendered_text": texts[index],
                            "continuation": str(answer),
                        }
                    )
            scores = score_continuations(
                bundle.model, bundle.tokenizer, requests, scoring_batch, max_input
            )
            by_key = {s.key: s for s in scores}

            output = []
            for index, record in enumerate(chunk):
                context_score = by_key[f"{index}|context"]
                best = max(
                    (
                        by_key[f"{index}|parametric|{alias}"]
                        for alias in range(len(record["acceptable_world_true_answers"]))
                    ),
                    key=lambda s: s.sum_logprob,
                )
                generation = generations[index]
                text = generation["text"]
                # See the note in E6: classify the stripped answer so these
                # rates are comparable to E8 and later.
                answer = str(generation.get("answer_text") or text)
                output.append(
                    {
                        "code_version": CODE_VERSION,
                        "analysis_version": ANALYSIS_VERSION,
                        **{
                            k: record[k]
                            for k in (
                                "sample_id", "fact_id", "relation_id", "fact_split",
                                "cell_id", "levels", "claim_sentence",
                                "claim_is_query_relevant", "raw_prompt",
                            )
                        },
                        "generated_answer": text,
                        "generated_answer_stripped": answer,
                        "had_reasoning_preamble": bool(
                            generation.get("had_reasoning_preamble", False)
                        ),
                        "format_compliant": is_one_orthographic_word(text),
                        "observed_knowledge_source": classify(record, answer),
                        "context_answer": record["context_candidate_answer"],
                        "parametric_answer": best.continuation,
                        "context_answer_sequence_logprob": context_score.sum_logprob,
                        "parametric_answer_sequence_logprob": best.sum_logprob,
                        "context_minus_parametric_logprob_margin": (
                            context_score.sum_logprob - best.sum_logprob
                        ),
                    }
                )
            append_jsonl(partial_path, output)
            if (start // generation_batch) % 20 == 0:
                print(f"  {start + len(chunk)}/{len(pending)} ({time.time() - started:7.1f}s)")

        rows = read_jsonl(partial_path)
        finalize_jsonl(partial_path, results_path)
        print(f"\nscored {len(rows)} prompts")

    # ---- analysis ----------------------------------------------------------
    report: dict[str, Any] = {
        "analysis_version": ANALYSIS_VERSION,
        "runtime": fingerprint,
        "frame": FRAME,
        "factors": list(FACTORS),
    }
    relevant = [r for r in rows if r.get("claim_is_query_relevant", True)]
    margins = {
        (str(r["fact_id"]), str(r["cell_id"])): float(
            r["context_minus_parametric_logprob_margin"]
        )
        for r in relevant
    }
    seed = int(config["project"]["seed"])

    print("\n" + "=" * 78)
    print("A0  anchor reproduction against E6")
    print("=" * 78)
    anchors: list[dict[str, Any]] = []
    for relation in relations:
        for anchor, e6_cell in anchor_to_e6.items():
            deltas = [
                margins[(str(r["fact_id"]), anchor)] - e6_margin[(str(r["fact_id"]), e6_cell)]
                for r in relevant
                if r["relation_id"] == relation
                and r["cell_id"] == anchor
                and (str(r["fact_id"]), e6_cell) in e6_margin
            ]
            if not deltas:
                continue
            entry = {
                "relation": relation, "anchor": anchor, "e6_cell": e6_cell,
                "mean_abs_delta": float(np.mean(np.abs(deltas))),
                "max_abs_delta": float(np.max(np.abs(deltas))), "n": len(deltas),
            }
            anchors.append(entry)
            print(
                f"  {relation:17s} {anchor:10s} vs E6 {e6_cell:16s} "
                f"mean|d|={entry['mean_abs_delta']:6.3f} max|d|={entry['max_abs_delta']:7.3f}"
            )
    report["anchor_reproduction"] = anchors
    print("  (the BF16 batch-width floor in this pipeline is ~0.4 mean, ~3.7 max)")

    print("\n" + "=" * 78)
    print("A1  main effect of each claim property (margin, logits)")
    print("    Each is averaged over all levels of the other three factors.")
    print("=" * 78)
    effects: list[dict[str, Any]] = []
    contrasts = {
        "act": ("stipulate", "assert"),
        "realization": ("r1", "r2"),
        "source": ("high", "low"),
        "persistence": ("present", "absent"),
    }
    for relation in relations:
        relation_facts = sorted({str(r["fact_id"]) for r in relevant if r["relation_id"] == relation})
        cells = [(c, lv) for c, lv, _ in claim_cells(relation) if lv]
        print(f"\n--- {relation} ---")
        print(f"  {'factor':14s}{'contrast':26s}{'delta':>9s}{'95% CI':>22s}")
        for factor, (plus, minus) in contrasts.items():
            a = [c for c, lv in cells if lv[factor] == plus]
            b = [c for c, lv in cells if lv[factor] == minus]
            result = paired_mean_delta(
                margins, relation_facts, a, b, args.bootstrap_replicates, seed
            )
            low, high = result["ci95"]
            star = "***" if (low > 0 or high < 0) else "   "
            effects.append({"relation": relation, "factor": factor,
                            "contrast": f"{plus} - {minus}", **result})
            print(
                f"  {factor:14s}{plus + ' - ' + minus:26s}{result['delta']:>9.2f}"
                f"{f'[{low:+.2f}, {high:+.2f}]':>22} {star}"
            )
        for anchor in ("orig_high", "orig_low", "bare"):
            values = [margins[(f, anchor)] for f in relation_facts if (f, anchor) in margins]
            if values:
                print(f"  {'anchor':14s}{anchor:26s}{float(np.mean(values)):>9.2f}")
    report["main_effects"] = effects

    print("\n" + "=" * 78)
    print("A2  specificity control: claim about a DIFFERENT entity")
    print("    A phrasing effect here would mean copying, not conflict resolution.")
    print("=" * 78)
    control: list[dict[str, Any]] = []
    irrelevant = [r for r in rows if not r.get("claim_is_query_relevant", True)]
    control_margins = {
        (str(r["fact_id"]), str(r["cell_id"])): float(
            r["context_minus_parametric_logprob_margin"]
        )
        for r in irrelevant
    }
    for relation in relations:
        relation_facts = sorted({str(r["fact_id"]) for r in irrelevant if r["relation_id"] == relation})
        if not relation_facts:
            continue
        result = paired_mean_delta(
            control_margins, relation_facts, ["irrelevant_stipulate"],
            ["irrelevant_assert"], args.bootstrap_replicates, seed,
        )
        low, high = result["ci95"]
        control.append({"relation": relation, **result})
        print(
            f"  {relation:17s} stipulate - assert (irrelevant claim) "
            f"{result['delta']:7.2f} [{low:+.2f}, {high:+.2f}]  n={result['n']}"
        )
    report["specificity_control"] = control

    cell_summary: list[dict[str, Any]] = []
    for relation in relations:
        for cell in sorted({str(r["cell_id"]) for r in rows}):
            subset = [r for r in rows if r["relation_id"] == relation and r["cell_id"] == cell]
            if not subset:
                continue
            counts = collections.Counter(r["observed_knowledge_source"] for r in subset)
            n = len(subset)
            cell_summary.append({
                "relation": relation, "cell": cell, "n": n,
                "context_rate": counts.get("contextual", 0) / n,
                "parametric_rate": counts.get("parametric", 0) / n,
                "other_rate": (counts.get("other", 0) + counts.get("unparseable", 0)) / n,
                "mean_margin": float(
                    np.mean([r["context_minus_parametric_logprob_margin"] for r in subset])
                ),
            })
    report["cell_summary"] = cell_summary

    write_json_atomic(args.out / "phrasing_summary.json", json_safe(report))
    if cell_summary:
        with (args.out / "phrasing_cells.csv").open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(cell_summary[0].keys()))
            writer.writeheader()
            writer.writerows(cell_summary)

    lines = ["# E7: which property of the claim sentence drives deference?\n"]
    lines.append(
        f"{len(rows)} prompts, {len(facts)} facts, neutral policy. Subject, false "
        "answer, filler, question and response constraint are held fixed at each "
        "relation's E6 low-endpoint frame; only the claim sentence varies.\n"
    )
    lines.append("## Main effects (margin, logits)\n")
    lines.append("| Relation | Factor | Contrast | Delta | 95% CI | n |")
    lines.append("|---|---|---|---:|---:|---:|")
    for entry in effects:
        low, high = entry["ci95"]
        lines.append(
            f"| {entry['relation']} | {entry['factor']} | {entry['contrast']} | "
            f"{entry['delta']:.2f} | [{low:+.2f}, {high:+.2f}] | {entry['n']} |"
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
        "- **`act` is the hypothesis.** A large positive stipulate-minus-assert "
        "effect in BOTH relations, surviving the `realization` control, means the "
        "model treats a source that ADOPTS a convention differently from one that "
        "ASSERTS a fact. That is a claim about pragmatics, and it is the version "
        "of this finding worth writing up.\n"
        "- **`realization` is the killer control.** If swapping one verb for a "
        "synonym of the same act moves the margin as much as changing the act, "
        "the result is lexical and the pragmatic reading is wrong. Report this "
        "number next to `act`, never on its own.\n"
        "- **`source` and `persistence`** are the two obvious alternative "
        "explanations for E6's endpoint gap. If either rivals `act`, say so.\n"
        "- **`bare`** shows where an unattributed assertion sits. If it lands "
        "near the assert cells, attribution is not what matters; if it is far "
        "from both, the whole effect depends on there being a source at all.\n"
        "- **A2 must be near zero.** A phrasing that lifts the claim answer even "
        "when the claim is about another entity is a salience effect, and the "
        "conflict-resolution reading would be wrong.\n"
        "- Anchors are the E6 cells rebuilt here. If they do not reproduce, "
        "nothing above is comparable to E6 and the frame has drifted.\n"
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwrote {args.out / 'phrasing_summary.json'}")
    print(f"wrote {report_path}")
    print(f"elapsed {time.time() - started:.1f}s")


if __name__ == "__main__":
    main()
