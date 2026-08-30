# E12: what the wrapper is doing — google/gemma-4-12B-it

The paragraph, claim sentence, question and response constraint are byte-identical in every row. Only the block that encloses the paragraph changes. `delta vs inline` is paired within fact and cluster-bootstrapped over facts.


| Relation | Wrapper | What it rules out | Cell | n | Context | Margin | Δ vs inline | 95% CI |
|---|---|---|---|---:|---:|---:|---:|---:|
| element_symbol | `inline` | baseline | `assert_r1` | 118 | 0.0% | -27.10 | +0.00 | [+0.00, +0.00] |
| element_symbol | `inline` | baseline | `bare` | 118 | 8.5% | -15.56 | +0.00 | [+0.00, +0.00] |
| element_symbol | `blankline` | layout only | `assert_r1` | 118 | 0.0% | -25.91 | +1.19 | [+0.85, +1.54] |
| element_symbol | `blankline` | layout only | `bare` | 118 | 9.3% | -14.27 | +1.29 | [+0.72, +1.91] |
| element_symbol | `dashes` | layout + fence | `assert_r1` | 118 | 25.4% | -9.46 | +17.64 | [+16.09, +19.21] |
| element_symbol | `dashes` | layout + fence | `bare` | 118 | 79.7% | 4.16 | +19.72 | [+18.20, +21.26] |
| element_symbol | `quotes` | layout + fence | `assert_r1` | 118 | 5.9% | -18.56 | +8.54 | [+7.33, +9.87] |
| element_symbol | `quotes` | layout + fence | `bare` | 118 | 88.1% | 4.74 | +20.30 | [+18.71, +21.91] |
| element_symbol | `tag_document` | E11's condition | `assert_r1` | 118 | 100.0% | 13.87 | +40.96 | [+39.63, +42.36] |
| element_symbol | `tag_document` | E11's condition | `bare` | 118 | 98.3% | 14.33 | +29.89 | [+28.14, +31.55] |
| element_symbol | `tag_passage` | same syntax, different word | `assert_r1` | 118 | 100.0% | 13.20 | +40.30 | [+39.00, +41.60] |
| element_symbol | `tag_passage` | same syntax, different word | `bare` | 118 | 98.3% | 14.13 | +29.69 | [+27.96, +31.33] |
| element_symbol | `tag_empty` | bracket syntax, no name at all | `assert_r1` | 118 | 25.4% | -12.51 | +14.58 | [+12.82, +16.33] |
| element_symbol | `tag_empty` | bracket syntax, no name at all | `bare` | 118 | 92.4% | 6.98 | +22.55 | [+21.10, +23.91] |
| element_symbol | `tag_untrusted` | same syntax, opposite valence | `assert_r1` | 118 | 0.0% | -24.32 | +2.78 | [+1.89, +3.67] |
| element_symbol | `tag_untrusted` | same syntax, opposite valence | `bare` | 118 | 31.4% | -6.98 | +8.58 | [+6.73, +10.55] |
| element_symbol | `tag_unreliable` | opposite valence, different words | `assert_r1` | 118 | 28.8% | -5.98 | +21.12 | [+19.73, +22.59] |
| element_symbol | `tag_unreliable` | opposite valence, different words | `bare` | 118 | 56.8% | -0.93 | +14.63 | [+12.87, +16.38] |
| element_symbol | `tag_trusted` | same syntax, positive valence | `assert_r1` | 118 | 100.0% | 16.36 | +43.46 | [+42.10, +44.87] |
| element_symbol | `tag_trusted` | same syntax, positive valence | `bare` | 118 | 99.2% | 17.19 | +32.76 | [+30.89, +34.52] |
| element_symbol | `tag_nonsense` | same syntax, no meaning at all | `assert_r1` | 118 | 78.8% | 4.11 | +31.21 | [+29.77, +32.64] |
| element_symbol | `tag_nonsense` | same syntax, no meaning at all | `bare` | 118 | 95.8% | 9.28 | +24.84 | [+23.28, +26.29] |
| element_symbol | `label_document` | same word, no markup | `assert_r1` | 118 | 98.3% | 11.46 | +38.55 | [+37.15, +39.97] |
| element_symbol | `label_document` | same word, no markup | `bare` | 118 | 95.8% | 9.10 | +24.67 | [+23.05, +26.16] |
| element_symbol | `label_search` | the RAG framing | `assert_r1` | 118 | 100.0% | 12.91 | +40.01 | [+38.64, +41.38] |
| element_symbol | `label_search` | the RAG framing | `bare` | 118 | 95.8% | 9.32 | +24.88 | [+23.24, +26.48] |
| element_symbol | `label_untrusted` | opposite valence, no markup | `assert_r1` | 118 | 0.0% | -21.44 | +5.66 | [+4.76, +6.63] |
| element_symbol | `label_untrusted` | opposite valence, no markup | `bare` | 118 | 11.9% | -10.00 | +5.56 | [+4.06, +7.03] |
| country_capital | `inline` | baseline | `assert_r1` | 143 | 0.0% | -28.09 | +0.00 | [+0.00, +0.00] |
| country_capital | `inline` | baseline | `bare` | 143 | 25.2% | -9.41 | +0.00 | [+0.00, +0.00] |
| country_capital | `blankline` | layout only | `assert_r1` | 143 | 0.0% | -24.19 | +3.90 | [+3.50, +4.30] |
| country_capital | `blankline` | layout only | `bare` | 143 | 39.2% | -4.68 | +4.72 | [+4.12, +5.37] |
| country_capital | `dashes` | layout + fence | `assert_r1` | 143 | 32.9% | -4.86 | +23.23 | [+21.87, +24.54] |
| country_capital | `dashes` | layout + fence | `bare` | 143 | 45.5% | 4.85 | +14.26 | [+13.09, +15.47] |
| country_capital | `quotes` | layout + fence | `assert_r1` | 143 | 54.5% | -1.56 | +26.53 | [+25.21, +27.79] |
| country_capital | `quotes` | layout + fence | `bare` | 143 | 52.4% | 8.52 | +17.93 | [+16.59, +19.25] |
| country_capital | `tag_document` | E11's condition | `assert_r1` | 143 | 100.0% | 12.65 | +40.74 | [+39.64, +41.83] |
| country_capital | `tag_document` | E11's condition | `bare` | 143 | 100.0% | 16.49 | +25.90 | [+24.48, +27.35] |
| country_capital | `tag_passage` | same syntax, different word | `assert_r1` | 143 | 100.0% | 10.66 | +38.75 | [+37.61, +39.85] |
| country_capital | `tag_passage` | same syntax, different word | `bare` | 143 | 100.0% | 16.26 | +25.67 | [+24.22, +27.19] |
| country_capital | `tag_empty` | bracket syntax, no name at all | `assert_r1` | 143 | 62.9% | 0.76 | +28.84 | [+27.34, +30.27] |
| country_capital | `tag_empty` | bracket syntax, no name at all | `bare` | 143 | 94.4% | 8.24 | +17.65 | [+16.33, +18.96] |
| country_capital | `tag_untrusted` | same syntax, opposite valence | `assert_r1` | 143 | 0.0% | -27.33 | +0.76 | [+0.27, +1.23] |
| country_capital | `tag_untrusted` | same syntax, opposite valence | `bare` | 143 | 3.5% | -17.63 | -8.22 | [-9.94, -6.51] |
| country_capital | `tag_unreliable` | opposite valence, different words | `assert_r1` | 143 | 0.7% | -21.73 | +6.35 | [+5.69, +7.04] |
| country_capital | `tag_unreliable` | opposite valence, different words | `bare` | 143 | 2.1% | -15.50 | -6.09 | [-8.00, -4.31] |
| country_capital | `tag_trusted` | same syntax, positive valence | `assert_r1` | 143 | 100.0% | 17.01 | +45.09 | [+43.97, +46.29] |
| country_capital | `tag_trusted` | same syntax, positive valence | `bare` | 143 | 100.0% | 18.67 | +28.08 | [+26.56, +29.65] |
| country_capital | `tag_nonsense` | same syntax, no meaning at all | `assert_r1` | 143 | 74.8% | 2.88 | +30.97 | [+29.64, +32.29] |
| country_capital | `tag_nonsense` | same syntax, no meaning at all | `bare` | 143 | 78.3% | 3.96 | +13.37 | [+12.06, +14.68] |
| country_capital | `label_document` | same word, no markup | `assert_r1` | 143 | 99.3% | 10.30 | +38.39 | [+37.27, +39.50] |
| country_capital | `label_document` | same word, no markup | `bare` | 143 | 99.3% | 18.01 | +27.41 | [+25.89, +28.94] |
| country_capital | `label_search` | the RAG framing | `assert_r1` | 143 | 100.0% | 13.35 | +41.43 | [+40.31, +42.53] |
| country_capital | `label_search` | the RAG framing | `bare` | 143 | 100.0% | 14.82 | +24.23 | [+22.82, +25.64] |
| country_capital | `label_untrusted` | opposite valence, no markup | `assert_r1` | 143 | 0.7% | -19.29 | +8.80 | [+8.01, +9.59] |
| country_capital | `label_untrusted` | opposite valence, no markup | `bare` | 143 | 14.0% | -11.23 | -1.82 | [-3.05, -0.54] |

