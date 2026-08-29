# E10: plausibility of the false answer — google/gemma-4-12B-it

Entity held fixed; only how far the false answer sits from the true one varies. For `element_atomic_number` that distance is a number line (d=1, d=2, d=5, d=20, plus a random derangement); elsewhere it is `near` (the adjacent row's answer) versus `random`.


## Act effect at each distance (the decisive test)

| Relation | Distance | Act effect (stipulate − assert) | 95% CI | n |
|---|---|---:|---:|---:|
| element_atomic_number | `d1` | -10.77 | [-12.05, -9.46] | 115 |
| element_atomic_number | `d2` | -14.60 | [-15.87, -13.24] | 115 |
| element_atomic_number | `d5` | -9.62 | [-11.17, -8.08] | 115 |
| element_atomic_number | `d20` | -11.23 | [-13.67, -8.83] | 115 |
| element_atomic_number | `random` | -4.24 | [-6.00, -2.58] | 115 |
| element_symbol | `near` | 10.89 | [+9.61, +12.23] | 118 |
| element_symbol | `random` | 12.15 | [+10.70, +13.64] | 118 |
| country_capital | `near` | 4.48 | [+2.84, +6.35] | 143 |
| country_capital | `random` | 2.10 | [+0.93, +3.38] | 143 |

## Deference by distance (neutral policy)

| Relation | Cell | Distance | n | Context | Mean margin | Mean strength |
|---|---|---|---:|---:|---:|---:|
| element_atomic_number | `stipulate_r1` | `d1` | 115 | 4.3% | -7.75 | 15.60 |
| element_atomic_number | `stipulate_r1` | `d2` | 115 | 4.3% | -7.39 | 16.22 |
| element_atomic_number | `stipulate_r1` | `d5` | 115 | 9.6% | -8.45 | 19.72 |
| element_atomic_number | `stipulate_r1` | `d20` | 115 | 20.0% | -6.13 | 21.36 |
| element_atomic_number | `stipulate_r1` | `random` | 115 | 13.9% | -6.43 | 21.98 |
| element_atomic_number | `stipulate_r2` | `d1` | 115 | 9.6% | -7.48 | 15.60 |
| element_atomic_number | `stipulate_r2` | `d2` | 115 | 4.3% | -7.52 | 16.22 |
| element_atomic_number | `stipulate_r2` | `d5` | 115 | 7.0% | -9.30 | 19.72 |
| element_atomic_number | `stipulate_r2` | `d20` | 115 | 10.4% | -8.38 | 21.36 |
| element_atomic_number | `stipulate_r2` | `random` | 115 | 7.0% | -9.14 | 21.98 |
| element_atomic_number | `assert_r1` | `d1` | 115 | 69.6% | 4.46 | 15.60 |
| element_atomic_number | `assert_r1` | `d2` | 115 | 83.5% | 8.06 | 16.22 |
| element_atomic_number | `assert_r1` | `d5` | 115 | 52.2% | 2.47 | 19.72 |
| element_atomic_number | `assert_r1` | `d20` | 115 | 55.7% | 5.39 | 21.36 |
| element_atomic_number | `assert_r1` | `random` | 115 | 24.3% | -1.50 | 21.98 |
| element_atomic_number | `assert_r2` | `d1` | 115 | 53.9% | 1.85 | 15.60 |
| element_atomic_number | `assert_r2` | `d2` | 115 | 73.9% | 6.22 | 16.22 |
| element_atomic_number | `assert_r2` | `d5` | 115 | 35.7% | -0.98 | 19.72 |
| element_atomic_number | `assert_r2` | `d20` | 115 | 48.7% | 2.56 | 21.36 |
| element_atomic_number | `assert_r2` | `random` | 115 | 17.4% | -5.59 | 21.98 |
| element_atomic_number | `bare` | `d1` | 115 | 72.2% | 5.73 | 15.60 |
| element_atomic_number | `bare` | `d2` | 115 | 87.8% | 9.39 | 16.22 |
| element_atomic_number | `bare` | `d5` | 115 | 62.6% | 4.54 | 19.72 |
| element_atomic_number | `bare` | `d20` | 115 | 63.5% | 6.90 | 21.36 |
| element_atomic_number | `bare` | `random` | 115 | 33.0% | 0.25 | 21.98 |
| element_atomic_number | `explicit_stipulation` | `d1` | 115 | 100.0% | 15.20 | 15.60 |
| element_atomic_number | `explicit_stipulation` | `d2` | 115 | 100.0% | 15.73 | 16.22 |
| element_atomic_number | `explicit_stipulation` | `d5` | 115 | 100.0% | 15.76 | 19.72 |
| element_atomic_number | `explicit_stipulation` | `d20` | 115 | 100.0% | 16.03 | 21.36 |
| element_atomic_number | `explicit_stipulation` | `random` | 115 | 100.0% | 16.39 | 21.98 |
| element_symbol | `stipulate_r1` | `near` | 118 | 26.3% | -5.68 | 29.61 |
| element_symbol | `stipulate_r1` | `random` | 118 | 21.2% | -10.78 | 34.72 |
| element_symbol | `stipulate_r2` | `near` | 118 | 15.3% | -9.68 | 29.61 |
| element_symbol | `stipulate_r2` | `random` | 118 | 10.2% | -16.16 | 34.72 |
| element_symbol | `assert_r1` | `near` | 118 | 4.2% | -17.85 | 29.61 |
| element_symbol | `assert_r1` | `random` | 118 | 1.7% | -26.21 | 34.72 |
| element_symbol | `assert_r2` | `near` | 118 | 8.5% | -19.29 | 29.61 |
| element_symbol | `assert_r2` | `random` | 118 | 5.9% | -25.02 | 34.72 |
| element_symbol | `bare` | `near` | 118 | 9.3% | -11.69 | 29.61 |
| element_symbol | `bare` | `random` | 118 | 11.9% | -14.24 | 34.72 |
| element_symbol | `explicit_stipulation` | `near` | 118 | 100.0% | 17.90 | 29.61 |
| element_symbol | `explicit_stipulation` | `random` | 118 | 99.2% | 18.10 | 34.72 |
| country_capital | `stipulate_r1` | `near` | 143 | 13.3% | -17.66 | 29.98 |
| country_capital | `stipulate_r1` | `random` | 143 | 2.8% | -26.65 | 39.82 |
| country_capital | `stipulate_r2` | `near` | 143 | 11.2% | -19.80 | 29.98 |
| country_capital | `stipulate_r2` | `random` | 143 | 1.4% | -26.89 | 39.82 |
| country_capital | `assert_r1` | `near` | 143 | 4.2% | -22.23 | 29.98 |
| country_capital | `assert_r1` | `random` | 143 | 0.0% | -27.57 | 39.82 |
| country_capital | `assert_r2` | `near` | 143 | 4.2% | -24.19 | 29.98 |
| country_capital | `assert_r2` | `random` | 143 | 0.0% | -30.17 | 39.82 |
| country_capital | `bare` | `near` | 143 | 15.4% | -12.50 | 29.98 |
| country_capital | `bare` | `random` | 143 | 28.0% | -8.29 | 39.82 |
| country_capital | `explicit_stipulation` | `near` | 143 | 100.0% | 25.32 | 29.98 |
| country_capital | `explicit_stipulation` | `random` | 143 | 100.0% | 27.14 | 39.82 |

## Leakage under `ignore the paragraph`

| Relation | Distance | Cell | Leak rate | n |
|---|---|---|---:|---:|
| element_atomic_number | `d1` | `bare` | 61.7% | 115 |
| element_atomic_number | `d1` | `assert_r1` | 20.0% | 115 |
| element_atomic_number | `d1` | `explicit_stipulation` | 0.0% | 115 |
| element_atomic_number | `d2` | `bare` | 77.4% | 115 |
| element_atomic_number | `d2` | `assert_r1` | 35.7% | 115 |
| element_atomic_number | `d2` | `explicit_stipulation` | 0.0% | 115 |
| element_atomic_number | `d5` | `bare` | 45.2% | 115 |
| element_atomic_number | `d5` | `assert_r1` | 9.6% | 115 |
| element_atomic_number | `d5` | `explicit_stipulation` | 0.0% | 115 |
| element_atomic_number | `d20` | `bare` | 46.1% | 115 |
| element_atomic_number | `d20` | `assert_r1` | 12.2% | 115 |
| element_atomic_number | `d20` | `explicit_stipulation` | 0.0% | 115 |
| element_atomic_number | `random` | `bare` | 16.5% | 115 |
| element_atomic_number | `random` | `assert_r1` | 0.9% | 115 |
| element_atomic_number | `random` | `explicit_stipulation` | 0.0% | 115 |
| element_symbol | `near` | `bare` | 4.2% | 118 |
| element_symbol | `near` | `assert_r1` | 2.5% | 118 |
| element_symbol | `near` | `explicit_stipulation` | 1.7% | 118 |
| element_symbol | `random` | `bare` | 0.8% | 118 |
| element_symbol | `random` | `assert_r1` | 0.8% | 118 |
| element_symbol | `random` | `explicit_stipulation` | 0.0% | 118 |
| country_capital | `near` | `bare` | 2.8% | 143 |
| country_capital | `near` | `assert_r1` | 2.1% | 143 |
| country_capital | `near` | `explicit_stipulation` | 0.7% | 143 |
| country_capital | `random` | `bare` | 0.0% | 143 |
| country_capital | `random` | `assert_r1` | 0.0% | 143 |
| country_capital | `random` | `explicit_stipulation` | 0.0% | 143 |

## Strength as a mediator, entity fixed

| Relation | Cell | rho(strength, margin) | n |
|---|---|---:|---:|
| element_atomic_number | `bare` | -0.185 | 575 |
| element_atomic_number | `assert_r1` | -0.215 | 575 |
| element_symbol | `bare` | -0.397 | 236 |
| element_symbol | `assert_r1` | -0.749 | 236 |
| country_capital | `bare` | +0.068 | 286 |
| country_capital | `assert_r1` | -0.555 | 286 |

## How to read this

- **A2 is the one that matters.** E8's act effect on atomic numbers was −10.83, measured where every false answer was true+1. If the effect keeps that sign and size at `d20` and `random`, the falsification of the stipulability account stands and is now confound-free. If it collapses toward zero as distance grows, the falsification was an artefact of near-miss claims and section 5 has to be rewritten.
- **A1 tells you how big the confound was.** Compare `near`/`d1` against `random` within `element_symbol` and `country_capital`: that gap is exactly the difference between the Gemma and Qwen E8 runs, which used different modes.
- **A3** asks whether the bare > assert > explicit leakage gradient is a property of atomic numbers or of near-miss claims. It was only ever visible on atomic numbers, and atomic numbers were the only relation pinned at distance 1.
- **A4** is E9's question asked properly. Strength and distance move together within one entity, so a strong negative rho means the model is tracking how confidently it holds the discrimination, not what kind of fact it is.
- Margins are teacher-forced and unaffected by answer formatting; the rates classify the answer with any reasoning preamble stripped, as E8 does and E6/E7 do not.
