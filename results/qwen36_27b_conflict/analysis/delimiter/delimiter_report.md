# E12: what the wrapper is doing — Qwen/Qwen3.6-27B

The paragraph, claim sentence, question and response constraint are byte-identical in every row. Only the block that encloses the paragraph changes. `delta vs inline` is paired within fact and cluster-bootstrapped over facts.


| Relation | Wrapper | What it rules out | Cell | n | Context | Margin | Δ vs inline | 95% CI |
|---|---|---|---|---:|---:|---:|---:|---:|
| element_symbol | `inline` | baseline | `assert_r1` | 118 | 0.0% | -7.21 | +0.00 | [+0.00, +0.00] |
| element_symbol | `inline` | baseline | `bare` | 118 | 35.6% | -0.43 | +0.00 | [+0.00, +0.00] |
| element_symbol | `blankline` | layout only | `assert_r1` | 118 | 0.0% | -7.14 | +0.07 | [-0.04, +0.17] |
| element_symbol | `blankline` | layout only | `bare` | 118 | 37.3% | -0.44 | -0.00 | [-0.04, +0.03] |
| element_symbol | `dashes` | layout + fence | `assert_r1` | 118 | 0.8% | -3.85 | +3.37 | [+3.13, +3.60] |
| element_symbol | `dashes` | layout + fence | `bare` | 118 | 80.5% | 0.56 | +0.99 | [+0.88, +1.11] |
| element_symbol | `quotes` | layout + fence | `assert_r1` | 118 | 1.7% | -3.82 | +3.39 | [+3.13, +3.66] |
| element_symbol | `quotes` | layout + fence | `bare` | 118 | 80.5% | 0.68 | +1.12 | [+0.98, +1.25] |
| element_symbol | `tag_document` | E11's condition | `assert_r1` | 118 | 61.9% | 0.55 | +7.76 | [+7.45, +8.07] |
| element_symbol | `tag_document` | E11's condition | `bare` | 118 | 100.0% | 2.90 | +3.34 | [+3.13, +3.55] |
| element_symbol | `tag_passage` | same syntax, different word | `assert_r1` | 118 | 55.9% | 0.28 | +7.49 | [+7.17, +7.81] |
| element_symbol | `tag_passage` | same syntax, different word | `bare` | 118 | 97.5% | 2.25 | +2.68 | [+2.48, +2.87] |
| element_symbol | `tag_empty` | bracket syntax, no name at all | `assert_r1` | 118 | 0.0% | -5.03 | +2.18 | [+1.97, +2.39] |
| element_symbol | `tag_empty` | bracket syntax, no name at all | `bare` | 118 | 34.7% | -0.18 | +0.25 | [+0.13, +0.36] |
| element_symbol | `tag_untrusted` | same syntax, opposite valence | `assert_r1` | 118 | 0.0% | -7.96 | -0.75 | [-0.95, -0.55] |
| element_symbol | `tag_untrusted` | same syntax, opposite valence | `bare` | 118 | 3.4% | -1.70 | -1.27 | [-1.40, -1.15] |
| element_symbol | `tag_unreliable` | opposite valence, different words | `assert_r1` | 118 | 0.0% | -8.18 | -0.97 | [-1.22, -0.72] |
| element_symbol | `tag_unreliable` | opposite valence, different words | `bare` | 118 | 0.0% | -3.05 | -2.62 | [-2.82, -2.43] |
| element_symbol | `tag_trusted` | same syntax, positive valence | `assert_r1` | 118 | 1.7% | -2.98 | +4.23 | [+3.95, +4.50] |
| element_symbol | `tag_trusted` | same syntax, positive valence | `bare` | 118 | 46.6% | -0.10 | +0.33 | [+0.20, +0.45] |
| element_symbol | `tag_nonsense` | same syntax, no meaning at all | `assert_r1` | 118 | 3.4% | -2.50 | +4.72 | [+4.45, +4.99] |
| element_symbol | `tag_nonsense` | same syntax, no meaning at all | `bare` | 118 | 64.4% | 0.38 | +0.81 | [+0.67, +0.94] |
| element_symbol | `label_document` | same word, no markup | `assert_r1` | 118 | 15.3% | -2.05 | +5.16 | [+4.86, +5.45] |
| element_symbol | `label_document` | same word, no markup | `bare` | 118 | 95.8% | 2.02 | +2.45 | [+2.25, +2.67] |
| element_symbol | `label_search` | the RAG framing | `assert_r1` | 118 | 2.5% | -3.18 | +4.03 | [+3.79, +4.27] |
| element_symbol | `label_search` | the RAG framing | `bare` | 118 | 72.9% | 0.68 | +1.12 | [+0.95, +1.28] |
| element_symbol | `label_untrusted` | opposite valence, no markup | `assert_r1` | 118 | 0.0% | -7.76 | -0.54 | [-0.80, -0.30] |
| element_symbol | `label_untrusted` | opposite valence, no markup | `bare` | 118 | 9.3% | -1.48 | -1.05 | [-1.20, -0.90] |
| country_capital | `inline` | baseline | `assert_r1` | 146 | 0.0% | -11.07 | +0.00 | [+0.00, +0.00] |
| country_capital | `inline` | baseline | `bare` | 146 | 3.4% | -4.28 | +0.00 | [+0.00, +0.00] |
| country_capital | `blankline` | layout only | `assert_r1` | 146 | 0.0% | -10.38 | +0.69 | [+0.56, +0.82] |
| country_capital | `blankline` | layout only | `bare` | 146 | 4.1% | -4.11 | +0.17 | [+0.12, +0.23] |
| country_capital | `dashes` | layout + fence | `assert_r1` | 146 | 2.1% | -7.09 | +3.98 | [+3.65, +4.30] |
| country_capital | `dashes` | layout + fence | `bare` | 146 | 24.7% | -0.66 | +3.62 | [+3.40, +3.85] |
| country_capital | `quotes` | layout + fence | `assert_r1` | 146 | 2.1% | -5.87 | +5.20 | [+4.85, +5.54] |
| country_capital | `quotes` | layout + fence | `bare` | 146 | 26.7% | -0.66 | +3.62 | [+3.39, +3.84] |
| country_capital | `tag_document` | E11's condition | `assert_r1` | 146 | 42.5% | -0.00 | +11.07 | [+10.62, +11.49] |
| country_capital | `tag_document` | E11's condition | `bare` | 146 | 96.6% | 2.70 | +6.98 | [+6.61, +7.37] |
| country_capital | `tag_passage` | same syntax, different word | `assert_r1` | 146 | 30.8% | -0.56 | +10.51 | [+10.06, +10.96] |
| country_capital | `tag_passage` | same syntax, different word | `bare` | 146 | 100.0% | 4.97 | +9.25 | [+8.82, +9.70] |
| country_capital | `tag_empty` | bracket syntax, no name at all | `assert_r1` | 146 | 2.1% | -7.10 | +3.97 | [+3.63, +4.29] |
| country_capital | `tag_empty` | bracket syntax, no name at all | `bare` | 146 | 7.5% | -1.97 | +2.30 | [+2.10, +2.52] |
| country_capital | `tag_untrusted` | same syntax, opposite valence | `assert_r1` | 146 | 0.0% | -13.02 | -1.95 | [-2.32, -1.57] |
| country_capital | `tag_untrusted` | same syntax, opposite valence | `bare` | 146 | 2.7% | -4.48 | -0.20 | [-0.41, -0.00] |
| country_capital | `tag_unreliable` | opposite valence, different words | `assert_r1` | 146 | 0.0% | -13.38 | -2.31 | [-2.68, -1.94] |
| country_capital | `tag_unreliable` | opposite valence, different words | `bare` | 146 | 0.0% | -10.74 | -6.46 | [-6.83, -6.07] |
| country_capital | `tag_trusted` | same syntax, positive valence | `assert_r1` | 146 | 4.8% | -4.91 | +6.16 | [+5.76, +6.54] |
| country_capital | `tag_trusted` | same syntax, positive valence | `bare` | 146 | 43.8% | -0.13 | +4.15 | [+3.90, +4.40] |
| country_capital | `tag_nonsense` | same syntax, no meaning at all | `assert_r1` | 146 | 4.1% | -7.10 | +3.97 | [+3.60, +4.33] |
| country_capital | `tag_nonsense` | same syntax, no meaning at all | `bare` | 146 | 25.3% | -0.86 | +3.42 | [+3.20, +3.63] |
| country_capital | `label_document` | same word, no markup | `assert_r1` | 146 | 5.5% | -4.85 | +6.22 | [+5.85, +6.57] |
| country_capital | `label_document` | same word, no markup | `bare` | 146 | 82.2% | 1.37 | +5.65 | [+5.28, +6.00] |
| country_capital | `label_search` | the RAG framing | `assert_r1` | 146 | 3.4% | -5.72 | +5.35 | [+4.98, +5.70] |
| country_capital | `label_search` | the RAG framing | `bare` | 146 | 50.7% | 0.18 | +4.46 | [+4.20, +4.72] |
| country_capital | `label_untrusted` | opposite valence, no markup | `assert_r1` | 146 | 0.0% | -12.32 | -1.25 | [-1.58, -0.92] |
| country_capital | `label_untrusted` | opposite valence, no markup | `bare` | 146 | 2.1% | -3.60 | +0.68 | [+0.44, +0.93] |

