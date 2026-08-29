# E9: is the leakage gradient about a relation, or about fact strength?

Leakage is measured under the `parametric` policy — the user instructing the model to ignore the paragraph. Knowledge strength is `log P(true) − log P(false)` on the context-free screening prompt, so it is measured before any manipulation touches the fact.

## Strength by relation

| Model | Relation | n | Median strength | q10 | q90 |
|---|---|---:|---:|---:|---:|
| gemma | country_capital | 143 | 38.60 | 30.79 | 50.59 |
| gemma | element_atomic_number | 116 | 21.84 | 15.80 | 26.66 |
| gemma | element_symbol | 118 | 36.56 | 28.01 | 41.29 |
| qwen | country_capital | 146 | 20.92 | 15.81 | 25.68 |
| qwen | element_atomic_number | 116 | 15.95 | 13.39 | 18.65 |
| qwen | element_symbol | 118 | 20.03 | 16.00 | 23.22 |

## The gradient inside each relation's strength bins

| Model | Relation | Bin | n | bare | assert_r1 | explicit_stipulation | neutral (bare) |
|---|---|---|---:|---:|---:|---:|---:|
| gemma | country_capital | weak | 71 | 0.0% | 0.0% | 0.0% | 18.3% |
| gemma | country_capital | strong | 72 | 0.0% | 0.0% | 0.0% | 26.4% |
| gemma | element_atomic_number | weak | 58 | 20.7% | 6.9% | 0.0% | 44.8% |
| gemma | element_atomic_number | strong | 58 | 20.7% | 5.2% | 0.0% | 36.2% |
| gemma | element_symbol | weak | 59 | 0.0% | 0.0% | 1.7% | 8.5% |
| gemma | element_symbol | strong | 59 | 0.0% | 0.0% | 0.0% | 6.8% |
| qwen | country_capital | weak | 73 | 0.0% | 0.0% | 0.0% | 5.5% |
| qwen | country_capital | strong | 73 | 0.0% | 0.0% | 0.0% | 0.0% |
| qwen | element_atomic_number | weak | 58 | 1.7% | 1.7% | 0.0% | 63.8% |
| qwen | element_atomic_number | strong | 58 | 0.0% | 0.0% | 0.0% | 81.0% |
| qwen | element_symbol | weak | 59 | 0.0% | 0.0% | 0.0% | 33.9% |
| qwen | element_symbol | strong | 59 | 0.0% | 0.0% | 0.0% | 37.3% |

## Leakage vs strength, continuously

| Model | Relation | Cell | rho(strength, leak) | rho(strength, margin) | n |
|---|---|---|---:|---:|---:|
| gemma | country_capital | bare | nan | -0.828 | 143 |
| gemma | country_capital | assert_r1 | nan | -0.831 | 143 |
| gemma | country_capital | explicit_stipulation | nan | -0.682 | 143 |
| gemma | element_atomic_number | bare | -0.121 | -0.306 | 116 |
| gemma | element_atomic_number | assert_r1 | -0.158 | -0.501 | 116 |
| gemma | element_atomic_number | explicit_stipulation | nan | -0.497 | 116 |
| gemma | element_symbol | bare | nan | -0.879 | 118 |
| gemma | element_symbol | assert_r1 | nan | -0.926 | 118 |
| gemma | element_symbol | explicit_stipulation | -0.156 | -0.754 | 118 |
| gemma | POOLED | bare | -0.324 | -0.926 | 377 |
| gemma | POOLED | assert_r1 | -0.189 | -0.934 | 377 |
| gemma | POOLED | explicit_stipulation | -0.068 | -0.878 | 377 |
| qwen | country_capital | bare | nan | -0.453 | 146 |
| qwen | country_capital | assert_r1 | nan | -0.529 | 146 |
| qwen | country_capital | explicit_stipulation | nan | -0.330 | 146 |
| qwen | element_atomic_number | bare | -0.160 | -0.569 | 116 |
| qwen | element_atomic_number | assert_r1 | -0.160 | -0.497 | 116 |
| qwen | element_atomic_number | explicit_stipulation | nan | -0.334 | 116 |
| qwen | element_symbol | bare | nan | -0.367 | 118 |
| qwen | element_symbol | assert_r1 | nan | -0.491 | 118 |
| qwen | element_symbol | explicit_stipulation | nan | -0.515 | 118 |
| qwen | POOLED | bare | -0.088 | -0.653 | 380 |
| qwen | POOLED | assert_r1 | -0.088 | -0.740 | 380 |
| qwen | POOLED | explicit_stipulation | nan | -0.457 | 380 |

## How to read this

- **The question.** The bare > assert > explicit gradient was only visible on atomic numbers, because every other relation sat at 0% leakage. Is it a fact about atomic numbers, or about facts the model holds loosely?
- **T1 gates T4.** If the relations' strength ranges do not overlap, relation and strength are confounded here and no matched comparison exists. Say that rather than implying one was made.
- **T2** is the direct test: the gradient appearing in the weak half of symbols and capitals too would make it general. Note that a weak half is only weak *relative to its own relation* — if the weakest symbols are still firmly held, this test has no room to show anything, and T3 carries the argument instead.
- **T3 needs no bins.** A consistently negative rho inside every relation says leakage falls with strength wherever it is measured, which supports strength over relation identity even without overlap.
- **The confound.** `neutral (bare)` is the same cell without the user instruction. If weak facts simply defer more everywhere, that column shows it, and the gradient claim has to be stated relative to that baseline rather than absolutely.
- Leakage is binary per fact, so the rates are what they are; the graded `bare − explicit` margin contrast printed to the console is the version with confidence intervals, clustered on facts.