## How to read this

- **`blankline` is the layout control.** If it moves the margin as much as `tag_document`, E11's effect was whitespace and the document framing is a red herring. If it does not, the markup is doing real work.
- **`tag_passage` versus `tag_document`** separates the syntax from the word. **`label_document`** separates the word from the syntax.
- **`tag_untrusted` is the one to report.** It is the tag whose entire purpose is to mark text as not-to-be-trusted. If deference under it matches `tag_document`, the wrapper is read as *this is source material* and its stated valence is ignored. If it does NOT -- if the tag suppresses deference -- then the model is reading the label's meaning, and the question becomes why the same words fail when they are put in the system prompt instead.
- **`tag_nonsense` is the control for that reading.** `<qzx_block>` carries the same syntax and no meaning. If it behaves like `<document>`, an unfamiliar tag is not inherently suppressive and a low score for `<untrusted_content>` really is about the word. If it behaves like `<untrusted_content>`, then any out-of-distribution tag suppresses deference and the semantic reading is wrong. `tag_trusted` and `tag_unreliable` place the same contrast on a scale.
- **`tag_empty` splits the structure term itself.** `<qzx_block>` still has a name; `<>` has only the brackets. If `<>` matches `<qzx_block>`, the name contributes nothing and the structural effect is the bracket syntax. If `<>` falls back toward `dashes`, then a tag needs to NAME something -- anything -- and `<qzx_block>`'s +31 was already partly semantic.
- **`bare` versus `assert_r1`** asks whether the wrapper confers source authority or changes the task. `bare` has no source to trust, so if it swings too, the model is switching into reading-comprehension mode rather than deciding whom to believe.
- Margins are teacher-forced. Rates classify the answer with any reasoning preamble stripped.
