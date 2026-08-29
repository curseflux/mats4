# E7: which property of the claim sentence drives deference?

5523 prompts, 263 facts, neutral policy. Subject, false answer, filler, question and response constraint are held fixed at each relation's E6 low-endpoint frame; only the claim sentence varies.

## Main effects (margin, logits)

| Relation | Factor | Contrast | Delta | 95% CI | n |
|---|---|---|---:|---:|---:|
| element_symbol | act | stipulate - assert | 9.40 | [+8.42, +10.46] | 118 |
| element_symbol | realization | r1 - r2 | 2.18 | [+1.71, +2.67] | 118 |
| element_symbol | source | high - low | 3.39 | [+2.52, +4.32] | 118 |
| element_symbol | persistence | present - absent | -5.23 | [-5.73, -4.76] | 118 |
| country_capital | act | stipulate - assert | 2.25 | [+1.40, +3.17] | 145 |
| country_capital | realization | r1 - r2 | 1.33 | [+1.05, +1.62] | 145 |
| country_capital | source | high - low | 3.93 | [+3.46, +4.44] | 145 |
| country_capital | persistence | present - absent | -1.98 | [-2.22, -1.75] | 145 |

## Behaviour per cell

| Relation | Cell | n | Context | Parametric | Other | Mean margin |
|---|---|---:|---:|---:|---:|---:|
| element_symbol | `assert_r1_high_absent` | 118 | 2.5% | 65.3% | 32.2% | -25.41 |
| element_symbol | `assert_r1_high_present` | 118 | 3.4% | 96.6% | 0.0% | -24.65 |
| element_symbol | `assert_r1_low_absent` | 118 | 0.8% | 57.6% | 41.5% | -28.37 |
| element_symbol | `assert_r1_low_present` | 118 | 0.0% | 100.0% | 0.0% | -30.70 |
| element_symbol | `assert_r2_high_absent` | 118 | 3.4% | 55.1% | 41.5% | -24.42 |
| element_symbol | `assert_r2_high_present` | 118 | 3.4% | 96.6% | 0.0% | -26.82 |
| element_symbol | `assert_r2_low_absent` | 118 | 0.8% | 76.3% | 22.9% | -29.06 |
| element_symbol | `assert_r2_low_present` | 118 | 0.0% | 100.0% | 0.0% | -31.97 |
| element_symbol | `bare` | 118 | 8.5% | 77.1% | 14.4% | -14.48 |
| element_symbol | `irrelevant_assert` | 118 | 0.0% | 88.1% | 11.9% | -32.45 |
| element_symbol | `irrelevant_stipulate` | 118 | 0.0% | 77.1% | 22.9% | -32.01 |
| element_symbol | `orig_high` | 118 | 64.4% | 35.6% | 0.0% | -0.14 |
| element_symbol | `orig_low` | 118 | 0.8% | 98.3% | 0.8% | -27.71 |
| element_symbol | `stipulate_r1_high_absent` | 118 | 18.6% | 68.6% | 12.7% | -10.18 |
| element_symbol | `stipulate_r1_high_present` | 118 | 5.9% | 83.1% | 11.0% | -21.52 |
| element_symbol | `stipulate_r1_low_absent` | 118 | 17.8% | 76.3% | 5.9% | -14.87 |
| element_symbol | `stipulate_r1_low_present` | 118 | 6.8% | 92.4% | 0.8% | -19.37 |
| element_symbol | `stipulate_r2_high_absent` | 118 | 6.8% | 89.8% | 3.4% | -15.80 |
| element_symbol | `stipulate_r2_high_present` | 118 | 5.1% | 94.1% | 0.8% | -21.41 |
| element_symbol | `stipulate_r2_low_absent` | 118 | 8.5% | 79.7% | 11.9% | -14.74 |
| element_symbol | `stipulate_r2_low_present` | 118 | 0.0% | 81.4% | 18.6% | -28.28 |
| country_capital | `assert_r1_high_absent` | 145 | 0.0% | 83.4% | 16.6% | -27.38 |
| country_capital | `assert_r1_high_present` | 145 | 0.0% | 100.0% | 0.0% | -29.59 |
| country_capital | `assert_r1_low_absent` | 145 | 0.0% | 80.7% | 19.3% | -32.16 |
| country_capital | `assert_r1_low_present` | 145 | 0.0% | 80.0% | 20.0% | -33.75 |
| country_capital | `assert_r2_high_absent` | 145 | 0.0% | 80.7% | 19.3% | -30.01 |
| country_capital | `assert_r2_high_present` | 145 | 0.0% | 100.0% | 0.0% | -31.44 |
| country_capital | `assert_r2_low_absent` | 145 | 0.0% | 86.9% | 13.1% | -34.58 |
| country_capital | `assert_r2_low_present` | 145 | 0.0% | 95.9% | 4.1% | -35.33 |
| country_capital | `bare` | 145 | 22.8% | 68.3% | 9.0% | -9.34 |
| country_capital | `irrelevant_assert` | 145 | 0.7% | 89.0% | 10.3% | -33.66 |
| country_capital | `irrelevant_stipulate` | 145 | 0.0% | 95.2% | 4.8% | -33.60 |
| country_capital | `orig_high` | 145 | 2.8% | 97.2% | 0.0% | -19.36 |
| country_capital | `orig_low` | 145 | 3.4% | 94.5% | 2.1% | -15.78 |
| country_capital | `stipulate_r1_high_absent` | 145 | 2.8% | 80.0% | 17.2% | -26.84 |
| country_capital | `stipulate_r1_high_present` | 145 | 1.4% | 96.6% | 2.1% | -28.68 |
| country_capital | `stipulate_r1_low_absent` | 145 | 2.8% | 78.6% | 18.6% | -28.95 |
| country_capital | `stipulate_r1_low_present` | 145 | 1.4% | 91.0% | 7.6% | -32.58 |
| country_capital | `stipulate_r2_high_absent` | 145 | 1.4% | 83.4% | 15.2% | -27.00 |
| country_capital | `stipulate_r2_high_present` | 145 | 0.7% | 99.3% | 0.0% | -28.58 |
| country_capital | `stipulate_r2_low_absent` | 145 | 0.7% | 86.2% | 13.1% | -30.42 |
| country_capital | `stipulate_r2_low_present` | 145 | 0.0% | 82.8% | 17.2% | -33.19 |

## How to read this

- **`act` is the hypothesis.** A large positive stipulate-minus-assert effect in BOTH relations, surviving the `realization` control, means the model treats a source that ADOPTS a convention differently from one that ASSERTS a fact. That is a claim about pragmatics, and it is the version of this finding worth writing up.
- **`realization` is the killer control.** If swapping one verb for a synonym of the same act moves the margin as much as changing the act, the result is lexical and the pragmatic reading is wrong. Report this number next to `act`, never on its own.
- **`source` and `persistence`** are the two obvious alternative explanations for E6's endpoint gap. If either rivals `act`, say so.
- **`bare`** shows where an unattributed assertion sits. If it lands near the assert cells, attribution is not what matters; if it is far from both, the whole effect depends on there being a source at all.
- **A2 must be near zero.** A phrasing that lifts the claim answer even when the claim is about another entity is a salience effect, and the conflict-resolution reading would be wrong.
- Anchors are the E6 cells rebuilt here. If they do not reproduce, nothing above is comparable to E6 and the frame has drifted.
