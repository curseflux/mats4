# Meaningless Tags, Meaningful Impact

What makes a language model believe a paragraph that contradicts what it knows?

I hand a model a short paragraph asserting something false, then ask the
question the paragraph answers wrongly. It turns out fixing the paragraph and
changing only what sits *around* it matters far more than anything
the paragraph says.

MATS 12.0 application (Neel Nanda stream). Write-up in `WRITEUP.docx`.

## Metrics

- **Paragraph rate** — fraction of facts where the model gives the paragraph's
  false answer instead of the true one.
- **Margin (M)** — `log P(paragraph's answer) − log P(true answer)`. Negative
  means it prefers the true answer, positive the paragraph's, zero a coin flip.
  `ΔM` is a difference in M between two named conditions.

Everything is behavioural. No training, no activation editing.

## Setup

```bash
pip install torch
pip install "transformers==5.15.0" accelerate pyyaml numpy scipy matplotlib
```

Set `paths.hf_cache_dir` in `config.yaml` and `config_qwen36.yaml` (relative
paths resolve from the config file).

Then follow `cmds.sh`, which lists every command in order with expected outputs.
Most scripts take `--validate-only`, which checks inputs and prints example
prompts without loading a model — worth running first. Full sweep is roughly
5 GPU-hours on an A100 40GB.

## Files

| File | What it does |
|---|---|
| `cmds.sh` | Every command in order, with the numbers each step should produce |
| `common.py` | Shared utilities: config loading and hashing, chat templating, batched generation, teacher-forced scoring, cluster bootstrap |
| `build_conflict_awareness_dataset.py` | Builds the dataset: 153 country/capital pairs, 118 IUPAC elements, claim templates, and a seeded derangement so every answer string appears once as a truth and once as a falsehood |
| `01_screen_knowledge.py` | Per-model screen — which facts does this model actually know, context-free, across three paraphrases |
| `02_collect_model_data.py` | The main factorial grid: claim truth × relevance × answer-source policy |
| `E6_template_decomposition.py` | Which part of the paragraph carries the deference swing |
| `E7_claim_phrasing.py` | Which property of the claim sentence drives it (speech act, paraphrase, source authority, hedging) |
| `E8_conventionality.py` | Whether the claim is one a source could legitimately stipulate |
| `E9_knowledge_strength.py` | Is the gradient about the relation, or about weakly-held facts? Analysis only, no GPU |
| `E10_answer_plausibility.py` | Relation vs. plausibility of the particular false answer |
| `E11_source_channel.py` | The channel: inline, delimited, a warning in three slots, a simulated retrieval turn |
| `E12_delimiter.py` | 17 wrappers over the identical paragraph — the headline experiment |
| `make_figures.py` | Figures, plus randomly sampled example prompts (`figures/examples.md`) |
| `config.yaml` / `config_qwen36.yaml` | Gemma 4 12B and Qwen 3.6 27B. Both read the *same* generated dataset |
| `results/` | Committed analysis outputs |
| `figures/` | Generated figures |
