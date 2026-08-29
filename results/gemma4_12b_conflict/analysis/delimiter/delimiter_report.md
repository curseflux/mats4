# E12: what the wrapper is doing — google/gemma-4-12B-it

The paragraph, claim sentence, question and response constraint are byte-identical in every row. Only the block that encloses the paragraph changes. `delta vs inline` is paired within fact and cluster-bootstrapped over facts.


| Relation | Wrapper | What it rules out | Cell | n | Context | Margin | Δ vs inline | 95% CI |
|---|---|---|---|---:|---:|---:|---:|---:|
| element_symbol | `inline` | baseline | `assert_r1` | 118 | 0.0% | -27.08 | +0.00 | [+0.00, +0.00] |
| element_symbol | `inline` | baseline | `bare` | 118 | 9.3% | -15.21 | +0.00 | [+0.00, +0.00] |
| element_symbol | `blankline` | layout only | `assert_r1` | 118 | 0.0% | -25.82 | +1.26 | [+0.90, +1.63] |
| element_symbol | `blankline` | layout only | `bare` | 118 | 8.5% | -14.04 | +1.17 | [+0.63, +1.78] |
| element_symbol | `dashes` | layout + fence | `assert_r1` | 118 | 23.7% | -9.28 | +17.80 | [+16.27, +19.35] |
| element_symbol | `dashes` | layout + fence | `bare` | 118 | 79.7% | 4.16 | +19.36 | [+17.81, +20.87] |
| element_symbol | `quotes` | layout + fence | `assert_r1` | 118 | 5.9% | -18.51 | +8.57 | [+7.35, +9.90] |
| element_symbol | `quotes` | layout + fence | `bare` | 118 | 88.1% | 4.74 | +19.95 | [+18.35, +21.57] |
| element_symbol | `tag_document` | E11's condition | `assert_r1` | 118 | 100.0% | 13.90 | +40.98 | [+39.61, +42.39] |
| element_symbol | `tag_document` | E11's condition | `bare` | 118 | 98.3% | 14.33 | +29.53 | [+27.79, +31.13] |
| element_symbol | `tag_passage` | same syntax, different word | `assert_r1` | 118 | 100.0% | 13.19 | +40.27 | [+38.95, +41.59] |
| element_symbol | `tag_passage` | same syntax, different word | `bare` | 118 | 98.3% | 14.16 | +29.37 | [+27.67, +30.94] |
| element_symbol | `tag_empty` | bracket syntax, no name at all | `assert_r1` | 118 | 25.4% | -12.51 | +14.57 | [+12.77, +16.32] |
| element_symbol | `tag_empty` | bracket syntax, no name at all | `bare` | 118 | 93.2% | 6.98 | +22.19 | [+20.74, +23.53] |
| element_symbol | `tag_untrusted` | same syntax, opposite valence | `assert_r1` | 118 | 0.0% | -24.32 | +2.76 | [+1.90, +3.66] |
| element_symbol | `tag_untrusted` | same syntax, opposite valence | `bare` | 118 | 31.4% | -6.98 | +8.23 | [+6.41, +10.23] |
| element_symbol | `tag_unreliable` | opposite valence, different words | `assert_r1` | 118 | 28.8% | -5.98 | +21.10 | [+19.70, +22.56] |
| element_symbol | `tag_unreliable` | opposite valence, different words | `bare` | 118 | 56.8% | -0.93 | +14.28 | [+12.58, +15.99] |
| element_symbol | `tag_trusted` | same syntax, positive valence | `assert_r1` | 118 | 100.0% | 16.36 | +43.44 | [+42.06, +44.88] |
| element_symbol | `tag_trusted` | same syntax, positive valence | `bare` | 118 | 99.2% | 17.19 | +32.40 | [+30.57, +34.07] |
| element_symbol | `tag_nonsense` | same syntax, no meaning at all | `assert_r1` | 118 | 78.8% | 4.11 | +31.19 | [+29.75, +32.64] |
| element_symbol | `tag_nonsense` | same syntax, no meaning at all | `bare` | 118 | 95.8% | 9.28 | +24.48 | [+22.94, +25.93] |
| element_symbol | `label_document` | same word, no markup | `assert_r1` | 118 | 98.3% | 11.46 | +38.54 | [+37.13, +39.94] |
| element_symbol | `label_document` | same word, no markup | `bare` | 118 | 93.2% | 9.09 | +24.30 | [+22.73, +25.75] |
| element_symbol | `label_search` | the RAG framing | `assert_r1` | 118 | 100.0% | 12.99 | +40.07 | [+38.69, +41.43] |
| element_symbol | `label_search` | the RAG framing | `bare` | 118 | 95.8% | 9.30 | +24.51 | [+22.85, +26.11] |
| country_capital | `inline` | baseline | `assert_r1` | 143 | 0.0% | -28.05 | +0.00 | [+0.00, +0.00] |
| country_capital | `inline` | baseline | `bare` | 143 | 23.1% | -9.39 | +0.00 | [+0.00, +0.00] |
| country_capital | `blankline` | layout only | `assert_r1` | 143 | 0.0% | -24.17 | +3.89 | [+3.49, +4.30] |
| country_capital | `blankline` | layout only | `bare` | 143 | 28.7% | -4.56 | +4.83 | [+4.24, +5.46] |
| country_capital | `dashes` | layout + fence | `assert_r1` | 143 | 33.6% | -4.80 | +23.26 | [+21.91, +24.55] |
| country_capital | `dashes` | layout + fence | `bare` | 143 | 67.1% | 4.83 | +14.22 | [+13.05, +15.42] |
| country_capital | `quotes` | layout + fence | `assert_r1` | 143 | 53.8% | -1.64 | +26.41 | [+25.11, +27.70] |
| country_capital | `quotes` | layout + fence | `bare` | 143 | 52.4% | 8.52 | +17.91 | [+16.61, +19.22] |
| country_capital | `tag_document` | E11's condition | `assert_r1` | 143 | 100.0% | 12.61 | +40.67 | [+39.56, +41.78] |
| country_capital | `tag_document` | E11's condition | `bare` | 143 | 100.0% | 16.49 | +25.88 | [+24.46, +27.35] |
| country_capital | `tag_passage` | same syntax, different word | `assert_r1` | 143 | 100.0% | 10.66 | +38.71 | [+37.59, +39.81] |
| country_capital | `tag_passage` | same syntax, different word | `bare` | 143 | 100.0% | 16.22 | +25.61 | [+24.14, +27.14] |
| country_capital | `tag_empty` | bracket syntax, no name at all | `assert_r1` | 143 | 62.9% | 0.76 | +28.81 | [+27.32, +30.24] |
| country_capital | `tag_empty` | bracket syntax, no name at all | `bare` | 143 | 69.9% | 8.24 | +17.63 | [+16.34, +18.91] |
| country_capital | `tag_untrusted` | same syntax, opposite valence | `assert_r1` | 143 | 0.0% | -27.33 | +0.72 | [+0.25, +1.18] |
| country_capital | `tag_untrusted` | same syntax, opposite valence | `bare` | 143 | 3.5% | -17.63 | -8.24 | [-9.94, -6.55] |
| country_capital | `tag_unreliable` | opposite valence, different words | `assert_r1` | 143 | 0.7% | -21.73 | +6.32 | [+5.66, +7.00] |
| country_capital | `tag_unreliable` | opposite valence, different words | `bare` | 143 | 2.1% | -15.50 | -6.11 | [-8.01, -4.31] |
| country_capital | `tag_trusted` | same syntax, positive valence | `assert_r1` | 143 | 100.0% | 17.01 | +45.06 | [+43.96, +46.24] |
| country_capital | `tag_trusted` | same syntax, positive valence | `bare` | 143 | 100.0% | 18.67 | +28.06 | [+26.56, +29.62] |
| country_capital | `tag_nonsense` | same syntax, no meaning at all | `assert_r1` | 143 | 74.8% | 2.88 | +30.94 | [+29.62, +32.25] |
| country_capital | `tag_nonsense` | same syntax, no meaning at all | `bare` | 143 | 78.3% | 3.96 | +13.35 | [+12.07, +14.68] |
| country_capital | `label_document` | same word, no markup | `assert_r1` | 143 | 99.3% | 10.30 | +38.35 | [+37.24, +39.47] |
| country_capital | `label_document` | same word, no markup | `bare` | 143 | 90.9% | 17.96 | +27.35 | [+25.85, +28.88] |
| country_capital | `label_search` | the RAG framing | `assert_r1` | 143 | 100.0% | 13.38 | +41.44 | [+40.33, +42.56] |
| country_capital | `label_search` | the RAG framing | `bare` | 143 | 93.0% | 14.81 | +24.20 | [+22.77, +25.63] |

