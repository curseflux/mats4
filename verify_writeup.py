#!/usr/bin/env python3
"""Re-derive every number quoted in WRITEUP.md from the raw result JSONL.

Nothing here reads a report or a summary file. Each claim is recomputed from
`*_results.jsonl` with its own arithmetic, so a bug in an analysis script cannot
launder itself into the write-up: if the report and this script agree, two
independent paths produced the number.

Every contrast is paired within fact, because each fact appears in every cell
and the rows of a fact are not independent.

    python verify_writeup.py

Exits non-zero if any claim fails. No GPU, no model, ~2 seconds.
"""

from __future__ import annotations

import collections
import json
import statistics
import sys

G = "results/gemma4_12b_conflict"
Q = "results/qwen36_27b_conflict"

FAILURES: list[str] = []


def load(path: str) -> list[dict]:
    return [json.loads(line) for line in open(path)]


def check(label: str, got: float, want: float, tol: float = 0.005) -> None:
    ok = abs(got - want) <= tol
    print(f"{'PASS' if ok else 'FAIL'}  {label:52s} got {got:10.4f}  writeup says {want:10.4f}")
    if not ok:
        FAILURES.append(label)


def select(rows, relation, cell, policy=None, **equals):
    out = []
    for row in rows:
        if row.get("relation_id") != relation or row.get("cell_id") != cell:
            continue
        if policy is not None and row.get("policy_id") != policy:
            continue
        if any(row.get(k) != v for k, v in equals.items()):
            continue
        out.append(row)
    return out


def paired_delta(rows, key, baseline, relation, cell, policy=None):
    """Mean within-fact difference in margin, every level against `baseline`."""
    by_fact = collections.defaultdict(dict)
    for row in select(rows, relation, cell, policy):
        by_fact[row["fact_id"]][row[key]] = row
    deltas = collections.defaultdict(list)
    for levels in by_fact.values():
        if baseline not in levels:
            continue
        base = levels[baseline]["context_minus_parametric_logprob_margin"]
        for level, row in levels.items():
            deltas[level].append(row["context_minus_parametric_logprob_margin"] - base)
    return {level: statistics.mean(v) for level, v in deltas.items()}


def rate(rows, key, value, relation, cell, policy=None):
    chosen = select(rows, relation, cell, policy, **{key: value})
    hits = sum(1 for r in chosen if r["observed_knowledge_source"] == "contextual")
    return 100 * hits / len(chosen)


def margin(rows, key, value, relation, cell, policy=None):
    chosen = select(rows, relation, cell, policy, **{key: value})
    return statistics.mean(r["context_minus_parametric_logprob_margin"] for r in chosen)


