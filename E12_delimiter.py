#!/usr/bin/env python3
"""E12: what exactly is the <document> wrapper doing?

E11's result
------------
Wrapping an otherwise identical paragraph in <document> tags takes Gemma from
0.0% to 100.0% context-following on a plain false assertion -- `assert_r1`,
neutral policy, both relations -- a swing of about 41 logits:

    element_symbol   inline -27.00  ->  delimited +13.86
    country_capital  inline -28.08  ->  delimited +12.65

That is larger than the paraphrase swing (30.9) and larger than the explicit
instruction "use the paragraph" (28.5), from a manipulation that changes no
words at all.  A system prompt saying the tags contain data and not
instructions changes nothing (100.0%).

Before that can be reported, three cheaper explanations have to go
--------------------------------------------------------------------
1. LAYOUT.  `delimited` also adds two newlines around the paragraph. Maybe any
   visual separation of source material from question does this, and the tags
   are irrelevant.
2. SYNTAX vs WORD.  Maybe it is angle-bracket markup of any kind, or maybe it
   is specifically the word "document" and its connotation of a citable source.
3. VALENCE.  If the model is reading the wrapper as "this is a source", does a
   wrapper that says the opposite reverse it?  `<untrusted_content>` is the
   test that matters for anyone building a RAG system: the tag whose whole
   purpose is to mark text as not-to-be-trusted.

The wrappers
------------
    inline            no wrapper at all (reproduces E11's baseline)
    blankline         extra blank lines, no markup      -> tests LAYOUT
    dashes            --- fences                        -> tests LAYOUT + fence
    quotes            triple-quote fences               -> tests LAYOUT + fence
    tag_document      <document>                        -> E11's condition
    tag_passage       <passage>                         -> tests the WORD
    tag_empty         <>                                -> tests the SYNTAX
    tag_untrusted     <untrusted_content>               -> tests VALENCE
    tag_unreliable    <unreliable_source>               -> tests VALENCE
    tag_trusted       <trusted_content>                 -> tests VALENCE
    tag_nonsense      <qzx_block>                       -> tests the SYNTAX + no meaning
    label_document    "Document:" on its own line       -> markup-free label
    label_search      "Search result:" on its own line  -> the RAG framing

Cells: `assert_r1` (a sourced false assertion, the cell that swung) and `bare`
(the same falsehood with no source at all).  If `bare` swings too, the wrapper
is not conferring source authority -- it is changing what task the model thinks
it is doing.  Neutral policy only: under `parametric` every channel in E11 sat
at 0.0%, so there is nothing there to move.

Usage
-----
python E12_delimiter.py --config config.yaml \\
    --out results/gemma4_12b_conflict/analysis/delimiter --validate-only

python E12_delimiter.py --config config.yaml \\
    --out results/gemma4_12b_conflict/analysis/delimiter
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

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
    render_messages,
    runtime_fingerprint,
    score_continuations,
    seed_everything,
    write_json_atomic,
)

from E8_conventionality import (
    CONSTRAINT,
    FILLER,
    PREDICATES,
    QUESTION,
    SOURCE,
    BARE,
    build_facts,
)

ANALYSIS_VERSION = "1.0.0"

CELLS = ("assert_r1", "bare")

# Each wrapper takes the paragraph and returns the block that replaces it.
# `inline` is the identity, and reproduces E11's baseline exactly.
WRAPPERS: dict[str, str] = {
    "inline": "{p}",
    "blankline": "\n{p}\n",
    "dashes": "---\n{p}\n---",
    "quotes": '"""\n{p}\n"""',
    "tag_document": "<document>\n{p}\n</document>",
    "tag_passage": "<passage>\n{p}\n</passage>",
    "tag_empty": "<>\n{p}\n</>",
    "tag_untrusted": "<untrusted_content>\n{p}\n</untrusted_content>",
    "tag_unreliable": "<unreliable_source>\n{p}\n</unreliable_source>",
    "tag_trusted": "<trusted_content>\n{p}\n</trusted_content>",
    "tag_nonsense": "<qzx_block>\n{p}\n</qzx_block>",
    "label_document": "Document:\n{p}",
    "label_search": "Search result:\n{p}",
}
# What each wrapper is there to rule out, carried into the report so the table
# cannot be read without the reason for each row.
WRAPPER_ROLE = {
    "inline": "baseline",
    "blankline": "layout only",
    "dashes": "layout + fence",
    "quotes": "layout + fence",
    "tag_document": "E11's condition",
    "tag_passage": "same syntax, different word",
    "tag_empty": "bracket syntax, no name at all",
    "tag_untrusted": "same syntax, opposite valence",
    "tag_unreliable": "opposite valence, different words",
    "tag_trusted": "same syntax, positive valence",
    "tag_nonsense": "same syntax, no meaning at all",
    "label_document": "same word, no markup",
    "label_search": "the RAG framing",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--relations", default="element_symbol,country_capital")
    parser.add_argument("--wrappers", default=",".join(WRAPPERS))
    parser.add_argument("--cells", default=",".join(CELLS))
    parser.add_argument(
        "--false-answer-mode", choices=("reuse", "rotation", "random"), default="random"
    )
    parser.add_argument("--false-answer-seed", type=int, default=20260816)
    parser.add_argument("--max-facts", type=int, default=None)
    parser.add_argument("--generation-batch-size", type=int, default=None)
    parser.add_argument("--scoring-batch-size", type=int, default=None)
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    parser.add_argument("--skip-screening", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--analyze-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def claim_sentence(relation: str, cell: str, subject: str, answer: str) -> str:
    if cell == "bare":
        return BARE[relation].format(s=subject, a=answer)
    act, realization = cell.rsplit("_", 1)
    return f"{SOURCE[relation]} {PREDICATES[relation][act][realization]}.".format(
        s=subject, a=answer
    )


def build_prompt(relation: str, wrapper: str, claim: str, subject: str) -> str:
    """Only the wrapper changes. The paragraph, question and constraint do not."""
    paragraph = f"{claim} {FILLER[relation]}"
    block = WRAPPERS[wrapper].format(p=paragraph)
    question = QUESTION[relation].format(s=subject)
    return f"{block}\n\n{question}\n{CONSTRAINT[relation]}"


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


def build_records(
    facts: Sequence[Mapping[str, Any]],
    wrappers: Sequence[str],
    cells: Sequence[str],
) -> list[dict[str, Any]]:
    records = []
    for fact in facts:
        relation = str(fact["relation_id"])
        subject, answer = str(fact["query_subject"]), str(fact["claim_answer"])
        for cell in cells:
            claim = claim_sentence(relation, cell, subject, answer)
            for wrapper in wrappers:
                prompt = build_prompt(relation, wrapper, claim, subject)
                records.append(
                    {
                        "sample_id": f"e12-{fact['fact_id']}-{cell}-{wrapper}",
                        "messages": [{"role": "user", "content": prompt}],
                        "fact_id": fact["fact_id"],
                        "relation_id": relation,
                        "cell_id": cell,
                        "wrapper": wrapper,
                        "claim_sentence": claim,
                        "raw_prompt": prompt,
                        "context_candidate_answer": answer,
                        "acceptable_world_true_answers": list(
                            fact["acceptable_world_true_answers"]
                        ),
                        "parametric_candidate_answer": fact["world_true_answer"],
                    }
                )
    return records


def screening_records(facts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for fact in facts:
        relation = str(fact["relation_id"])
        prompt = (
            f"{QUESTION[relation].format(s=fact['query_subject'])}\n{CONSTRAINT[relation]}"
        )
        records.append(
            {
                "sample_id": f"e12screen-{fact['fact_id']}",
                "messages": [{"role": "user", "content": prompt}],
                "fact_id": fact["fact_id"],
                "relation_id": relation,
                "cell_id": "screen",
                "wrapper": "inline",
                "claim_sentence": "",
                "raw_prompt": prompt,
                "context_candidate_answer": fact["claim_answer"],
                "acceptable_world_true_answers": list(fact["acceptable_world_true_answers"]),
                "parametric_candidate_answer": fact["world_true_answer"],
            }
        )
    return records


def evaluate(
    records: Sequence[Mapping[str, Any]],
    bundle: Any,
    config: Mapping[str, Any],
    partial_path: Path,
    generation_batch: int,
    scoring_batch: int,
    started: float,
) -> None:
    max_input = int(config["chat"]["max_input_tokens"])
    for start in range(0, len(records), generation_batch):
        chunk = records[start : start + generation_batch]
        rendered = [render_messages(bundle.processor, r["messages"], config) for r in chunk]
        generations = generate_batch(bundle.model, bundle.tokenizer, rendered, config)

        requests: list[dict[str, str]] = []
        for index, record in enumerate(chunk):
            requests.append(
                {
                    "key": f"{index}|context",
                    "rendered_text": rendered[index],
                    "continuation": str(record["context_candidate_answer"]),
                }
            )
            for alias, answer in enumerate(record["acceptable_world_true_answers"]):
                requests.append(
                    {
                        "key": f"{index}|parametric|{alias}",
                        "rendered_text": rendered[index],
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
            answer = str(generation.get("answer_text") or generation["text"])
            output.append(
                {
                    "code_version": CODE_VERSION,
                    "analysis_version": ANALYSIS_VERSION,
                    **{
                        k: record[k]
                        for k in (
                            "sample_id", "fact_id", "relation_id", "cell_id",
                            "wrapper", "claim_sentence", "raw_prompt",
                        )
                    },
                    "generated_answer": generation["text"],
                    "generated_answer_stripped": answer,
                    "format_compliant": is_one_orthographic_word(generation["text"]),
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
            print(f"  {start + len(chunk)}/{len(records)} ({time.time() - started:7.1f}s)")


def main() -> None:
    import numpy as np

    started = time.time()
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    results_path = args.out / "delimiter_results.jsonl"
    partial_path = args.out / "delimiter_results.jsonl.partial"
    report_path = args.out / "delimiter_report.md"
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
    wrappers = [w.strip() for w in args.wrappers.split(",") if w.strip()]
    cells = [c.strip() for c in args.cells.split(",") if c.strip()]
    for wrapper in wrappers:
        if wrapper not in WRAPPERS:
            raise ValueError(f"Unknown wrapper {wrapper!r}; expected {sorted(WRAPPERS)}")
    if "inline" not in wrappers:
        raise ValueError("`inline` is the baseline that reproduces E11; keep it in")

    facts = build_facts(
        relations, None, args.max_facts,
        mode=args.false_answer_mode, seed=args.false_answer_seed,
    )
    print(f"model: {config['model']['id']}")
    print(f"facts before screening: {len(facts)}   mode {args.false_answer_mode}")

    if args.validate_only:
        example = facts[0]
        for wrapper in wrappers:
            print(f"\n{'=' * 78}\n{wrapper}  ({WRAPPER_ROLE.get(wrapper, '')})\n{'=' * 78}")
            print(
                build_prompt(
                    str(example["relation_id"]), wrapper,
                    claim_sentence(
                        str(example["relation_id"]), "assert_r1",
                        str(example["query_subject"]), str(example["claim_answer"]),
                    ),
                    str(example["query_subject"]),
                )
            )
        print(
            f"\nvalidate-only: {len(facts)} screening + "
            f"{len(build_records(facts, wrappers, cells))} experimental prompts"
        )
        return

    if args.analyze_only:
        if not results_path.is_file():
            raise FileNotFoundError(f"--analyze-only needs an existing {results_path}")
        rows = read_jsonl(results_path)
        fingerprint: Any = {"note": "analyze-only; the model was not loaded"}
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

        if not args.skip_screening:
            print("\nscreening (context-free)")
            screen = [r for r in screening_records(facts) if r["sample_id"] not in done]
            evaluate(screen, bundle, config, partial_path, generation_batch,
                     scoring_batch, started)
            scored = {
                str(r["sample_id"]): r
                for r in read_jsonl(partial_path)
                if str(r["cell_id"]) == "screen"
            }
            kept = [
                fact for fact in facts
                if (row := scored.get(f"e12screen-{fact['fact_id']}")) is not None
                and row["observed_knowledge_source"] == "parametric"
                and float(row["context_minus_parametric_logprob_margin"]) < 0
            ]
            print(f"  kept {len(kept)}/{len(facts)} facts")
            facts = kept
            if not facts:
                raise RuntimeError("No facts survived screening")

        experiment = [
            r for r in build_records(facts, wrappers, cells)
            if r["sample_id"] not in done
        ]
        print(f"\nscoring {len(experiment)} experimental prompts")
        evaluate(experiment, bundle, config, partial_path, generation_batch,
                 scoring_batch, started)
        rows = read_jsonl(partial_path)
        finalize_jsonl(partial_path, results_path)
        print(f"\nscored {len(rows)} prompts total")

    # ---- analysis ----------------------------------------------------------
    seed = int(config["project"]["seed"])
    live = [r for r in rows if r["cell_id"] != "screen"]
    margins = {
        (str(r["fact_id"]), str(r["cell_id"]), str(r["wrapper"])): float(
            r["context_minus_parametric_logprob_margin"]
        )
        for r in live
    }

    summary, contrasts = [], []
    print("\n" + "=" * 78)
    print("wrapper effect, paired within fact against `inline`")
    print("=" * 78)
    for relation in relations:
        print(f"\n{relation}")
        print(f"  {'wrapper':18s}{'role':28s}{'cell':12s}"
              f"{'context':>10s}{'margin':>9s}{'vs inline':>11s}{'95% CI':>20s}")
        fact_ids = sorted({str(r["fact_id"]) for r in live if r["relation_id"] == relation})
        for wrapper in wrappers:
            for cell in cells:
                group = [
                    r for r in live
                    if r["relation_id"] == relation
                    and r["wrapper"] == wrapper and r["cell_id"] == cell
                ]
                if not group:
                    continue
                rate = float(np.mean(
                    [r["observed_knowledge_source"] == "contextual" for r in group]
                ))
                margin = float(np.mean(
                    [r["context_minus_parametric_logprob_margin"] for r in group]
                ))
                deltas, usable = [], []
                for fact in fact_ids:
                    here = margins.get((fact, cell, wrapper))
                    base = margins.get((fact, cell, "inline"))
                    if here is None or base is None:
                        continue
                    usable.append(fact)
                    deltas.append(here - base)
                if usable:
                    array = np.asarray(deltas)
                    low, high = cluster_bootstrap(
                        usable, lambda picked: float(np.mean(array[picked])),
                        args.bootstrap_replicates, seed,
                    )
                    delta = float(array.mean())
                else:
                    delta, low, high = float("nan"), float("nan"), float("nan")
                print(
                    f"  {wrapper:18s}{WRAPPER_ROLE.get(wrapper, ''):28s}{cell:12s}"
                    f"{100 * rate:>9.1f}%{margin:>9.2f}{delta:>11.2f}"
                    f"{f'[{low:+.1f}, {high:+.1f}]':>20}"
                )
                summary.append({
                    "relation": relation, "wrapper": wrapper, "cell": cell,
                    "role": WRAPPER_ROLE.get(wrapper, ""), "n": len(group),
                    "context_rate": rate, "mean_margin": margin,
                })
                contrasts.append({
                    "relation": relation, "wrapper": wrapper, "cell": cell,
                    "delta_vs_inline": delta, "ci95": [low, high], "n": len(usable),
                })

    report = {
        "analysis_version": ANALYSIS_VERSION,
        "runtime": fingerprint,
        "model": config["model"]["id"],
        "false_answer_mode": args.false_answer_mode,
        "false_answer_seed": args.false_answer_seed,
        "wrappers": {w: WRAPPERS[w] for w in wrappers},
        "wrapper_roles": WRAPPER_ROLE,
        "cells": summary,
        "contrasts_vs_inline": contrasts,
    }
    write_json_atomic(args.out / "delimiter_summary.json", json_safe(report))
    if summary:
        with (args.out / "delimiter_cells.csv").open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(summary[0].keys()))
            writer.writeheader()
            writer.writerows(summary)

    lines = [f"# E12: what the wrapper is doing — {config['model']['id']}\n"]
    lines.append(
        "The paragraph, claim sentence, question and response constraint are "
        "byte-identical in every row. Only the block that encloses the paragraph "
        "changes. `delta vs inline` is paired within fact and "
        "cluster-bootstrapped over facts.\n"
    )
    lines.append(
        "\n| Relation | Wrapper | What it rules out | Cell | n | Context | Margin | Δ vs inline | 95% CI |"
    )
    lines.append("|---|---|---|---|---:|---:|---:|---:|---:|")
    by_key = {(c["relation"], c["wrapper"], c["cell"]): c for c in contrasts}
    for entry in summary:
        contrast = by_key[(entry["relation"], entry["wrapper"], entry["cell"])]
        low, high = contrast["ci95"]
        lines.append(
            f"| {entry['relation']} | `{entry['wrapper']}` | {entry['role']} | "
            f"`{entry['cell']}` | {entry['n']} | {100 * entry['context_rate']:.1f}% | "
            f"{entry['mean_margin']:.2f} | {contrast['delta_vs_inline']:+.2f} | "
            f"[{low:+.2f}, {high:+.2f}] |"
        )
    lines.append("\n## How to read this\n")
    lines.append(
        "- **`blankline` is the layout control.** If it moves the margin as much "
        "as `tag_document`, E11's effect was whitespace and the document framing "
        "is a red herring. If it does not, the markup is doing real work.\n"
        "- **`tag_passage` versus `tag_document`** separates the syntax from the "
        "word. **`label_document`** separates the word from the syntax.\n"
        "- **`tag_untrusted` is the one to report.** It is the tag whose entire "
        "purpose is to mark text as not-to-be-trusted. If deference under it "
        "matches `tag_document`, the wrapper is read as *this is source "
        "material* and its stated valence is ignored. If it does NOT -- if the "
        "tag suppresses deference -- then the model is reading the label's "
        "meaning, and the question becomes why the same words fail when they "
        "are put in the system prompt instead.\n"
        "- **`tag_nonsense` is the control for that reading.** `<qzx_block>` "
        "carries the same syntax and no meaning. If it behaves like "
        "`<document>`, an unfamiliar tag is not inherently suppressive and a "
        "low score for `<untrusted_content>` really is about the word. If it "
        "behaves like `<untrusted_content>`, then any out-of-distribution tag "
        "suppresses deference and the semantic reading is wrong. "
        "`tag_trusted` and `tag_unreliable` place the same contrast on a scale.\n"
        "- **`tag_empty` splits the structure term itself.** `<qzx_block>` still "
        "has a name; `<>` has only the brackets. If `<>` matches `<qzx_block>`, "
        "the name contributes nothing and the structural effect is the bracket "
        "syntax. If `<>` falls back toward `dashes`, then a tag needs to NAME "
        "something -- anything -- and `<qzx_block>`'s +31 was already partly "
        "semantic.\n"
        "- **`bare` versus `assert_r1`** asks whether the wrapper confers source "
        "authority or changes the task. `bare` has no source to trust, so if it "
        "swings too, the model is switching into reading-comprehension mode "
        "rather than deciding whom to believe.\n"
        "- Margins are teacher-forced. Rates classify the answer with any "
        "reasoning preamble stripped.\n"
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwrote {report_path}")
    print(f"elapsed {time.time() - started:.1f}s")


if __name__ == "__main__":
    main()
