# E11: does the channel matter? — google/gemma-4-12B-it

The claim sentence, paragraph, question and user instruction are byte-identical across channels. Only who appears to be speaking changes.


| Relation | Cell | Policy | Channel | Context-following | Mean margin | n |
|---|---|---|---|---:|---:|---:|
| element_symbol | `assert_r1` | neutral | `inline` | 0.0% | -27.00 | 118 |
| element_symbol | `assert_r1` | neutral | `delimited` | 100.0% | 13.86 | 118 |
| element_symbol | `assert_r1` | neutral | `system_guard` | 100.0% | 13.66 | 118 |
| element_symbol | `assert_r1` | neutral | `user_guard` | 100.0% | 10.80 | 118 |
| element_symbol | `assert_r1` | neutral | `user_guard_first_person` | 97.5% | 19.36 | 118 |
| element_symbol | `assert_r1` | neutral | `retrieved_turn` | 57.6% | 0.30 | 118 |
| element_symbol | `assert_r1` | parametric | `inline` | 0.0% | -35.35 | 118 |
| element_symbol | `assert_r1` | parametric | `delimited` | 0.0% | -34.97 | 118 |
| element_symbol | `assert_r1` | parametric | `system_guard` | 0.0% | -35.30 | 118 |
| element_symbol | `assert_r1` | parametric | `user_guard` | 0.0% | -34.77 | 118 |
| element_symbol | `assert_r1` | parametric | `user_guard_first_person` | 0.0% | -34.99 | 118 |
| element_symbol | `assert_r1` | parametric | `retrieved_turn` | 0.0% | -34.49 | 118 |
| element_symbol | `explicit_stipulation` | neutral | `inline` | 99.2% | 18.13 | 118 |
| element_symbol | `explicit_stipulation` | neutral | `delimited` | 100.0% | 21.88 | 118 |
| element_symbol | `explicit_stipulation` | neutral | `system_guard` | 100.0% | 21.93 | 118 |
| element_symbol | `explicit_stipulation` | neutral | `user_guard` | 100.0% | 21.75 | 118 |
| element_symbol | `explicit_stipulation` | neutral | `user_guard_first_person` | 78.0% | 23.91 | 118 |
| element_symbol | `explicit_stipulation` | neutral | `retrieved_turn` | 74.6% | 11.13 | 118 |
| element_symbol | `explicit_stipulation` | parametric | `inline` | 0.8% | -27.60 | 118 |
| element_symbol | `explicit_stipulation` | parametric | `delimited` | 2.5% | -23.22 | 118 |
| element_symbol | `explicit_stipulation` | parametric | `system_guard` | 1.7% | -28.47 | 118 |
| element_symbol | `explicit_stipulation` | parametric | `user_guard` | 1.7% | -25.81 | 118 |
| element_symbol | `explicit_stipulation` | parametric | `user_guard_first_person` | 1.7% | -29.19 | 118 |
| element_symbol | `explicit_stipulation` | parametric | `retrieved_turn` | 0.0% | -31.97 | 118 |
| country_capital | `assert_r1` | neutral | `inline` | 0.0% | -28.08 | 143 |
| country_capital | `assert_r1` | neutral | `delimited` | 100.0% | 12.65 | 143 |
| country_capital | `assert_r1` | neutral | `system_guard` | 100.0% | 13.93 | 143 |
| country_capital | `assert_r1` | neutral | `user_guard` | 100.0% | 17.35 | 143 |
| country_capital | `assert_r1` | neutral | `user_guard_first_person` | 98.6% | 24.13 | 143 |
| country_capital | `assert_r1` | neutral | `retrieved_turn` | 93.7% | 6.35 | 143 |
| country_capital | `assert_r1` | parametric | `inline` | 0.0% | -37.38 | 143 |
| country_capital | `assert_r1` | parametric | `delimited` | 0.0% | -37.36 | 143 |
| country_capital | `assert_r1` | parametric | `system_guard` | 0.0% | -37.94 | 143 |
| country_capital | `assert_r1` | parametric | `user_guard` | 0.0% | -37.38 | 143 |
| country_capital | `assert_r1` | parametric | `user_guard_first_person` | 0.0% | -37.76 | 143 |
| country_capital | `assert_r1` | parametric | `retrieved_turn` | 0.0% | -37.08 | 143 |
| country_capital | `explicit_stipulation` | neutral | `inline` | 100.0% | 27.04 | 143 |
| country_capital | `explicit_stipulation` | neutral | `delimited` | 100.0% | 27.39 | 143 |
| country_capital | `explicit_stipulation` | neutral | `system_guard` | 100.0% | 27.17 | 143 |
| country_capital | `explicit_stipulation` | neutral | `user_guard` | 100.0% | 26.80 | 143 |
| country_capital | `explicit_stipulation` | neutral | `user_guard_first_person` | 95.1% | 29.14 | 143 |
| country_capital | `explicit_stipulation` | neutral | `retrieved_turn` | 94.4% | 20.09 | 143 |
| country_capital | `explicit_stipulation` | parametric | `inline` | 0.0% | -36.63 | 143 |
| country_capital | `explicit_stipulation` | parametric | `delimited` | 0.0% | -37.43 | 143 |
| country_capital | `explicit_stipulation` | parametric | `system_guard` | 0.0% | -38.05 | 143 |
| country_capital | `explicit_stipulation` | parametric | `user_guard` | 0.0% | -36.60 | 143 |
| country_capital | `explicit_stipulation` | parametric | `user_guard_first_person` | 0.0% | -37.56 | 143 |
| country_capital | `explicit_stipulation` | parametric | `retrieved_turn` | 0.0% | -36.19 | 143 |

## How to read this

- **`inline` is the baseline** and should reproduce E8. If it does not, nothing else here is comparable.
- **The decisive comparison** is `explicit_stipulation` under `neutral` across channels. E8 measured 100% for that cell with no boundary at all. If it stays near 100% through `system_guard` and `retrieved_turn`, the model does not track who authored an imperative and a system-prompt guard does not fix it. If it falls, E8's hierarchy framing was an artefact of the single-turn prompt and should be retracted.
- **`assert_r1` is the control.** It carries the same false fact without an imperative, so a channel effect there is about source trust rather than instruction-following. Report the two together or neither.
- **`user_guard` versus `system_guard` is the clean channel test.** The guard sentences and the `<document>` wrapper are identical in both; only the turn they sit in changes. If `user_guard` suppresses deference and `system_guard` does not, provenance has to be stated in-band and the claim is about the channel. If neither suppresses, the channel is not the variable: a tag NAME is read and prose about the tag is not, wherever it sits -- which is a different claim and has to be written up as one. `user_guard_first_person` decides whether a `user_guard` null is really about the register of the borrowed system wording.
- Under `parametric` the user has told the model to ignore the paragraph. Any non-zero context-following there is the document winning against an explicit user instruction.