## How to read this

- **`blankline` is the layout control.** If it moves the margin as much as `tag_document`, E11's effect was whitespace and the document framing is a red herring. If it does not, the markup is doing real work.
- **`tag_passage` versus `tag_document`** separates the syntax from the word. **`label_document`** separates the word from the syntax.
- **`tag_untrusted` is the one to report.** It is the tag whose entire purpose is to mark text as not-to-be-trusted. If deference under it matches `tag_document`, the wrapper is read as *this is source material* and its stated valence is ignored. If it does NOT -- if the tag suppresses deference -- then the model is reading the label's meaning, and the question becomes why the same words fail when they are put in the system prompt instead.
- **`tag_nonsense` is the control for that reading.** `<qzx_block>` carries the same syntax and no meaning. If it behaves like `<document>`, an unfamiliar tag is not inherently suppressive and a low score for `<untrusted_content>` really is about the word. If it behaves like `<untrusted_content>`, then any out-of-distribution tag suppresses deference and the semantic reading is wrong. `tag_trusted` and `tag_unreliable` place the same contrast on a scale.
- **`tag_empty` splits the structure term itself.** `<qzx_block>` still has a name; `<>` has only the brackets. If `<>` matches `<qzx_block>`, the name contributes nothing and the structural effect is the bracket syntax. If `<>` falls back toward `dashes`, then a tag needs to NAME something -- anything -- and `<qzx_block>`'s +31 was already partly semantic.
- **`bare` versus `assert_r1`** asks whether the wrapper confers source authority or changes the task. `bare` has no source to trust, so if it swings too, the model is switching into reading-comprehension mode rather than deciding whom to believe.
- Margins are teacher-forced. Rates classify the answer with any reasoning preamble stripped.
