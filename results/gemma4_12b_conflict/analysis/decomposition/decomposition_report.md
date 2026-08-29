# E6: which part of the paragraph carries the swing?

Design `swap`, 3682 prompts, 263 facts, neutral policy unless noted.

## Endpoint reproduction

| Relation | Cell | Bundle | mean abs delta | max abs delta | n |
|---|---|---|---:|---:|---:|
| country_capital | endpoint_high | `heldout_paraphrase` | 0.477 | 4.094 | 145 |
| country_capital | endpoint_low | `validation` | 0.365 | 2.734 | 145 |
| element_symbol | endpoint_high | `validation` | 0.356 | 2.688 | 118 |
| element_symbol | endpoint_low | `heldout_paraphrase` | 0.262 | 2.000 | 118 |

## Per-factor decomposition (margin, logits)

| Relation | Factor | Kind | Delta | 95% CI | n |
|---|---|---|---:|---:|---:|
| country_capital | TOTAL | total | 12.18 | [+10.44, +13.99] | 145 |
| country_capital | claim | sufficiency | -3.58 | [-5.06, -2.08] | 145 |
| country_capital | claim | necessity | 9.39 | [+7.53, +11.26] | 145 |
| country_capital | filler | sufficiency | 6.65 | [+5.82, +7.53] | 145 |
| country_capital | filler | necessity | 11.82 | [+10.72, +12.93] | 145 |
| country_capital | question | sufficiency | -3.61 | [-4.50, -2.74] | 145 |
| country_capital | question | necessity | 8.02 | [+6.85, +9.19] | 145 |
| country_capital | constraint | sufficiency | 0.63 | [+0.29, +0.97] | 145 |
| country_capital | constraint | necessity | -0.25 | [-0.57, +0.10] | 145 |
| country_capital | ADDITIVITY_RESIDUAL | residual | 12.09 | -- | 145 |
| element_symbol | TOTAL | total | 30.87 | [+29.16, +32.55] | 118 |
| element_symbol | claim | sufficiency | 27.57 | [+25.55, +29.45] | 118 |
| element_symbol | claim | necessity | 28.12 | [+26.18, +29.97] | 118 |
| element_symbol | filler | sufficiency | -0.16 | [-0.57, +0.25] | 118 |
| element_symbol | filler | necessity | -4.51 | [-5.28, -3.73] | 118 |
| element_symbol | question | sufficiency | 6.26 | [+5.47, +7.11] | 118 |
| element_symbol | question | necessity | 1.75 | [+0.91, +2.60] | 118 |
| element_symbol | constraint | sufficiency | 1.13 | [+0.82, +1.47] | 118 |
| element_symbol | constraint | necessity | 3.82 | [+3.26, +4.42] | 118 |
| element_symbol | ADDITIVITY_RESIDUAL | residual | -3.92 | -- | 118 |

## Behaviour per cell

| Relation | Cell | n | Context | Parametric | Other | Mean margin |
|---|---|---:|---:|---:|---:|---:|
| country_capital | `endpoint_high` | 145 | 44.1% | 55.9% | 0.0% | -3.60 |
| country_capital | `endpoint_low` | 145 | 2.8% | 94.5% | 2.8% | -15.79 |
| country_capital | `high_minus_claim` | 145 | 11.7% | 88.3% | 0.0% | -12.99 |
| country_capital | `high_minus_constraint` | 145 | 43.4% | 56.6% | 0.0% | -3.35 |
| country_capital | `high_minus_filler` | 145 | 2.8% | 97.2% | 0.0% | -15.42 |
| country_capital | `high_minus_question` | 145 | 7.6% | 92.4% | 0.0% | -11.63 |
| country_capital | `low_plus_claim` | 145 | 2.8% | 97.2% | 0.0% | -19.36 |
| country_capital | `low_plus_constraint` | 145 | 3.4% | 95.9% | 0.7% | -15.15 |
| country_capital | `low_plus_filler` | 145 | 13.1% | 84.8% | 2.1% | -9.13 |
| country_capital | `low_plus_question` | 145 | 4.1% | 95.9% | 0.0% | -19.40 |
| element_symbol | `endpoint_high` | 118 | 76.3% | 23.7% | 0.0% | 3.16 |
| element_symbol | `endpoint_low` | 118 | 0.8% | 98.3% | 0.8% | -27.71 |
| element_symbol | `high_minus_claim` | 118 | 2.5% | 97.5% | 0.0% | -24.95 |
| element_symbol | `high_minus_constraint` | 118 | 55.1% | 44.9% | 0.0% | -0.66 |
| element_symbol | `high_minus_filler` | 118 | 89.0% | 11.0% | 0.0% | 7.68 |
| element_symbol | `high_minus_question` | 118 | 65.3% | 34.7% | 0.0% | 1.41 |
| element_symbol | `low_plus_claim` | 118 | 64.4% | 35.6% | 0.0% | -0.14 |
| element_symbol | `low_plus_constraint` | 118 | 0.8% | 98.3% | 0.8% | -26.58 |
| element_symbol | `low_plus_filler` | 118 | 0.8% | 98.3% | 0.8% | -27.87 |
| element_symbol | `low_plus_question` | 118 | 4.2% | 95.8% | 0.0% | -21.45 |

## How to read this

- **Endpoint reproduction gates everything.** These two cells were already measured in step 02. If they do not come back, the run is not comparable and nothing else in this file means anything.
- **Sufficiency** is `low + one factor` minus `low`: does this component alone move the model? **Necessity** is `high` minus `high with that component reverted`: does removing it collapse the effect? A component that owns the effect scores high on both.
- **Additivity.** If the four sufficiency effects sum to roughly the endpoint gap, the factors act independently and this table is the whole story. A large residual means they interact, and the single-factor reading is wrong -- say so rather than picking the biggest bar.
- **`claim` winning** is the interesting outcome: the two wordings differ in whether the false binding reads as a stipulation or an assertion, which is a claim about pragmatics, not about brittleness. Read the two prompts before asserting that interpretation -- the wording difference has to be one a person would actually describe that way.
- **`constraint` winning** would mean output-format pressure drives apparent source-trust. That is a smaller mechanism but a sharper warning for anyone building context-faithfulness evals.
- Cells are per-fact paired throughout, and intervals resample facts, so item difficulty cannot manufacture any of these differences.
