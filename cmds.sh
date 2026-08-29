#!/usr/bin/env bash
#
# Full pipeline, start to finish, on an empty results tree.
#
# Run it with `bash cmds.sh` to execute everything, or paste blocks by hand --
# `set -e` means a failure stops the run rather than letting later steps build
# on a broken artefact.
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
#      candidate log-probabilities. No activations are written, so the only
#      disk cost is ~2 GiB of results. Wall clock on one A100-80G is roughly
#      6-8 h, nearly all of it in steps 2 and 5-8.
#
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
# A fact passes only if the model generates the true answer with no paragraph
# present AND prefers it to every false answer it will later be shown, in all
# three paraphrase bundles. Screening is per model; facts Gemma knows are not
# necessarily facts Qwen knows.
#
# --validate-only checks the dataset and returns before any model is loaded.

python 01_screen_knowledge.py --config config.yaml --validate-only
python 01_screen_knowledge.py --config config.yaml

python 01_screen_knowledge.py --config config_qwen36.yaml --validate-only
python 01_screen_knowledge.py --config config_qwen36.yaml

# Expect: Gemma 267/271 eligible, Qwen 271/271, and every surviving fact
# answered correctly on all three of its screening prompts (Gemma 801/801).
# A large drop means something is wrong with the chat template, not with the
# model's knowledge.


# ===========================================================================
# 2. BEHAVIOUR -- the factorial grid                     (~2 h Gemma, ~1 h Qwen)
# ===========================================================================
# Claim truth x query relevance x answer-source instruction, in three paraphrase
# bundles. This is the base grid the later experiments are anchored against.
# Resumable.

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
# E6 asks which of claim / filler / question / constraint carries the swing
# between paraphrase bundles. E7 then asks which PROPERTY of the claim sentence
# matters -- speech act, source authority, persistence, or lexicon -- holding
# everything else at E6's frame. E7 needs E6's results, so the order matters.
#
# Both classify the answer with any reasoning preamble stripped; margins are
# teacher-forced and unaffected either way.

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

# Expect (Gemma): act (stipulate - assert) +9.40 on symbols, +2.25 on capitals,
# against +2.18 for swapping one verb for a synonym of the SAME act.


# ===========================================================================
# 4. E8 -- stipulability                                      (~1 h per model)
# ===========================================================================
# The control that kills the obvious reading of E7. Atomic numbers reuse the
# same 118 entities as element symbols but cannot be stipulated, so a
# stipulability account predicts about zero there.
#
# Same seeded derangement for both models, so the subject -> false-answer map is
# identical even though different facts survive screening. Watch the header:
# "|false - true| for element_atomic_number" should read median ~33.

python E8_conventionality.py --config config.yaml \
  --out $G/analysis/conventionality_random \
  --false-answer-mode random --policies neutral,context,parametric --validate-only
python E8_conventionality.py --config config.yaml \
  --out $G/analysis/conventionality_random \
  --false-answer-mode random --policies neutral,context,parametric

python E8_conventionality.py --config config_qwen36.yaml \
  --out $Q/analysis/conventionality_random \
  --false-answer-mode random --policies neutral,context,parametric

# Expect (Gemma): symbols +12.10, atomic -5.50, capitals +1.79.
#        (Qwen):  symbols -1.09.


# ===========================================================================
# 5. E9 -- the thread that went nowhere                       (~2 min, no GPU)
# ===========================================================================
# E8 leaves a loose end: under an explicit "ignore the paragraph" instruction,
# a little of the false claim still leaks through on atomic numbers
# (bare 20.7% > assert 6.0% > explicit 0.0%) and on nothing else. Is that a
# fact about atomic numbers, or about facts the model holds loosely? Every fact
# already carries the measurement -- log P(true) - log P(false) on the
# context-free screening prompt -- so this costs no GPU.
#
# It comes back negative and is written up as such: see section 8.

python E9_knowledge_strength.py \
  --results gemma=$G/analysis/conventionality_random/conventionality_results.jsonl \
            qwen=$Q/analysis/conventionality_random/conventionality_results.jsonl \
  --out results/analysis_knowledge_strength

# Expect: Gemma's weak and strong halves of atomic numbers leak identically
# (20.7% vs 20.7%), and the weak halves of symbols and capitals stay at 0.0%.
# Strength does not explain the gradient.


# ===========================================================================
# 6. E10 -- plausibility: is it the relation or the near miss?   (~2-3 h)
# ===========================================================================
# Write-up section 7. Holds the entity fixed and varies only the distance from
# the true answer, so the act effect can be read at every distance. Also records
# log P(true) - log P(false at distance d) per row as a covariate. Pilot first.

python E10_answer_plausibility.py --config config.yaml \
  --out $G/analysis/plausibility --validate-only
python E10_answer_plausibility.py --config config.yaml \
  --out $G/analysis/plausibility_pilot --max-facts 12
