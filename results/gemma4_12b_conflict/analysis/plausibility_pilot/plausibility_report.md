# E10: plausibility of the false answer — google/gemma-4-12B-it

Entity held fixed; only how far the false answer sits from the true one varies. For `element_atomic_number` that distance is a number line (d=1, d=2, d=5, d=20, plus a random derangement); elsewhere it is `near` (the adjacent row's answer) versus `random`.


## Act effect at each distance (the decisive test)

| Relation | Distance | Act effect (stipulate − assert) | 95% CI | n |
|---|---|---:|---:|---:|
| element_atomic_number | `d1` | -4.02 | [-5.84, -2.05] | 12 |
| element_atomic_number | `d2` | -8.08 | [-12.33, -4.06] | 12 |
| element_atomic_number | `d5` | -3.31 | [-5.66, -1.07] | 12 |
| element_atomic_number | `d20` | -2.69 | [-5.03, -0.48] | 12 |
| element_atomic_number | `random` | -0.47 | [-2.48, +1.55] | 12 |
| element_symbol | `near` | 14.35 | [+11.34, +17.13] | 12 |
| element_symbol | `random` | 15.39 | [+12.66, +17.78] | 12 |
| country_capital | `near` | -0.62 | [-2.57, +1.77] | 12 |
| country_capital | `random` | -2.00 | [-3.56, -0.37] | 12 |

## Deference by distance (neutral policy)

| Relation | Cell | Distance | n | Context | Mean margin | Mean strength |
|---|---|---|---:|---:|---:|---:|
| element_atomic_number | `stipulate_r1` | `d1` | 12 | 25.0% | -3.60 | 18.03 |
| element_atomic_number | `stipulate_r1` | `d2` | 12 | 25.0% | -3.50 | 18.21 |
| element_atomic_number | `stipulate_r1` | `d5` | 12 | 33.3% | -3.83 | 20.08 |
| element_atomic_number | `stipulate_r1` | `d20` | 12 | 33.3% | -4.36 | 21.39 |
| element_atomic_number | `stipulate_r1` | `random` | 12 | 25.0% | -3.97 | 24.45 |
| element_atomic_number | `stipulate_r2` | `d1` | 12 | 16.7% | -7.34 | 18.03 |
| element_atomic_number | `stipulate_r2` | `d2` | 12 | 8.3% | -6.32 | 18.21 |
| element_atomic_number | `stipulate_r2` | `d5` | 12 | 8.3% | -9.67 | 20.08 |
| element_atomic_number | `stipulate_r2` | `d20` | 12 | 8.3% | -8.80 | 21.39 |
| element_atomic_number | `stipulate_r2` | `random` | 12 | 16.7% | -9.14 | 24.45 |
| element_atomic_number | `assert_r1` | `d1` | 12 | 41.7% | 0.33 | 18.03 |
| element_atomic_number | `assert_r1` | `d2` | 12 | 58.3% | 3.40 | 18.21 |
| element_atomic_number | `assert_r1` | `d5` | 12 | 25.0% | -2.00 | 20.08 |
| element_atomic_number | `assert_r1` | `d20` | 12 | 8.3% | -2.40 | 21.39 |
| element_atomic_number | `assert_r1` | `random` | 12 | 16.7% | -3.71 | 24.45 |
| element_atomic_number | `assert_r2` | `d1` | 12 | 25.0% | -3.22 | 18.03 |
| element_atomic_number | `assert_r2` | `d2` | 12 | 58.3% | 2.93 | 18.21 |
| element_atomic_number | `assert_r2` | `d5` | 12 | 8.3% | -4.89 | 20.08 |
| element_atomic_number | `assert_r2` | `d20` | 12 | 8.3% | -5.38 | 21.39 |
| element_atomic_number | `assert_r2` | `random` | 12 | 8.3% | -8.47 | 24.45 |
| element_atomic_number | `bare` | `d1` | 12 | 0.0% | -4.90 | 18.03 |
| element_atomic_number | `bare` | `d2` | 12 | 58.3% | 3.79 | 18.21 |
| element_atomic_number | `bare` | `d5` | 12 | 0.0% | -5.18 | 20.08 |
| element_atomic_number | `bare` | `d20` | 12 | 16.7% | -3.34 | 21.39 |
| element_atomic_number | `bare` | `random` | 12 | 0.0% | -4.19 | 24.45 |
| element_atomic_number | `explicit_stipulation` | `d1` | 12 | 100.0% | 16.79 | 18.03 |
| element_atomic_number | `explicit_stipulation` | `d2` | 12 | 100.0% | 16.99 | 18.21 |
| element_atomic_number | `explicit_stipulation` | `d5` | 12 | 100.0% | 17.47 | 20.08 |
| element_atomic_number | `explicit_stipulation` | `d20` | 12 | 100.0% | 14.99 | 21.39 |
| element_atomic_number | `explicit_stipulation` | `random` | 12 | 100.0% | 17.20 | 24.45 |
| element_symbol | `stipulate_r1` | `near` | 12 | 50.0% | -0.81 | 28.64 |
| element_symbol | `stipulate_r1` | `random` | 12 | 66.7% | 1.77 | 33.91 |
| element_symbol | `stipulate_r2` | `near` | 12 | 41.7% | -5.87 | 28.64 |
| element_symbol | `stipulate_r2` | `random` | 12 | 33.3% | -5.34 | 33.91 |
| element_symbol | `assert_r1` | `near` | 12 | 0.0% | -17.69 | 28.64 |
| element_symbol | `assert_r1` | `random` | 12 | 0.0% | -19.74 | 33.91 |
| element_symbol | `assert_r2` | `near` | 12 | 0.0% | -17.69 | 28.64 |
| element_symbol | `assert_r2` | `random` | 12 | 25.0% | -14.61 | 33.91 |
| element_symbol | `bare` | `near` | 12 | 25.0% | -7.92 | 28.64 |
| element_symbol | `bare` | `random` | 12 | 50.0% | -3.11 | 33.91 |
| element_symbol | `explicit_stipulation` | `near` | 12 | 100.0% | 15.46 | 28.64 |
| element_symbol | `explicit_stipulation` | `random` | 12 | 100.0% | 18.33 | 33.91 |
| country_capital | `stipulate_r1` | `near` | 12 | 0.0% | -22.71 | 30.00 |
| country_capital | `stipulate_r1` | `random` | 12 | 0.0% | -22.93 | 41.60 |
| country_capital | `stipulate_r2` | `near` | 12 | 0.0% | -24.08 | 30.00 |
| country_capital | `stipulate_r2` | `random` | 12 | 0.0% | -22.41 | 41.60 |
| country_capital | `assert_r1` | `near` | 12 | 0.0% | -20.70 | 30.00 |
| country_capital | `assert_r1` | `random` | 12 | 0.0% | -20.17 | 41.60 |
| country_capital | `assert_r2` | `near` | 12 | 0.0% | -24.86 | 30.00 |
| country_capital | `assert_r2` | `random` | 12 | 0.0% | -21.18 | 41.60 |
| country_capital | `bare` | `near` | 12 | 25.0% | -6.43 | 30.00 |
| country_capital | `bare` | `random` | 12 | 50.0% | -2.91 | 41.60 |
| country_capital | `explicit_stipulation` | `near` | 12 | 100.0% | 24.86 | 30.00 |
| country_capital | `explicit_stipulation` | `random` | 12 | 100.0% | 26.25 | 41.60 |

## Leakage under `ignore the paragraph`

| Relation | Distance | Cell | Leak rate | n |
|---|---|---|---:|---:|
| element_atomic_number | `d1` | `bare` | 0.0% | 12 |
| element_atomic_number | `d1` | `assert_r1` | 0.0% | 12 |
| element_atomic_number | `d1` | `explicit_stipulation` | 0.0% | 12 |
| element_atomic_number | `d2` | `bare` | 16.7% | 12 |
| element_atomic_number | `d2` | `assert_r1` | 0.0% | 12 |
| element_atomic_number | `d2` | `explicit_stipulation` | 0.0% | 12 |
| element_atomic_number | `d5` | `bare` | 0.0% | 12 |
| element_atomic_number | `d5` | `assert_r1` | 0.0% | 12 |
| element_atomic_number | `d5` | `explicit_stipulation` | 0.0% | 12 |
| element_atomic_number | `d20` | `bare` | 0.0% | 12 |
| element_atomic_number | `d20` | `assert_r1` | 0.0% | 12 |
| element_atomic_number | `d20` | `explicit_stipulation` | 0.0% | 12 |
| element_atomic_number | `random` | `bare` | 0.0% | 12 |
| element_atomic_number | `random` | `assert_r1` | 0.0% | 12 |
| element_atomic_number | `random` | `explicit_stipulation` | 0.0% | 12 |
| element_symbol | `near` | `bare` | 0.0% | 12 |
| element_symbol | `near` | `assert_r1` | 0.0% | 12 |
| element_symbol | `near` | `explicit_stipulation` | 0.0% | 12 |
| element_symbol | `random` | `bare` | 0.0% | 12 |
| element_symbol | `random` | `assert_r1` | 0.0% | 12 |
| element_symbol | `random` | `explicit_stipulation` | 0.0% | 12 |
| country_capital | `near` | `bare` | 0.0% | 12 |
| country_capital | `near` | `assert_r1` | 0.0% | 12 |
| country_capital | `near` | `explicit_stipulation` | 0.0% | 12 |
| country_capital | `random` | `bare` | 0.0% | 12 |
| country_capital | `random` | `assert_r1` | 0.0% | 12 |
| country_capital | `random` | `explicit_stipulation` | 0.0% | 12 |

## Strength as a mediator, entity fixed

| Relation | Cell | rho(strength, margin) | n |
|---|---|---:|---:|
| element_atomic_number | `bare` | -0.021 | 60 |
| element_atomic_number | `assert_r1` | -0.156 | 60 |
| element_symbol | `bare` | -0.340 | 24 |
| element_symbol | `assert_r1` | -0.752 | 24 |
| country_capital | `bare` | +0.350 | 24 |
| country_capital | `assert_r1` | +0.158 | 24 |

## How to read this

- **A2 is the one that matters.** E8's act effect on atomic numbers was −10.83, measured where every false answer was true+1. If the effect keeps that sign and size at `d20` and `random`, the falsification of the stipulability account stands and is now confound-free. If it collapses toward zero as distance grows, the falsification was an artefact of near-miss claims and section 5 has to be rewritten.
- **A1 tells you how big the confound was.** Compare `near`/`d1` against `random` within `element_symbol` and `country_capital`: that gap is exactly the difference between the Gemma and Qwen E8 runs, which used different modes.
- **A3** asks whether the bare > assert > explicit leakage gradient is a property of atomic numbers or of near-miss claims. It was only ever visible on atomic numbers, and atomic numbers were the only relation pinned at distance 1.
- **A4** is E9's question asked properly. Strength and distance move together within one entity, so a strong negative rho means the model is tracking how confidently it holds the discrimination, not what kind of fact it is.
- Margins are teacher-forced and unaffected by answer formatting; the rates classify the answer with any reasoning preamble stripped, as E8 does and E6/E7 do not.
