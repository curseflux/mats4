#!/usr/bin/env bash
#
# ---------------------------------------------------------------------------
# BEFORE YOU START
# ---------------------------------------------------------------------------
#
#   1. Edit `paths.hf_cache_dir` in config.yaml and config_qwen36.yaml.
#      Relative paths in those files resolve from the config file, not the
#      shell.
#
#   2. Install:
#        pip install torch
#        pip install "transformers==5.15.0" accelerate pyyaml numpy scipy \
#                    matplotlib
#
#   3. Everything here is behavioural -- greedy answers plus teacher-forced
#      candidate log-probabilities.

set -euo pipefail

G=results/gemma4_12b_conflict;
Q=results/qwen36_27b_conflict;
DATA=conflict_awareness_dataset;


# ===========================================================================
# 0. DATASET                                                    (~1 min, no GPU)
# ===========================================================================
# Deterministic in --seed. Both models must read the SAME dataset: reusing the
# identical prompts is what makes the two comparable. Do not regenerate it
# between the Gemma and Qwen runs.

python build_conflict_awareness_dataset.py \
  --output-dir $DATA \
  --seed 20260816 \
  --counterbalance-rounds 1

# Expect: 271 facts, 813 screening records, 9756 experiment records.


# ===========================================================================
# 1. SCREENING -- which facts does each model actually know?    (~15 min each)
# ===========================================================================
# --validate-only checks the dataset and returns before any model is loaded.

python 01_screen_knowledge.py --config config.yaml --validate-only
python 01_screen_knowledge.py --config config.yaml

python 01_screen_knowledge.py --config config_qwen36.yaml --validate-only
python 01_screen_knowledge.py --config config_qwen36.yaml

# Expect: Gemma 267/271 eligible, Qwen 271/271, and every surviving fact
# answered correctly on all three of its screening prompts (Gemma 801/801).


# ===========================================================================
# 2. BEHAVIOUR -- the factorial grid                     (~2 h Gemma, ~1 h Qwen)
# ===========================================================================

python 02_collect_model_data.py --config config.yaml --validate-only
python 02_collect_model_data.py --config config.yaml --behavior-only

python 02_collect_model_data.py --config config_qwen36.yaml --validate-only
python 02_collect_model_data.py --config config_qwen36.yaml --behavior-only

# Expect: 9468 Gemma rows, 9756 Qwen rows.
# CHECKPOINT -- the write-up's "greedy answer and margin agree" claim:
python - <<'PY'
import json
rows = [json.loads(l) for l in open("results/gemma4_12b_conflict/behavior_results.jsonl")]
rows = [r for r in rows if r.get("context_minus_parametric_logprob_margin") is not None
        and r["observed_knowledge_source"] in ("contextual", "parametric")]
agree = [(r["observed_knowledge_source"] == "contextual")
         == (r["context_minus_parametric_logprob_margin"] > 0) for r in rows]
gap = [abs(r["context_minus_parametric_logprob_margin"])
       for r, a in zip(rows, agree) if not a]
print(f"n={len(rows)}  agreement={100 * sum(agree) / len(agree):.2f}%")
if gap:
    print(f"disagreements occur within {max(gap):.2f} logits of a tie")
PY

# output:
# n=2308  agreement=99.18%
# disagreements occur within 1.23 logits of a tie


# ===========================================================================
# 3. E6 / E7 -- the paraphrase decomposition and the claim's properties
#                                                            (~1-2 h, ~2 h)
# ===========================================================================

python E6_template_decomposition.py --config config.yaml \
  --behavior   $G/behavior_results.jsonl \
  --experiment $DATA/experiment.jsonl \
  --out $G/analysis/decomposition --validate-only
python E6_template_decomposition.py --config config.yaml \
  --behavior   $G/behavior_results.jsonl \
  --experiment $DATA/experiment.jsonl \
  --out $G/analysis/decomposition --include-policy-endpoints

python E7_claim_phrasing.py --config config.yaml \
  --behavior   $G/behavior_results.jsonl \
  --e6-results $G/analysis/decomposition/decomposition_results.jsonl \
  --out $G/analysis/phrasing --validate-only