def main() -> int:
    delim_g = load(f"{G}/analysis/delimiter/delimiter_results.jsonl")
    delim_q = load(f"{Q}/analysis/delimiter/delimiter_results.jsonl")
    chan_g = load(f"{G}/analysis/channel/channel_results.jsonl")
    chan_q = load(f"{Q}/analysis/channel/channel_results.jsonl")
    conv_g = load(f"{G}/analysis/conventionality_random/conventionality_results.jsonl")
    phrasing = load(f"{G}/analysis/phrasing/phrasing_results.jsonl")

    print("\n== 3 - the wrapper ladder, Gemma elements, paired against no wrapper ==")
    ladder = paired_delta(delim_g, "wrapper", "inline", "element_symbol", "assert_r1")
    for wrapper, expected, expected_rate in [
        ("blankline", 1.26, 0.0), ("tag_untrusted", 2.76, 0.0), ("quotes", 8.57, 5.9),
        ("tag_empty", 14.57, 25.4), ("dashes", 17.80, 23.7), ("tag_unreliable", 21.10, 28.8),
        ("tag_nonsense", 31.19, 78.8), ("label_document", 38.54, 98.3),
        ("label_search", 40.07, 100.0), ("tag_passage", 40.27, 100.0),
        ("tag_document", 40.98, 100.0), ("tag_trusted", 43.44, 100.0),
    ]:
        check(f"{wrapper} margin", ladder[wrapper], expected)
        check(f"{wrapper} rate", rate(delim_g, "wrapper", wrapper, "element_symbol", "assert_r1"),
              expected_rate, 0.06)

    print("\n== 3 - what the NAME buys, paired against <qzx_block> ==")
    for relation, expected in [
        ("element_symbol", {"tag_trusted": 12.25, "tag_document": 9.79,
                            "tag_unreliable": -10.09, "tag_untrusted": -28.43}),
        ("country_capital", {"tag_trusted": 14.12, "tag_document": 9.73,
                             "tag_unreliable": -24.62, "tag_untrusted": -30.22}),
    ]:
        got = paired_delta(delim_g, "wrapper", "tag_nonsense", relation, "assert_r1")
        for wrapper, value in expected.items():
            check(f"{relation[:4]} {wrapper} vs qzx", got[wrapper], value)

    print("\n== 3 - capitals, and the sourceless `bare` claim ==")
    caps = paired_delta(delim_g, "wrapper", "inline", "country_capital", "assert_r1")
    check("capitals quotes", caps["quotes"], 26.41)
    check("capitals unreliable", caps["tag_unreliable"], 6.32)
    check("capitals <> vs qzx gap", caps["tag_nonsense"] - caps["tag_empty"], 2.13, 0.01)
    check("elements <> vs qzx gap", ladder["tag_nonsense"] - ladder["tag_empty"], 16.63, 0.01)
    for relation, wrapper, expected in [
        ("element_symbol", "inline", 9.3), ("country_capital", "inline", 23.1),
        ("element_symbol", "tag_document", 98.3), ("country_capital", "tag_document", 100.0),
    ]:
        check(f"bare {relation[:4]} {wrapper}",
              rate(delim_g, "wrapper", wrapper, relation, "bare"), expected, 0.06)

    print("\n== 2 and 5 - the tag effect, and where the guards land ==")
    for rows, name, relation, expected in [
        (chan_g, "gemma", "element_symbol", 40.86), (chan_g, "gemma", "country_capital", 40.73),
        (chan_q, "qwen", "element_symbol", 7.79), (chan_q, "qwen", "country_capital", 11.09),
    ]:
        got = paired_delta(rows, "channel", "inline", relation, "assert_r1", "neutral")
        check(f"{name} {relation[:4]} tag effect", got["delimited"], expected)

    print("\n== 4 - four ways to say 'do not trust this block' ==")
    for rows, name, relation, expected in [
        (chan_g, "gemma", "element_symbol", {"system_guard": -0.21, "user_guard": -3.06,
                                             "user_guard_first_person": 5.49}),
        (chan_g, "gemma", "country_capital", {"system_guard": 1.27, "user_guard": 4.69,
                                              "user_guard_first_person": 11.47}),
        (chan_q, "qwen", "element_symbol", {"system_guard": -0.09, "user_guard": -1.53,
                                            "user_guard_first_person": 1.52}),
        (chan_q, "qwen", "country_capital", {"system_guard": -3.33, "user_guard": -3.15,
                                             "user_guard_first_person": -0.77}),
    ]:
        got = paired_delta(rows, "channel", "delimited", relation, "assert_r1", "neutral")
        for channel, value in expected.items():
            check(f"{name} {relation[:4]} {channel}", got[channel], value)
    for rows, name, relation, expected in [
        (delim_g, "gemma", "element_symbol", -38.22), (delim_g, "gemma", "country_capital", -39.94),
        (delim_q, "qwen", "element_symbol", -8.50), (delim_q, "qwen", "country_capital", -13.02),
    ]:
        got = paired_delta(rows, "wrapper", "tag_document", relation, "assert_r1")
        check(f"{name} {relation[:4]} <untrusted_content>", got["tag_untrusted"], expected)

    # The one cell where the two channels genuinely differ, called out in section 4.
    by_fact = collections.defaultdict(dict)
    for row in select(chan_q, "element_symbol", "assert_r1", "neutral"):
        by_fact[row["fact_id"]][row["channel"]] = row
    diff = [f["user_guard"]["context_minus_parametric_logprob_margin"]
            - f["system_guard"]["context_minus_parametric_logprob_margin"]
            for f in by_fact.values()]
    check("qwen elem user_guard - system_guard", statistics.mean(diff), -1.44, 0.01)

    print("\n== 2 - the channel table, and the imperative for scale ==")
    for channel, relation, expected_rate, expected_margin in [
        ("inline", "element_symbol", 0.0, -27.00), ("delimited", "element_symbol", 100.0, 13.86),
        ("inline", "country_capital", 0.0, -28.08), ("delimited", "country_capital", 100.0, 12.65),
        ("retrieved_turn", "element_symbol", 57.6, None),
        ("retrieved_turn", "country_capital", 93.7, None),
    ]:
        check(f"gemma {channel} {relation[:4]} rate",
              rate(chan_g, "channel", channel, relation, "assert_r1", "neutral"), expected_rate, 0.06)
        if expected_margin is not None:
            check(f"gemma {channel} {relation[:4]} margin",
                  margin(chan_g, "channel", channel, relation, "assert_r1", "neutral"),
                  expected_margin, 0.006)
    imperative = (margin(chan_g, "channel", "inline", "element_symbol", "explicit_stipulation", "neutral")
                  - margin(chan_g, "channel", "inline", "element_symbol", "assert_r1", "neutral"))
    check("in-sentence imperative is worth", imperative, 45.13, 0.01)

    print("\n== 5 - Qwen ==")
    for channel, relation, expected_rate, expected_margin in [
        ("inline", "element_symbol", 0.0, -7.24), ("delimited", "element_symbol", 62.7, 0.56),
        ("inline", "country_capital", 0.0, -11.07), ("delimited", "country_capital", 41.1, 0.02),
        ("system_guard", "element_symbol", 58.5, None), ("system_guard", "country_capital", 8.9, None),
        ("retrieved_turn", "element_symbol", 15.3, None), ("retrieved_turn", "country_capital", 2.7, None),
    ]:
        check(f"qwen {channel} {relation[:4]} rate",
              rate(chan_q, "channel", channel, relation, "assert_r1", "neutral"), expected_rate, 0.06)
        if expected_margin is not None:
            check(f"qwen {channel} {relation[:4]} margin",
                  margin(chan_q, "channel", channel, relation, "assert_r1", "neutral"),
                  expected_margin, 0.006)
    qwen_ladder = paired_delta(delim_q, "wrapper", "inline", "element_symbol", "assert_r1")
    for wrapper, expected in [("tag_document", 7.75), ("tag_passage", 7.47), ("tag_trusted", 4.21),
                              ("tag_nonsense", 4.70), ("label_document", 5.13), ("tag_empty", 2.15)]:
        check(f"qwen elem {wrapper}", qwen_ladder[wrapper], expected)
    qwen_caps = paired_delta(delim_q, "wrapper", "inline", "country_capital", "assert_r1")
    check("qwen caps <>", qwen_caps["tag_empty"], 3.96)
    check("qwen caps <qzx_block>", qwen_caps["tag_nonsense"], 3.97)

    print("\n== 6 - the speech act, and the control that kills it ==")
    check("atomic assert cell mean", margin(conv_g, "policy_id", "neutral",
                                            "element_atomic_number", "assert_r1"), -0.82, 0.006)
    check("atomic adopt cell mean", margin(conv_g, "policy_id", "neutral",
                                           "element_atomic_number", "stipulate_r1"), -7.05, 0.006)
    counts = collections.Counter(r["observed_knowledge_source"] for r in phrasing)
    check("E7 neither-candidate rate",
          100 * (counts["other"] + counts["unparseable"]) / len(phrasing), 10.9, 0.05)

    print("\n== 7 - the knowledge-strength dead end ==")
    leak = collections.defaultdict(lambda: [0, 0])
    for row in conv_g:
        if row.get("policy_id") != "parametric":
            continue
        bucket = leak[(row["relation_id"], row["cell_id"])]
        bucket[1] += 1
        bucket[0] += row["observed_knowledge_source"] == "contextual"
    for cell, expected in [("bare", 20.7), ("assert_r1", 6.0), ("explicit_stipulation", 0.0)]:
        hits, total = leak[("element_atomic_number", cell)]
        check(f"atomic leaks under 'ignore it', {cell}", 100 * hits / total, expected, 0.06)
    for relation in ("element_symbol", "country_capital"):
        for cell in ("bare", "assert_r1"):
            hits, total = leak[(relation, cell)]
            check(f"{relation[:4]} leaks under 'ignore it', {cell}", 100 * hits / total, 0.0, 0.06)

    print("\n== 1 and 8 - the sanity checks the write-up leans on ==")
    behaviour = load(f"{G}/behavior_results.jsonl")
    scored = [r for r in behaviour
              if r.get("context_minus_parametric_logprob_margin") is not None
              and r["observed_knowledge_source"] in ("contextual", "parametric")]
    agree = [(r["observed_knowledge_source"] == "contextual")
             == (r["context_minus_parametric_logprob_margin"] > 0) for r in scored]
    check("rows where greedy and margin are comparable", len(scored), 2308, 0)
    check("they agree", 100 * sum(agree) / len(agree), 99.18)
    check("worst disagreement is this close to a tie",
          max(abs(r["context_minus_parametric_logprob_margin"])
              for r, ok in zip(scored, agree) if not ok), 1.23)

    screening = load(f"{G}/screening_results.jsonl")
    eligible = {r["fact_id"] for r in load(f"{G}/eligible_facts.jsonl") if r["eligible"]}
    check("facts surviving screening", len(eligible), 267, 0)
    check("screening prompts they get right",
          sum(1 for r in screening if r["fact_id"] in eligible and r["generated_answer_is_correct"]),
          801, 0)
    check("and that is out of", sum(1 for r in screening if r["fact_id"] in eligible), 801, 0)

    for rows, name, expected in [(delim_g, "gemma", 2.9), (delim_q, "qwen", 0.15)]:
        real = [r for r in rows if r["cell_id"] != "screen"]
        counts = collections.Counter(r["observed_knowledge_source"] for r in real)
        check(f"{name} generations that are neither candidate",
              100 * (counts["other"] + counts["unparseable"]) / len(real), expected, 0.05)

    by_fact = collections.defaultdict(dict)
    for row in delim_g:
        if row["cell_id"] == "assert_r1":
            by_fact[(row["relation_id"], row["fact_id"])][row["wrapper"]] = row
    for wrapper, expected in [("tag_document", 261), ("tag_nonsense", 200)]:
        flips = sum(1 for levels in by_fact.values()
                    if levels["inline"]["observed_knowledge_source"] != "contextual"
                    and levels[wrapper]["observed_knowledge_source"] == "contextual")
        check(f"facts {wrapper} flips, of 261", flips, expected, 0)
    for relation, n in [("element_symbol", 118), ("country_capital", 143)]:
        moved = sum(1 for key, levels in by_fact.items() if key[0] == relation
                    and levels["tag_document"]["context_minus_parametric_logprob_margin"]
                    > levels["inline"]["context_minus_parametric_logprob_margin"])
        check(f"<document> moves {relation[:4]} margins up, of {n}", moved, n, 0)

    print("\n== the noise floor: one byte-identical cell, three GPU sessions ==")
    runs = {
        "E8 ": margin(conv_g, "policy_id", "neutral", "element_symbol", "assert_r1"),
        "E11": margin(chan_g, "channel", "inline", "element_symbol", "assert_r1", "neutral"),
        "E12": margin(delim_g, "wrapper", "inline", "element_symbol", "assert_r1"),
    }
    for name, expected in [("E8 ", -27.11), ("E11", -27.00), ("E12", -27.08)]:
        check(f"{name} unwrapped baseline", runs[name], expected, 0.006)
    check("spread across the three", max(runs.values()) - min(runs.values()), 0.10)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} CLAIM(S) IN WRITEUP.md NO LONGER MATCH THE DATA:")
        for name in FAILURES:
            print(f"  - {name}")
        return 1
    print("Every number in WRITEUP.md re-derived from raw results. All match.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