## How to read this

- **`blankline` is the layout control.** If it moves the margin as much as `tag_document`, E11's effect was whitespace and the document framing is a red herring. If it does not, the markup is doing real work.
- **`tag_passage` versus `tag_document`** separates the syntax from the word. **`label_document`** separates the word from the syntax.
- **`tag_untrusted` is the one to report.** It is the tag whose entire purpose is to mark text as not-to-be-trusted. If deference under it matches `tag_document`, the wrapper is read as *this is source material* and its stated valence is ignored. If it does NOT -- if the tag suppresses deference -- then the model is reading the label's meaning, and the question becomes why the same words fail when they are put in the system prompt instead.
- **`tag_nonsense` is the control for that reading.** `<qzx_block>` carries the same syntax and no meaning. If it behaves like `<document>`, an unfamiliar tag is not inherently suppressive and a low score for `<untrusted_content>` really is about the word. If it behaves like `<untrusted_content>`, then any out-of-distribution tag suppresses deference and the semantic reading is wrong. `tag_trusted` and `tag_unreliable` place the same contrast on a scale.
- **`tag_empty` splits the structure term itself.** `<qzx_block>` still has a name; `<>` has only the brackets. If `<>` matches `<qzx_block>`, the name contributes nothing and the structural effect is the bracket syntax. If `<>` falls back toward `dashes`, then a tag needs to NAME something -- anything -- and `<qzx_block>`'s +31 was already partly semantic.
- **`bare` versus `assert_r1`** asks whether the wrapper confers source authority or changes the task. `bare` has no source to trust, so if it swings too, the model is switching into reading-comprehension mode rather than deciding whom to believe.
- Margins are teacher-forced. Rates classify the answer with any reasoning preamble stripped.