python E7_claim_phrasing.py --config config.yaml \
  --behavior   $G/behavior_results.jsonl \
  --e6-results $G/analysis/decomposition/decomposition_results.jsonl \
  --out $G/analysis/phrasing

# ===========================================================================
# 4. E8 -- stipulability                                      (~1 h per model)
# ===========================================================================

python E8_conventionality.py --config config.yaml \
  --out $G/analysis/conventionality_random \
  --false-answer-mode random --policies neutral,context,parametric --validate-only
python E8_conventionality.py --config config.yaml \
  --out $G/analysis/conventionality_random \
  --false-answer-mode random --policies neutral,context,parametric

python E8_conventionality.py --config config_qwen36.yaml \
  --out $Q/analysis/conventionality_random \
  --false-answer-mode random --policies neutral,context,parametric


# ===========================================================================
# 5. E9 -- the thread that went nowhere                       (~2 min, no GPU)
# ===========================================================================

python E9_knowledge_strength.py \
  --results gemma=$G/analysis/conventionality_random/conventionality_results.jsonl \
            qwen=$Q/analysis/conventionality_random/conventionality_results.jsonl \
  --out results/analysis_knowledge_strength


# ===========================================================================
# 6. E10 -- plausibility: is it the relation or the near miss?   (~2-3 h)
# ===========================================================================

python E10_answer_plausibility.py --config config.yaml \
  --out $G/analysis/plausibility --validate-only
python E10_answer_plausibility.py --config config.yaml \
  --out $G/analysis/plausibility_pilot --max-facts 12
python E10_answer_plausibility.py --config config.yaml \
  --out $G/analysis/plausibility

python E10_answer_plausibility.py --config config_qwen36.yaml \
  --out $Q/analysis/plausibility \
  --relations element_atomic_number,element_symbol


# ===========================================================================
# 7. E11 -- the channel, all eight at once            (~75 min Gemma, ~60 Qwen)
# ===========================================================================

python E11_source_channel.py --config config.yaml \
  --out $G/analysis/channel --validate-only
python E11_source_channel.py --config config.yaml \
  --out $G/analysis/channel
python E11_source_channel.py --config config_qwen36.yaml \
  --out $Q/analysis/channel


# ===========================================================================
# 8. E12 -- what the wrapper is, all fourteen at once      (~80 min per model)
# ===========================================================================

python E12_delimiter.py --config config.yaml \
  --out $G/analysis/delimiter --validate-only
python E12_delimiter.py --config config.yaml \
  --out $G/analysis/delimiter
python E12_delimiter.py --config config_qwen36.yaml \
  --out $Q/analysis/delimiter


python - <<'PY'
import json, statistics
G = "results/gemma4_12b_conflict/analysis"
def cell(path, keep):
    rows = [json.loads(l) for l in open(path)]
    m = [r["context_minus_parametric_logprob_margin"] for r in rows
         if r["relation_id"] == "element_symbol" and r["cell_id"] == "assert_r1" and keep(r)]
    return statistics.mean(m), len(m)
runs = {
    "E8 ": cell(f"{G}/conventionality_random/conventionality_results.jsonl",
                lambda r: r.get("policy_id") == "neutral"),
    "E11": cell(f"{G}/channel/channel_results.jsonl",
                lambda r: r.get("policy_id") == "neutral" and r["channel"] == "inline"),
    "E12": cell(f"{G}/delimiter/delimiter_results.jsonl",
                lambda r: r["wrapper"] == "inline"),
}
for name, (mean, n) in runs.items():
    print(f"  {name}  inline mean margin {mean:7.2f}  (n={n})")
means = [m for m, _ in runs.values()]
print(f"  spread across three runs: {max(means) - min(means):.2f} logits")
PY

# output:
#   E8   inline mean margin  -27.11  (n=118)
#   E11  inline mean margin  -27.00  (n=118)
#   E12  inline mean margin  -27.10  (n=118)
#   spread across three runs: 0.10 logits


# ===========================================================================
# 9. FIGURES AND EXAMPLES                                   (~10 s, no GPU)
# ===========================================================================

python make_figures.py --results results --out figures


echo
echo "Done. Diff the headline numbers against WRITEUP.md. Anything that moved by"
echo "more than rounding is worth understanding, not editing."
