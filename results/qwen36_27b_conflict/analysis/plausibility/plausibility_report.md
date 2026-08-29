# E10: plausibility of the false answer — Qwen/Qwen3.6-27B

Entity held fixed; only how far the false answer sits from the true one varies. For `element_atomic_number` that distance is a number line (d=1, d=2, d=5, d=20, plus a random derangement); elsewhere it is `near` (the adjacent row's answer) versus `random`.


## Act effect at each distance (the decisive test)

| Relation | Distance | Act effect (stipulate − assert) | 95% CI | n |
|---|---|---:|---:|---:|
| element_atomic_number | `d1` | -2.67 | [-3.38, -2.01] | 116 |
| element_atomic_number | `d2` | -5.49 | [-6.49, -4.48] | 116 |
| element_atomic_number | `d5` | -1.95 | [-2.66, -1.34] | 116 |
| element_atomic_number | `d20` | -0.83 | [-1.46, -0.23] | 116 |
| element_atomic_number | `random` | -1.12 | [-1.60, -0.69] | 116 |
| element_symbol | `near` | -0.86 | [-1.18, -0.54] | 118 |
| element_symbol | `random` | -0.98 | [-1.36, -0.62] | 118 |

## Deference by distance (neutral policy)

| Relation | Cell | Distance | n | Context | Mean margin | Mean strength |
|---|---|---|---:|---:|---:|---:|
| element_atomic_number | `stipulate_r1` | `d1` | 116 | 10.3% | -2.45 | 11.54 |
| element_atomic_number | `stipulate_r1` | `d2` | 116 | 13.8% | -1.85 | 12.06 |
| element_atomic_number | `stipulate_r1` | `d5` | 116 | 3.4% | -4.10 | 14.42 |
| element_atomic_number | `stipulate_r1` | `d20` | 116 | 7.8% | -3.23 | 14.93 |
| element_atomic_number | `stipulate_r1` | `random` | 116 | 0.9% | -4.97 | 16.26 |
| element_atomic_number | `stipulate_r2` | `d1` | 116 | 6.9% | -3.25 | 11.54 |
| element_atomic_number | `stipulate_r2` | `d2` | 116 | 11.2% | -2.58 | 12.06 |
| element_atomic_number | `stipulate_r2` | `d5` | 116 | 3.4% | -5.22 | 14.42 |
| element_atomic_number | `stipulate_r2` | `d20` | 116 | 2.6% | -4.71 | 14.93 |
| element_atomic_number | `stipulate_r2` | `random` | 116 | 0.0% | -6.25 | 16.26 |
| element_atomic_number | `assert_r1` | `d1` | 116 | 33.6% | 0.34 | 11.54 |
| element_atomic_number | `assert_r1` | `d2` | 116 | 55.2% | 3.51 | 12.06 |
| element_atomic_number | `assert_r1` | `d5` | 116 | 12.1% | -2.18 | 14.42 |
| element_atomic_number | `assert_r1` | `d20` | 116 | 6.0% | -2.46 | 14.93 |
| element_atomic_number | `assert_r1` | `random` | 116 | 3.4% | -3.85 | 16.26 |
| element_atomic_number | `assert_r2` | `d1` | 116 | 18.1% | -0.69 | 11.54 |
| element_atomic_number | `assert_r2` | `d2` | 116 | 50.0% | 3.03 | 12.06 |
| element_atomic_number | `assert_r2` | `d5` | 116 | 8.6% | -3.23 | 14.42 |
| element_atomic_number | `assert_r2` | `d20` | 116 | 1.7% | -3.82 | 14.93 |
| element_atomic_number | `assert_r2` | `random` | 116 | 2.6% | -5.13 | 16.26 |
| element_atomic_number | `bare` | `d1` | 116 | 80.2% | 3.71 | 11.54 |
| element_atomic_number | `bare` | `d2` | 116 | 88.8% | 5.99 | 12.06 |
| element_atomic_number | `bare` | `d5` | 116 | 70.7% | 1.87 | 14.42 |
| element_atomic_number | `bare` | `d20` | 116 | 81.0% | 1.93 | 14.93 |
| element_atomic_number | `bare` | `random` | 116 | 79.3% | 1.02 | 16.26 |
| element_atomic_number | `explicit_stipulation` | `d1` | 116 | 100.0% | 7.06 | 11.54 |
| element_atomic_number | `explicit_stipulation` | `d2` | 116 | 100.0% | 8.25 | 12.06 |
| element_atomic_number | `explicit_stipulation` | `d5` | 116 | 100.0% | 7.84 | 14.42 |
| element_atomic_number | `explicit_stipulation` | `d20` | 116 | 100.0% | 7.35 | 14.93 |
| element_atomic_number | `explicit_stipulation` | `random` | 116 | 100.0% | 6.82 | 16.26 |
| element_symbol | `stipulate_r1` | `near` | 118 | 0.0% | -6.26 | 15.01 |
| element_symbol | `stipulate_r1` | `random` | 118 | 0.0% | -8.36 | 19.42 |
| element_symbol | `stipulate_r2` | `near` | 118 | 0.0% | -7.37 | 15.01 |
| element_symbol | `stipulate_r2` | `random` | 118 | 0.8% | -10.00 | 19.42 |
| element_symbol | `assert_r1` | `near` | 118 | 0.8% | -5.10 | 15.01 |
| element_symbol | `assert_r1` | `random` | 118 | 0.8% | -7.36 | 19.42 |
| element_symbol | `assert_r2` | `near` | 118 | 0.0% | -6.82 | 15.01 |
| element_symbol | `assert_r2` | `random` | 118 | 0.0% | -9.04 | 19.42 |
| element_symbol | `bare` | `near` | 118 | 22.9% | -0.73 | 15.01 |
| element_symbol | `bare` | `random` | 118 | 34.7% | -0.24 | 19.42 |
| element_symbol | `explicit_stipulation` | `near` | 118 | 98.3% | 2.11 | 15.01 |
| element_symbol | `explicit_stipulation` | `random` | 118 | 95.8% | 1.75 | 19.42 |

## Leakage under `ignore the paragraph`

| Relation | Distance | Cell | Leak rate | n |
|---|---|---|---:|---:|
| element_atomic_number | `d1` | `bare` | 37.1% | 116 |
| element_atomic_number | `d1` | `assert_r1` | 12.9% | 116 |
| element_atomic_number | `d1` | `explicit_stipulation` | 0.0% | 116 |
| element_atomic_number | `d2` | `bare` | 60.3% | 116 |
| element_atomic_number | `d2` | `assert_r1` | 40.5% | 116 |
| element_atomic_number | `d2` | `explicit_stipulation` | 0.0% | 116 |
| element_atomic_number | `d5` | `bare` | 11.2% | 116 |
| element_atomic_number | `d5` | `assert_r1` | 5.2% | 116 |
| element_atomic_number | `d5` | `explicit_stipulation` | 0.0% | 116 |
| element_atomic_number | `d20` | `bare` | 4.3% | 116 |
| element_atomic_number | `d20` | `assert_r1` | 1.7% | 116 |
| element_atomic_number | `d20` | `explicit_stipulation` | 0.0% | 116 |
| element_atomic_number | `random` | `bare` | 1.7% | 116 |
| element_atomic_number | `random` | `assert_r1` | 1.7% | 116 |
| element_atomic_number | `random` | `explicit_stipulation` | 0.0% | 116 |
| element_symbol | `near` | `bare` | 0.0% | 118 |
| element_symbol | `near` | `assert_r1` | 0.0% | 118 |
| element_symbol | `near` | `explicit_stipulation` | 0.0% | 118 |
| element_symbol | `random` | `bare` | 0.8% | 118 |
| element_symbol | `random` | `assert_r1` | 0.0% | 118 |
| element_symbol | `random` | `explicit_stipulation` | 0.0% | 118 |

## Strength as a mediator, entity fixed

| Relation | Cell | rho(strength, margin) | n |
|---|---|---:|---:|
| element_atomic_number | `bare` | -0.215 | 580 |
| element_atomic_number | `assert_r1` | -0.438 | 580 |
| element_symbol | `bare` | +0.077 | 236 |
| element_symbol | `assert_r1` | -0.436 | 236 |

## How to read this

- **A2 is the one that matters.** E8's act effect on atomic numbers was −10.83, measured where every false answer was true+1. If the effect keeps that sign and size at `d20` and `random`, the falsification of the stipulability account stands and is now confound-free. If it collapses toward zero as distance grows, the falsification was an artefact of near-miss claims and section 5 has to be rewritten.
- **A1 tells you how big the confound was.** Compare `near`/`d1` against `random` within `element_symbol` and `country_capital`: that gap is exactly the difference between the Gemma and Qwen E8 runs, which used different modes.
- **A3** asks whether the bare > assert > explicit leakage gradient is a property of atomic numbers or of near-miss claims. It was only ever visible on atomic numbers, and atomic numbers were the only relation pinned at distance 1.
- **A4** is E9's question asked properly. Strength and distance move together within one entity, so a strong negative rho means the model is tracking how confidently it holds the discrimination, not what kind of fact it is.
- Margins are teacher-forced and unaffected by answer formatting; the rates classify the answer with any reasoning preamble stripped, as E8 does and E6/E7 do not.
