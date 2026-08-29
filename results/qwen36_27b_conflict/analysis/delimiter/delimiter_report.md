# E12: what the wrapper is doing — Qwen/Qwen3.6-27B

The paragraph, claim sentence, question and response constraint are byte-identical in every row. Only the block that encloses the paragraph changes. `delta vs inline` is paired within fact and cluster-bootstrapped over facts.


| Relation | Wrapper | What it rules out | Cell | n | Context | Margin | Δ vs inline | 95% CI |
|---|---|---|---|---:|---:|---:|---:|---:|
| element_symbol | `inline` | baseline | `assert_r1` | 118 | 0.0% | -7.19 | +0.00 | [+0.00, +0.00] |
| element_symbol | `inline` | baseline | `bare` | 118 | 38.1% | -0.43 | +0.00 | [+0.00, +0.00] |
| element_symbol | `blankline` | layout only | `assert_r1` | 118 | 0.0% | -7.14 | +0.05 | [-0.05, +0.15] |
| element_symbol | `blankline` | layout only | `bare` | 118 | 37.3% | -0.43 | -0.00 | [-0.03, +0.03] |
| element_symbol | `dashes` | layout + fence | `assert_r1` | 118 | 0.8% | -3.86 | +3.33 | [+3.09, +3.57] |
| element_symbol | `dashes` | layout + fence | `bare` | 118 | 80.5% | 0.55 | +0.98 | [+0.87, +1.10] |
| element_symbol | `quotes` | layout + fence | `assert_r1` | 118 | 1.7% | -3.81 | +3.38 | [+3.11, +3.65] |
| element_symbol | `quotes` | layout + fence | `bare` | 118 | 80.5% | 0.69 | +1.12 | [+0.98, +1.25] |
| element_symbol | `tag_document` | E11's condition | `assert_r1` | 118 | 63.6% | 0.56 | +7.75 | [+7.45, +8.06] |
| element_symbol | `tag_document` | E11's condition | `bare` | 118 | 100.0% | 2.91 | +3.34 | [+3.13, +3.56] |
| element_symbol | `tag_passage` | same syntax, different word | `assert_r1` | 118 | 54.2% | 0.28 | +7.47 | [+7.16, +7.77] |
| element_symbol | `tag_passage` | same syntax, different word | `bare` | 118 | 97.5% | 2.26 | +2.69 | [+2.49, +2.89] |
| element_symbol | `tag_empty` | bracket syntax, no name at all | `assert_r1` | 118 | 0.0% | -5.04 | +2.15 | [+1.95, +2.36] |
| element_symbol | `tag_empty` | bracket syntax, no name at all | `bare` | 118 | 34.7% | -0.18 | +0.25 | [+0.13, +0.37] |
| element_symbol | `tag_untrusted` | same syntax, opposite valence | `assert_r1` | 118 | 0.0% | -7.94 | -0.75 | [-0.95, -0.55] |
| element_symbol | `tag_untrusted` | same syntax, opposite valence | `bare` | 118 | 3.4% | -1.70 | -1.27 | [-1.41, -1.15] |
| element_symbol | `tag_unreliable` | opposite valence, different words | `assert_r1` | 118 | 0.0% | -8.18 | -0.99 | [-1.24, -0.75] |
| element_symbol | `tag_unreliable` | opposite valence, different words | `bare` | 118 | 0.0% | -3.05 | -2.62 | [-2.82, -2.43] |
| element_symbol | `tag_trusted` | same syntax, positive valence | `assert_r1` | 118 | 1.7% | -2.98 | +4.21 | [+3.93, +4.48] |
| element_symbol | `tag_trusted` | same syntax, positive valence | `bare` | 118 | 48.3% | -0.11 | +0.32 | [+0.19, +0.45] |
| element_symbol | `tag_nonsense` | same syntax, no meaning at all | `assert_r1` | 118 | 3.4% | -2.49 | +4.70 | [+4.44, +4.97] |
| element_symbol | `tag_nonsense` | same syntax, no meaning at all | `bare` | 118 | 65.3% | 0.37 | +0.80 | [+0.67, +0.94] |
| element_symbol | `label_document` | same word, no markup | `assert_r1` | 118 | 15.3% | -2.06 | +5.13 | [+4.84, +5.41] |
| element_symbol | `label_document` | same word, no markup | `bare` | 118 | 95.8% | 2.03 | +2.46 | [+2.25, +2.68] |
| element_symbol | `label_search` | the RAG framing | `assert_r1` | 118 | 2.5% | -3.18 | +4.01 | [+3.77, +4.25] |
| element_symbol | `label_search` | the RAG framing | `bare` | 118 | 75.4% | 0.68 | +1.11 | [+0.94, +1.28] |
| country_capital | `inline` | baseline | `assert_r1` | 146 | 0.0% | -11.07 | +0.00 | [+0.00, +0.00] |
| country_capital | `inline` | baseline | `bare` | 146 | 2.7% | -4.29 | +0.00 | [+0.00, +0.00] |
| country_capital | `blankline` | layout only | `assert_r1` | 146 | 0.0% | -10.41 | +0.66 | [+0.53, +0.79] |
| country_capital | `blankline` | layout only | `bare` | 146 | 4.1% | -4.10 | +0.19 | [+0.14, +0.25] |
| country_capital | `dashes` | layout + fence | `assert_r1` | 146 | 2.1% | -7.09 | +3.98 | [+3.65, +4.28] |
| country_capital | `dashes` | layout + fence | `bare` | 146 | 24.0% | -0.67 | +3.63 | [+3.40, +3.86] |
| country_capital | `quotes` | layout + fence | `assert_r1` | 146 | 2.1% | -5.87 | +5.20 | [+4.85, +5.54] |
| country_capital | `quotes` | layout + fence | `bare` | 146 | 27.4% | -0.67 | +3.62 | [+3.40, +3.84] |
| country_capital | `tag_document` | E11's condition | `assert_r1` | 146 | 41.1% | 0.00 | +11.07 | [+10.62, +11.49] |
| country_capital | `tag_document` | E11's condition | `bare` | 146 | 96.6% | 2.70 | +6.99 | [+6.62, +7.38] |
| country_capital | `tag_passage` | same syntax, different word | `assert_r1` | 146 | 30.1% | -0.56 | +10.50 | [+10.06, +10.95] |
| country_capital | `tag_passage` | same syntax, different word | `bare` | 146 | 100.0% | 4.95 | +9.24 | [+8.82, +9.69] |
| country_capital | `tag_empty` | bracket syntax, no name at all | `assert_r1` | 146 | 2.1% | -7.10 | +3.96 | [+3.62, +4.28] |
| country_capital | `tag_empty` | bracket syntax, no name at all | `bare` | 146 | 7.5% | -1.97 | +2.32 | [+2.11, +2.54] |
| country_capital | `tag_untrusted` | same syntax, opposite valence | `assert_r1` | 146 | 0.0% | -13.01 | -1.95 | [-2.31, -1.57] |
| country_capital | `tag_untrusted` | same syntax, opposite valence | `bare` | 146 | 2.7% | -4.48 | -0.19 | [-0.40, +0.01] |
| country_capital | `tag_unreliable` | opposite valence, different words | `assert_r1` | 146 | 0.0% | -13.38 | -2.31 | [-2.70, -1.94] |
| country_capital | `tag_unreliable` | opposite valence, different words | `bare` | 146 | 0.0% | -10.74 | -6.45 | [-6.83, -6.07] |
| country_capital | `tag_trusted` | same syntax, positive valence | `assert_r1` | 146 | 4.8% | -4.91 | +6.15 | [+5.77, +6.53] |
| country_capital | `tag_trusted` | same syntax, positive valence | `bare` | 146 | 43.8% | -0.14 | +4.15 | [+3.90, +4.39] |
| country_capital | `tag_nonsense` | same syntax, no meaning at all | `assert_r1` | 146 | 4.1% | -7.10 | +3.97 | [+3.61, +4.33] |
| country_capital | `tag_nonsense` | same syntax, no meaning at all | `bare` | 146 | 23.3% | -0.88 | +3.41 | [+3.20, +3.63] |
| country_capital | `label_document` | same word, no markup | `assert_r1` | 146 | 6.2% | -4.86 | +6.21 | [+5.84, +6.58] |
| country_capital | `label_document` | same word, no markup | `bare` | 146 | 82.9% | 1.38 | +5.67 | [+5.31, +6.04] |
| country_capital | `label_search` | the RAG framing | `assert_r1` | 146 | 2.7% | -5.70 | +5.37 | [+5.01, +5.73] |
| country_capital | `label_search` | the RAG framing | `bare` | 146 | 50.0% | 0.18 | +4.48 | [+4.22, +4.73] |

