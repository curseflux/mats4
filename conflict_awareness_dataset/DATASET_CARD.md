# Conflict Awareness Under Instructed Obedience — Candidate Dataset

Schema version: `1.0.0`  
Counterbalance rounds: `1`  
Policies: `neutral, context, parametric`

## Files

- `facts.jsonl`: candidate world facts and deterministic split metadata.
- `screening.jsonl`: context-free prompts used to establish model-specific parametric knowledge.
- `experiment.jsonl`: truth × relevance × answer-source-policy prompts.
- `manifest.json`: full schema, templates, counts, hashes, and generation settings.

## Required filtering before the main experiment

`query_conflict_label=true` means the paragraph contradicts the curated world fact and is relevant to the query. It does **not** yet prove an effective context-memory conflict for a specific model. A fact should enter the main experiment only after the evaluated model:

1. gives the true answer on the context-free screening prompts across prompt bundles;
2. assigns the true answer greater sequence log-probability than every false answer assigned to that fact; and
3. produces a parseable one-word answer.

For a `false_irrelevant` record, also require that the model passed screening for the `claim_fact_id` before treating `claim_conflict_label` as an effective false-claim signal.

Do not filter facts based on whether the context-grounded prompt later flips the answer. Flip rate and the continuous context-minus-parametric log-probability margin are experimental outcomes.

World-fact curation and model knowledge are intentionally separate.  Relation-level
reference links, the audit date, and notable exclusion rules are recorded in
`manifest.json`; each fact also carries the audit date.

## Leakage controls

- False answers are permutations of true answers, not a separate vocabulary.
- Every fact is used once as an irrelevant distractor per counterbalance round.
- Query facts, distractor facts, and false-answer sources are assigned within
  the same `fact_split` **and** `cv_fold`; no held-out fact can enter a training
  prompt through an irrelevant paragraph or false answer.
- `content_pair_id` links prompts whose content is identical apart from answer-source policy.
- `matched_factorial_group_id` links the four truth × relevance cells within a
  prompt bundle; `stimulus_family_id` additionally links those cells across bundles.
- The `heldout_paraphrase` bundle should not be used to fit probes or select layers.
- Character spans are authoritative; do not rediscover positions by searching prompt strings.

## Counts

```json
{
  "by_relation": {
    "country_capital": {
      "condition_counts": {
        "false_irrelevant": 1377,
        "false_relevant": 1377,
        "true_irrelevant": 1377,
        "true_relevant": 1377
      },
      "display_name": "country capital",
      "experiment_count": 5508,
      "fact_count": 153,
      "fact_split_counts": {
        "test": 32,
        "train": 91,
        "validation": 30
      },
      "policy_counts": {
        "context": 1836,
        "neutral": 1836,
        "parametric": 1836
      },
      "screening_count": 459,
      "template_bundle_counts": {
        "development": 1836,
        "heldout_paraphrase": 1836,
        "validation": 1836
      },
      "transfer_role": "development_relation"
    },
    "element_symbol": {
      "condition_counts": {
        "false_irrelevant": 1062,
        "false_relevant": 1062,
        "true_irrelevant": 1062,
        "true_relevant": 1062
      },
      "display_name": "chemical element symbol",
      "experiment_count": 4248,
      "fact_count": 118,
      "fact_split_counts": {
        "ood_test": 118
      },
      "policy_counts": {
        "context": 1416,
        "neutral": 1416,
        "parametric": 1416
      },
      "screening_count": 354,
      "template_bundle_counts": {
        "development": 1416,
        "heldout_paraphrase": 1416,
        "validation": 1416
      },
      "transfer_role": "heldout_transfer_relation"
    }
  },
  "experiment_records": 9756,
  "facts": 271,
  "screening_records": 813
}
```