python E10_answer_plausibility.py --config config.yaml \
  --out $G/analysis/plausibility

python E10_answer_plausibility.py --config config_qwen36.yaml \
  --out $Q/analysis/plausibility \
  --relations element_atomic_number,element_symbol

# Expect (Gemma, atomic act effect): -10.77 / -14.60 / -9.62 / -11.23 / -4.24
# across d=1, 2, 5, 20, random -- negative everywhere, every CI excluding zero.


# ===========================================================================
# 7. E11 -- the channel, all six at once              (~55 min Gemma, ~45 Qwen)
# ===========================================================================
# Write-up sections 3, 5 and 6. One run, every channel, both policies, both
# models -- there is no reason to split this. `inline` must reproduce E8's
# assert_r1 numbers or nothing else in the file is comparable.
#
# The four channels that answer "does the model track who is speaking":
#   inline          one user turn, no delimiter (the baseline)
#   delimited       the paragraph in <document> tags
#   system_guard    delimited, plus a system message saying the tags hold data
#   retrieved_turn  the document arrives in a prior ASSISTANT turn
#
# ...and the two that decide whether section 5 is about the CHANNEL or about
# the delimiter slot. Both carry the same guard sentences as `system_guard`,
# moved into the user turn with the <document> wrapper kept, so only the
# channel differs:
#   user_guard                  the guard sentences verbatim
#   user_guard_first_person     the same content in the user's own register,
#                               so a null cannot be blamed on the borrowed
#                               third-person wording

python E11_source_channel.py --config config.yaml \
  --out $G/analysis/channel --validate-only
python E11_source_channel.py --config config.yaml \
  --out $G/analysis/channel
python E11_source_channel.py --config config_qwen36.yaml \
  --out $Q/analysis/channel

# Expect (Gemma, assert_r1, neutral): inline 0.0% -> delimited 100.0%,
#   system_guard 100.0%, user_guard 100%, user_guard_first_person 97.5%.
#   Qwen: inline 0.0% -> delimited 62.7%, system_guard 58.5%.
# The point of the run: paired against `delimited`, Gemma's guards are
#   -0.2 (system), -3.1 (user), +5.5 (user, first person) on elements --
#   against -38.2 for renaming the tag <untrusted_content> in step 8.
#
# NOTE on rates from this run. Gemma leaks a thought-channel residue on some
# batches (`-Zn`, `-W-`, `aMajuro`: the right answer with a stray character
# glued on), at a rate that varies with batch composition and therefore with
# channel. Margins are teacher-forced and unaffected -- read margins. If you
# need rates, repair them with the exact-match rule in make_figures.py
# (`repaired_label`) and report that you did.


# ===========================================================================
# 8. E12 -- what the wrapper is, all thirteen at once      (~75 min per model)
# ===========================================================================
# Write-up section 4, and where the headline comes from. One run, every
# wrapper. Three things are being separated:
#
#   LAYOUT     blankline           blank lines, no markup
#   FENCE      dashes, quotes      a contentless fence
#   SYNTAX     tag_empty           <> -- brackets, no name at all
#              tag_nonsense        <qzx_block> -- a name that means nothing
#   WORD       label_document      "Document:" -- the word, no markup
#              tag_passage, tag_document, label_search
#   VALENCE    tag_trusted, tag_unreliable, tag_untrusted

python E12_delimiter.py --config config.yaml \
  --out $G/analysis/delimiter --validate-only
python E12_delimiter.py --config config.yaml \
  --out $G/analysis/delimiter
python E12_delimiter.py --config config_qwen36.yaml \
  --out $Q/analysis/delimiter

# Expect (Gemma, symbols, assert_r1, delta vs inline): blankline +1.3,
# untrusted +2.8, quotes +8.6, tag_empty +14.6, dashes +17.8, unreliable +21.1,
# qzx_block +31.2, Document: +38.5, document +41.0, trusted_content +43.4.
#
# CHECKPOINT -- the noise floor. `inline` is byte-identical in E8, E11 and E12,
# so three independent GPU sessions scored the same 118 prompts. The cell means
# must agree to a fraction of a logit or nothing in the ladder is readable:
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
#   E12  inline mean margin  -27.08  (n=118)
#   spread across three runs: 0.10 logits


# ===========================================================================
# 9. FIGURES AND EXAMPLES                                   (~10 s, no GPU)
# ===========================================================================
# Reads only committed result files, so a figure cannot disagree with the table
# beside it. Also writes figures/random_examples.md -- the randomly selected
# prompt block for the write-up, ordered by a hash of sample_id rather than
# chosen by hand.

python make_figures.py --results results --out figures


echo
echo "Done. Diff the headline numbers against WRITEUP.md. Anything that moved by"
echo "more than rounding is worth understanding, not editing."
