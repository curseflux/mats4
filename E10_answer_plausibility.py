#!/usr/bin/env python3
"""E10: is the relation the variable, or is it how plausible the false answer is?
"""

from __future__ import annotations

import argparse
import collections
import csv
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from build_conflict_awareness_dataset import CAPITAL_ROWS, ELEMENT_ROWS, POLICY_TEMPLATES
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

from E8_conventionality import (
    BARE,
    CONSTRAINT,
    EXPLICIT,
    PREDICATES,
    SOURCE,
    STIPULABLE,
    assemble,
    seeded_derangement,
    stable_seed,
)

ANALYSIS_VERSION = "1.0.0"

RELATIONS = ("element_atomic_number", "element_symbol", "country_capital")

# E8 act-effect cells minus the gap cells, same names and templates so the
# numbers are comparable to E8 cell for cell.
CELLS = ("stipulate_r1", "stipulate_r2", "assert_r1", "assert_r2", "bare", "explicit_stipulation")

# Numeric offsets for the one relation where distance is a real number line.
NUMERIC_DISTANCES = (1, 2, 5, 20)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--relations", default=",".join(RELATIONS))
    parser.add_argument(
        "--policies",
        default="neutral",
        help="`neutral` is where deference is graded; "
        "ignore-the-paragraph instruction the leakage gradient lives under. "
        "`context` is saturated near 100% and is off by default.",
    )
    parser.add_argument("--seed", type=int, default=20260816)
    parser.add_argument("--max-facts", type=int, default=None)
    parser.add_argument("--generation-batch-size", type=int, default=None)
    parser.add_argument("--scoring-batch-size", type=int, default=None)
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    parser.add_argument("--skip-screening", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--analyze-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Facts, crossed with distance
# ---------------------------------------------------------------------------


def _numeric_false(true_z: int, offset: int, ceiling: int) -> int:
    """true_z +/- offset, reflected at the ends so |false - true| == offset."""
    candidate = true_z + offset
    if candidate > ceiling:
        candidate = true_z - offset
    if candidate < 1:
        raise ValueError(f"offset {offset} does not fit around Z={true_z}")
    return candidate


def build_facts(relations: Sequence[str], seed: int, max_facts: int | None) -> list[dict[str, Any]]:
    """One record per (subject, distance level).

    `distance_id` is the manipulation. `numeric_distance` is filled in only for
    atomic numbers, where it is meaningful; elsewhere the levels are `near`
    (the adjacent row's answer) and `random` (a seeded derangement).
    """
    facts: list[dict[str, Any]] = []
    for relation in relations:
        if relation == "element_atomic_number":
            rows = [(name, str(index + 1)) for index, (name, _) in enumerate(ELEMENT_ROWS)]
        elif relation == "element_symbol":
            rows = [(name, symbol) for name, symbol in ELEMENT_ROWS]
        elif relation == "country_capital":
            rows = [(country, capital) for country, capital in CAPITAL_ROWS]
        else:
            raise ValueError(f"Unknown relation {relation!r}")

        # Derange over the full relation, then truncate, so a pilot's
        # assignments match the full run's.
        permutation = seeded_derangement(len(rows), stable_seed(seed, relation, "random"))
        random_answer = {subject: rows[permutation[i]][1] for i, (subject, _) in enumerate(rows)}
        # `near` is the adjacent row, reflected at the end of the list.
        near_answer = {
            subject: rows[i + 1][1] if i + 1 < len(rows) else rows[i - 1][1]
            for i, (subject, _) in enumerate(rows)
        }

        selected = rows[:max_facts] if max_facts is not None else rows
        for index, (subject, answer) in enumerate(selected):
            levels: list[tuple[str, str, int | None]] = []
            if relation == "element_atomic_number":
                for offset in NUMERIC_DISTANCES:
                    false_z = _numeric_false(index + 1, offset, len(rows))
                    levels.append((f"d{offset}", str(false_z), offset))
                false_random = random_answer[subject]
                levels.append(("random", false_random, abs(int(false_random) - (index + 1))))
            else:
                levels.append(("near", near_answer[subject], None))
                levels.append(("random", random_answer[subject], None))

            for distance_id, false_answer, numeric in levels:
                if normalize_answer(false_answer) == normalize_answer(answer):
                    continue
                facts.append(
                    {
                        "fact_id": f"{relation}:{subject.casefold().replace(' ', '-')}",
                        "relation_id": relation,
                        "query_subject": subject,
                        "world_true_answer": answer,
                        "acceptable_world_true_answers": [answer],
                        "claim_answer": false_answer,
                        "distance_id": distance_id,
                        "numeric_distance": numeric,
                    }
                )
    return facts


def claim_sentence(relation: str, cell: str, subject: str, answer: str) -> str:
    if cell == "bare":
        template = BARE[relation]
    elif cell == "explicit_stipulation":
        template = EXPLICIT[relation]
    else:
        act, realization = cell.rsplit("_", 1)
        template = f"{SOURCE[relation]} {PREDICATES[relation][act][realization]}."
    return template.format(s=subject, a=answer)


def build_records(
    facts: Sequence[Mapping[str, Any]],
    policies: Sequence[str],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for fact in facts:
        relation = str(fact["relation_id"])
        subject = str(fact["query_subject"])
        answer = str(fact["claim_answer"])
        for cell in CELLS:
            claim = claim_sentence(relation, cell, subject, answer)
            for policy in policies:
                prompt = assemble(relation, claim, subject, policy)
                records.append(
                    {
                        "sample_id": (
                            f"e10-{relation}-{fact['fact_id']}-"
                            f"{fact['distance_id']}-{cell}-{policy}"
                        ),
                        "raw_prompt": prompt,
                        "messages": [{"role": "user", "content": prompt}],
                        "semantic_positions": {"prompt_end": len(prompt)},
                        "fact_id": fact["fact_id"],
                        "relation_id": relation,
                        "distance_id": fact["distance_id"],
                        "numeric_distance": fact["numeric_distance"],
                        "cell_id": cell,
                        "policy_id": policy,
                        "claim_sentence": claim,
                        "context_candidate_answer": answer,
                        "acceptable_world_true_answers": list(
                            fact["acceptable_world_true_answers"]
                        ),
                        "parametric_candidate_answer": fact["world_true_answer"],
                    }
                )
    return records


def screening_record(relation: str, subject: str, true_answer: str) -> dict[str, Any]:
    question = {
        "element_symbol": "Give the chemical symbol of {s}.",
        "element_atomic_number": "Give the atomic number of {s}.",
        "country_capital": "Which city is the capital of {s}?",
    }[relation].format(s=subject)
    return {
        "sample_id": f"e10screen-{relation}:{subject.casefold().replace(' ', '-')}",
        "raw_prompt": f"{question}\n{CONSTRAINT[relation]}",
        "messages": [
            {"role": "user", "content": f"{question}\n{CONSTRAINT[relation]}"}
        ],
        "semantic_positions": {"prompt_end": len(f"{question}\n{CONSTRAINT[relation]}")},
        "relation_id": relation,
        "query_subject": subject,
        "world_true_answer": true_answer,
    }


def classify(record: Mapping[str, Any], text: str) -> str:
    if not is_one_orthographic_word(text):
        return "unparseable"
    parametric = answer_matches(text, list(record["acceptable_world_true_answers"]))
    contextual = normalize_answer(text) == normalize_answer(record["context_candidate_answer"])
    if parametric and contextual:
        return "shared_parametric_and_context"
    if parametric:
        return "parametric"
    if contextual:
        return "contextual"
    return "other"


def screen(
    facts: Sequence[Mapping[str, Any]],
    bundle: Any,
    config: Mapping[str, Any],
    generation_batch: int,
    scoring_batch: int,
) -> tuple[set[str], dict[tuple[str, str], float]]:
    """Context-free screen, plus per-distance knowledge strength.

    Returns the fact_ids that pass, and log P(true) - log P(false at distance d)
    for every (fact_id, distance_id). The gate uses the `random` distance only,
    so which facts survive does not depend on the manipulation.
    """
    max_input = int(config["chat"]["max_input_tokens"])
    by_subject: dict[str, dict[str, Any]] = {}
    false_by_fact: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    for fact in facts:
        by_subject.setdefault(
            str(fact["fact_id"]),
            {
                "relation_id": str(fact["relation_id"]),
                "query_subject": str(fact["query_subject"]),
                "world_true_answer": str(fact["world_true_answer"]),
            },
        )
        false_by_fact[str(fact["fact_id"])].append(
            (str(fact["distance_id"]), str(fact["claim_answer"]))
        )

    fact_ids = sorted(by_subject)
    passed: set[str] = set()
    strength: dict[tuple[str, str], float] = {}
    for start in range(0, len(fact_ids), generation_batch):
        chunk = fact_ids[start : start + generation_batch]
        records = [
            screening_record(
                by_subject[f]["relation_id"],
                by_subject[f]["query_subject"],
                by_subject[f]["world_true_answer"],
            )
            for f in chunk
        ]
        rendered = [render_dataset_record(bundle.processor, r, config) for r in records]
        texts = [r.rendered_text for r in rendered]
        generations = generate_batch(bundle.model, bundle.tokenizer, texts, config)

        requests: list[dict[str, str]] = []
        for index, fact_id in enumerate(chunk):
            requests.append(
                {
                    "key": f"{index}|true",
                    "rendered_text": texts[index],
                    "continuation": by_subject[fact_id]["world_true_answer"],
                }
            )
            for distance_id, false_answer in false_by_fact[fact_id]:
                requests.append(
                    {
                        "key": f"{index}|false|{distance_id}",
                        "rendered_text": texts[index],
                        "continuation": false_answer,
                    }
                )
        scores = score_continuations(
            bundle.model, bundle.tokenizer, requests, scoring_batch, max_input
        )
        by_key = {s.key: s for s in scores}

        for index, fact_id in enumerate(chunk):
            true_lp = by_key[f"{index}|true"].sum_logprob
            for distance_id, _ in false_by_fact[fact_id]:
                strength[(fact_id, distance_id)] = (
                    true_lp - by_key[f"{index}|false|{distance_id}"].sum_logprob
                )
            generation = generations[index]
            answer = str(generation.get("answer_text") or generation["text"])
            generated_true = is_one_orthographic_word(answer) and answer_matches(
                answer, [by_subject[fact_id]["world_true_answer"]]
            )
            if generated_true and strength.get((fact_id, "random"), -1.0) > 0:
                passed.add(fact_id)
    return passed, strength


def evaluate(
    records: Sequence[Mapping[str, Any]],
    bundle: Any,
    config: Mapping[str, Any],
    partial_path: Path,
    generation_batch: int,
    scoring_batch: int,
    strength: Mapping[tuple[str, str], float],
    started: float,
) -> None:
    max_input = int(config["chat"]["max_input_tokens"])
    for start in range(0, len(records), generation_batch):
        chunk = records[start : start + generation_batch]
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
            # Stripped, as E8 does. E6/E7 classify the unstripped decode, which
            # is why their "other" column runs to 41% where E8's is 0%.
            answer = str(generation.get("answer_text") or generation["text"])
            output.append(
                {
                    "code_version": CODE_VERSION,
                    "analysis_version": ANALYSIS_VERSION,
                    **{
                        k: record[k]
                        for k in (
                            "sample_id", "fact_id", "relation_id", "distance_id",
                            "numeric_distance", "cell_id", "policy_id",
                            "claim_sentence", "raw_prompt",
                        )
                    },
                    "generated_answer": generation["text"],
                    "generated_answer_stripped": answer,
                    "had_reasoning_preamble": bool(
                        generation.get("had_reasoning_preamble", False)
                    ),
                    "format_compliant": is_one_orthographic_word(generation["text"]),
                    "observed_knowledge_source": classify(record, answer),
                    "context_answer": record["context_candidate_answer"],
                    "parametric_answer": best.continuation,
                    "knowledge_strength_at_distance": strength.get(
                        (str(record["fact_id"]), str(record["distance_id"]))
                    ),
                    "context_answer_sequence_logprob": context_score.sum_logprob,
                    "parametric_answer_sequence_logprob": best.sum_logprob,
                    "context_minus_parametric_logprob_margin": (
                        context_score.sum_logprob - best.sum_logprob
                    ),
                }
            )
        append_jsonl(partial_path, output)
        if (start // generation_batch) % 20 == 0:
            print(f"  {start + len(chunk)}/{len(records)} ({time.time() - started:7.1f}s)")


def paired_delta(
    margins: Mapping[tuple[str, str], float],
    facts: Sequence[str],
    cells_a: Sequence[str],
    cells_b: Sequence[str],
    replicates: int,
    seed: int,
) -> dict[str, Any]:
    import numpy as np

    usable, deltas = [], []
    for fact in facts:
        a = [margins[(fact, c)] for c in cells_a if (fact, c) in margins]
        b = [margins[(fact, c)] for c in cells_b if (fact, c) in margins]
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
    results_path = args.out / "plausibility_results.jsonl"
    partial_path = args.out / "plausibility_results.jsonl.partial"
    report_path = args.out / "plausibility_report.md"
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
    for relation in relations:
        if relation not in RELATIONS:
            raise ValueError(f"Unknown relation {relation!r}; expected {RELATIONS}")
    policies = [p.strip() for p in args.policies.split(",") if p.strip()]
    for policy in policies:
        if policy not in POLICY_TEMPLATES:
            raise ValueError(f"Unknown policy {policy!r}")

    facts = build_facts(relations, args.seed, args.max_facts)
    print(f"model: {config['model']['id']}  (family {config['model'].get('family','gemma4')})")
    per_level = collections.Counter(
        (f["relation_id"], f["distance_id"]) for f in facts
    )
    for key in sorted(per_level):
        print(f"  {key[0]:24s} {key[1]:8s} {per_level[key]:4d} facts")

    if args.validate_only:
        for relation in relations:
            print(f"\n{'=' * 78}\n{relation}  (stipulable: {STIPULABLE[relation]})\n{'=' * 78}")
            examples = [f for f in facts if f["relation_id"] == relation]
            subject = examples[0]["query_subject"]
            for fact in [f for f in examples if f["query_subject"] == subject]:
                print(
                    f"  [{fact['distance_id']:7s}] true={fact['world_true_answer']:>14s}"
                    f"   false={fact['claim_answer']:>14s}"
                    f"   numeric_distance={fact['numeric_distance']}"
                )
            fact = examples[0]
            for cell in CELLS:
                print(
                    f"  [{cell:22s}] "
                    f"{claim_sentence(relation, cell, fact['query_subject'], fact['claim_answer'])}"
                )
            print("\n  full prompt:")
            print(
                assemble(
                    relation,
                    claim_sentence(relation, "assert_r1", fact["query_subject"], fact["claim_answer"]),
                    fact["query_subject"],
                    policies[-1],
                )
            )
        experiment = build_records(facts, policies)
        screens = len({f["fact_id"] for f in facts})
        print(f"\nvalidate-only: {screens} screening + {len(experiment)} experimental prompts")
        return

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

        bundle = load_model_bundle(config)
        fingerprint = runtime_fingerprint(config, bundle, {})
        generation_batch = args.generation_batch_size or int(
            config["collection"]["generation_batch_size"]
        )
        scoring_batch = args.scoring_batch_size or int(
            config["collection"]["scoring_batch_size"]
        )

        print("\nscreening (context-free), and measuring strength at every distance")
        passed, strength = screen(facts, bundle, config, generation_batch, scoring_batch)
        if not args.skip_screening:
            before = len({f["fact_id"] for f in facts})
            facts = [f for f in facts if f["fact_id"] in passed]
            after = len({f["fact_id"] for f in facts})
            print(f"  kept {after}/{before} facts")
            for relation in relations:
                kept = len({f["fact_id"] for f in facts if f["relation_id"] == relation})
                print(f"    {relation:24s} {kept:4d}")
            if not facts:
                raise RuntimeError("No facts survived screening")

        experiment = [r for r in build_records(facts, policies) if r["sample_id"] not in done]
        print(f"\nscoring {len(experiment)} experimental prompts")
        evaluate(experiment, bundle, config, partial_path, generation_batch,
                 scoring_batch, strength, started)
        rows = read_jsonl(partial_path)
        finalize_jsonl(partial_path, results_path)
        print(f"\nscored {len(rows)} prompts total")

    # ---- analysis ----------------------------------------------------------
    seed = int(config["project"]["seed"])
    report: dict[str, Any] = {
        "analysis_version": ANALYSIS_VERSION,
        "runtime": fingerprint,
        "model": config["model"]["id"],
        "numeric_distances": list(NUMERIC_DISTANCES),
    }
    order = {"d1": 0, "d2": 1, "d5": 2, "d20": 3, "near": 0, "random": 9}

    def distances_for(relation: str, subset: Sequence[Mapping[str, Any]]) -> list[str]:
        return sorted(
            {str(r["distance_id"]) for r in subset if r["relation_id"] == relation},
            key=lambda d: order.get(d, 5),
        )

    print("\n" + "=" * 78)
    print("A1  deference vs distance  (neutral policy, per cell)")
    print("=" * 78)
    a1 = []
    neutral = [r for r in rows if str(r["policy_id"]) == "neutral"]
    for relation in relations:
        print(f"\n{relation}")
        header = "".join(f"{d:>18s}" for d in distances_for(relation, neutral))
        print(f"  {'cell':22s}{header}")
        for cell in CELLS:
            parts = []
            for distance in distances_for(relation, neutral):
                group = [
                    r for r in neutral
                    if r["relation_id"] == relation
                    and r["distance_id"] == distance
                    and r["cell_id"] == cell
                ]
                if not group:
                    parts.append(f"{'--':>18s}")
                    continue
                rate = float(np.mean(
                    [r["observed_knowledge_source"] == "contextual" for r in group]
                ))
                margin = float(np.mean(
                    [r["context_minus_parametric_logprob_margin"] for r in group]
                ))
                parts.append(f"{100 * rate:>9.1f}% {margin:>7.2f}")
                a1.append({
                    "relation": relation, "cell": cell, "distance": distance,
                    "policy": "neutral", "context_rate": rate, "mean_margin": margin,
                    "n": len(group),
                    "mean_strength": float(np.mean([
                        r["knowledge_strength_at_distance"] for r in group
                        if r.get("knowledge_strength_at_distance") is not None
                    ])) if any(
                        r.get("knowledge_strength_at_distance") is not None for r in group
                    ) else None,
                })
            print(f"  {cell:22s}" + "".join(parts))
    print("\n  Each cell is context-following% then mean margin.")
    report["deference_by_distance"] = a1

    print("\n" + "=" * 78)
    print("A2  THE DECISIVE TEST: act effect (stipulate - assert) at each distance")
    print("=" * 78)
    print("  E8 reported -10.83 for atomic numbers, where every false answer was")
    print("  true+1. If the sign flip is real it should hold at d=5, d=20 and")
    print("  random. If it is a plausibility artefact it will move toward zero.")
    a2 = []
    print(f"\n  {'relation':24s}{'distance':10s}{'act effect':>12s}{'95% CI':>22s}{'n':>6s}")
    for relation in relations:
        for distance in distances_for(relation, neutral):
            subset = [
                r for r in neutral
                if r["relation_id"] == relation and r["distance_id"] == distance
            ]
            margins = {
                (str(r["fact_id"]), str(r["cell_id"])): float(
                    r["context_minus_parametric_logprob_margin"]
                )
                for r in subset
            }
            fact_ids = sorted({str(r["fact_id"]) for r in subset})
            result = paired_delta(
                margins, fact_ids,
                ["stipulate_r1", "stipulate_r2"], ["assert_r1", "assert_r2"],
                args.bootstrap_replicates, seed,
            )
            low, high = result["ci95"]
            a2.append({"relation": relation, "distance": distance, **result})
            print(
                f"  {relation:24s}{distance:10s}{result['delta']:>12.2f}"
                f"{f'[{low:+.2f}, {high:+.2f}]':>22}{result['n']:>6d}"
            )
    report["act_effect_by_distance"] = a2

    print("\n" + "=" * 78)
    print("A4  does strength mediate it?  (entity fixed, distance varying)")
    print("=" * 78)
    print("  E9 could not ask this: its strength measure was defined against the")
    print("  same confounded false answer. Here the entity is held fixed and only")
    print("  the false answer moves, so strength and distance vary together")
    print("  within a single fact.")
    a4 = []
    try:
        from scipy import stats as scipy_stats
    except ImportError:
        scipy_stats = None
    for relation in relations:
        for cell in ("bare", "assert_r1"):
            subset = [
                r for r in neutral
                if r["relation_id"] == relation
                and r["cell_id"] == cell
                and r.get("knowledge_strength_at_distance") is not None
            ]
            if len(subset) < 10:
                continue
            strengths = np.asarray([r["knowledge_strength_at_distance"] for r in subset])
            margins = np.asarray([r["context_minus_parametric_logprob_margin"] for r in subset])
            if scipy_stats is not None:
                rho = float(scipy_stats.spearmanr(strengths, margins).statistic)
            else:
                rho = float(np.corrcoef(strengths, margins)[0, 1])
            a4.append({
                "relation": relation, "cell": cell, "rho_strength_margin": rho,
                "n": len(subset),
            })
            print(f"  {relation:24s}{cell:12s}rho(strength, margin) = {rho:+.3f}  n={len(subset)}")
    report["strength_mediation"] = a4

    # ---- files -------------------------------------------------------------
    write_json_atomic(args.out / "plausibility_summary.json", json_safe(report))
    if a1:
        with (args.out / "plausibility_cells.csv").open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(a1[0].keys()))
            writer.writeheader()
            writer.writerows(a1)

    lines = [f"# E10: plausibility of the false answer — {config['model']['id']}\n"]
    lines.append(
        "Entity held fixed; only how far the false answer sits from the true one "
        "varies. For `element_atomic_number` that distance is a number line "
        f"({', '.join(f'd={d}' for d in NUMERIC_DISTANCES)}, plus a random "
        "derangement); elsewhere it is `near` (the adjacent row's answer) versus "
        "`random`.\n"
    )
    lines.append("\n## Act effect at each distance (the decisive test)\n")
    lines.append("| Relation | Distance | Act effect (stipulate − assert) | 95% CI | n |")
    lines.append("|---|---|---:|---:|---:|")
    for entry in a2:
        low, high = entry["ci95"]
        lines.append(
            f"| {entry['relation']} | `{entry['distance']}` | {entry['delta']:.2f} | "
            f"[{low:+.2f}, {high:+.2f}] | {entry['n']} |"
        )
    lines.append("\n## Deference by distance (neutral policy)\n")
    lines.append("| Relation | Cell | Distance | n | Context | Mean margin | Mean strength |")
    lines.append("|---|---|---|---:|---:|---:|---:|")
    for entry in a1:
        strength_text = (
            f"{entry['mean_strength']:.2f}" if entry["mean_strength"] is not None else "--"
        )
        lines.append(
            f"| {entry['relation']} | `{entry['cell']}` | `{entry['distance']}` | "
            f"{entry['n']} | {100 * entry['context_rate']:.1f}% | "
            f"{entry['mean_margin']:.2f} | {strength_text} |"
        )
    if a3:
        lines.append("\n## Leakage under `ignore the paragraph`\n")
        lines.append("| Relation | Distance | Cell | Leak rate | n |")
        lines.append("|---|---|---|---:|---:|")
        for entry in a3:
            lines.append(
                f"| {entry['relation']} | `{entry['distance']}` | `{entry['cell']}` | "
                f"{100 * entry['leak_rate']:.1f}% | {entry['n']} |"
            )
    if a4:
        lines.append("\n## Strength as a mediator, entity fixed\n")
        lines.append("| Relation | Cell | rho(strength, margin) | n |")
        lines.append("|---|---|---:|---:|")
        for entry in a4:
            lines.append(
                f"| {entry['relation']} | `{entry['cell']}` | "
                f"{entry['rho_strength_margin']:+.3f} | {entry['n']} |"
            )
    lines.append("\n## How to read this\n")
    lines.append(
        "- **A2 is the one that matters.** E8's act effect on atomic numbers was "
        "−10.83, measured where every false answer was true+1. If the effect keeps "
        "that sign and size at `d20` and `random`, the falsification of the "
        "stipulability account stands and is now confound-free. If it collapses "
        "toward zero as distance grows, the falsification was an artefact of "
        "near-miss claims and section 5 has to be rewritten.\n"
        "- **A1 tells you how big the confound was.** Compare `near`/`d1` against "
        "`random` within `element_symbol` and `country_capital`: that gap is "
        "exactly the difference between the Gemma and Qwen E8 runs, which used "
        "different modes.\n"
        "- **A3** asks whether the bare > assert > explicit leakage gradient is a "
        "property of atomic numbers or of near-miss claims. It was only ever "
        "visible on atomic numbers, and atomic numbers were the only relation "
        "pinned at distance 1.\n"
        "- **A4** is E9's question asked properly. Strength and distance move "
        "together within one entity, so a strong negative rho means the model is "
        "tracking how confidently it holds the discrimination, not what kind of "
        "fact it is.\n"
        "- Margins are teacher-forced and unaffected by answer formatting; the "
        "rates classify the answer with any reasoning preamble stripped, as E8 "
        "does and E6/E7 do not.\n"
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwrote {args.out / 'plausibility_summary.json'}")
    print(f"wrote {report_path}")
    print(f"elapsed {time.time() - started:.1f}s")


if __name__ == "__main__":
    main()