## How to read this

- **`blankline` is the layout control.** If it moves the margin as much as `tag_document`, E11's effect was whitespace and the document framing is a red herring. If it does not, the markup is doing real work.
- **`tag_passage` versus `tag_document`** separates the syntax from the word. **`label_document`** separates the word from the syntax.
- **`tag_untrusted` is the one to report.** It is the tag whose entire purpose is to mark text as not-to-be-trusted. If deference under it matches `tag_document`, the wrapper is read as *this is source material* and its stated valence is ignored. If it does NOT -- if the tag suppresses deference -- then the model is reading the label's meaning, and the question becomes why the same words fail when they are put in the system prompt instead.
- **`tag_nonsense` is the control for that reading.** `<qzx_block>` carries the same syntax and no meaning. If it behaves like `<document>`, an unfamiliar tag is not inherently suppressive and a low score for `<untrusted_content>` really is about the word. If it behaves like `<untrusted_content>`, then any out-of-distribution tag suppresses deference and the semantic reading is wrong. `tag_trusted` and `tag_unreliable` place the same contrast on a scale.
- **`tag_empty` splits the structure term itself.** `<qzx_block>` still has a name; `<>` has only the brackets. If `<>` matches `<qzx_block>`, the name contributes nothing and the structural effect is the bracket syntax. If `<>` falls back toward `dashes`, then a tag needs to NAME something -- anything -- and `<qzx_block>`'s +31 was already partly semantic.
- **`bare` versus `assert_r1`** asks whether the wrapper confers source authority or changes the task. `bare` has no source to trust, so if it swings too, the model is switching into reading-comprehension mode rather than deciding whom to believe.
- Margins are teacher-forced. Rates classify the answer with any reasoning preamble stripped.
