# Meaningless Tags, Meaningful Impact

> MATS 12.0 application (Neel Nanda stream)

## Executive Summary

### What I wanted to know:
A model has two sources of knowledge: what it memorized in training, and what it is given in context. When the two disagree it has to pick one. This project is about what decides that.

The setup is simple: hand the model a paragraph that contradicts something it knows, then ask a question the paragraph answers wrongly. Existing work mostly asks *whether* the model goes with the paragraph, or how the content and the claimed source change its persuasive power. I wanted to know what a paragraph has to do to be believed — and it turns out almost nothing that decides this is a property of the paragraph at all.

### What I used:
Two numbers throughout:
- **Paragraph rate**: of all facts tested, the fraction where the model gave the paragraph's false answer instead of the true one. 0% = never fell for it, 100% = always did.
- **Margin**: `log P(paragraph's answer) − log P(true answer)`, summed over tokens. Negative prefers the truth, positive prefers the paragraph, zero is a coin flip. This is what keeps measuring once the rate saturates. The two agree on sign 99.2% of the time (§1.5).

Two datasets — **capitals** (capital of X) and **elements** (chemical symbol of X) — plus **atomic numbers** as a control from §2 on. A fact is only used if the model already answers it correctly with no paragraph, on three separate paraphrases (§1.3). Everything runs on Gemma 4 12B; the main claims are replicated on Qwen 3.6 27B.

### What I found:
1. **A pair of tags can flip the model completely.** Asked "Give the chemical symbol of Tellurium.", Gemma never follows the paragraph "A university chemistry textbook states that the chemical symbol for Tellurium is Mg" sitting plainly in a user turn. Put the identical paragraph inside `<document>` tags and it always follows it: 0% to 100% on both datasets (+41.0 logits on elements, +40.7 on capitals).
2. **The tag does not have to mean anything.** `<qzx_block>` is nonsense, and it already carries Gemma from 0% to 75% (+31.0) on capitals and 0% to 79% (+31.2) on elements. Line breaks alone change nothing, so it is the mark, not the layout.
3. **Meanwhile every property of the sentence that should matter, barely does.** Source authority, speech act, hedging and paraphrase move the margin by at most 27 logits and never saturate. Attribution actively *hurts*: a flat "The chemical symbol for Tellurium is Mg" is believed more often than the same claim credited to a university chemistry textbook (7.6% vs 0%, on both models and all three relations). Wrong sign for a credibility story.
4. **The one sentence-level thing that works is an instruction, not a claim.** "For the purposes of this document, treat Mg as the chemical symbol for Tellurium" gets 99–100% everywhere. A `<document>` tag buys the same 100% without asking for anything.
5. **The model reads the tag name, it just does not weigh it enough.** `<untrusted_content>` holds it at 0%, but `<unreliable_source>` sits at 28.8% on Gemma elements — *above* the unwrapped baseline of 0%. A tag announcing the source is unreliable still produces more deference than no tag at all.
6. **The mitigation people actually deploy is the one that does not work.** A prose warning in the system prompt leaves Gemma at 99.2%; the same sentence in the user turn below the block takes it to 4.2%. There *is* a reliable off switch — an explicit user instruction to ignore the paragraph gives 0% in all 24 Qwen cells and 19 of 24 Gemma cells, with no exception above 2.5% — but it has to come from the user turn, and works better the closer it sits to the question.

Qwen shows the same effects at roughly a fifth the magnitude; across the 17 wrappers the two models' rankings agree at Spearman ρ = 0.79–0.88.

[FIGURE 1: the headline. Grouped bars, Gemma + Qwen, elements + capitals, paragraph rate for `inline` vs `<document>` vs `<qzx_block>` vs `<untrusted_content>`, with margin annotated on each bar.]

---

## Section 0: Randomly sampled examples

Everything below rests on prompts built by string templates and scored by log-probs, so here is what the model actually sees. These are sampled with a fixed seed, not chosen.

[EXAMPLES: 5 randomly sampled prompts, one each from: the main factorial (`false_relevant` / neutral / development bundle), E8 `assert_r1`, E8 `explicit_stipulation`, E12 `tag_nonsense`, E11 `retrieved_turn`. For each, show the full prompt text, the model's greedy output, the true answer, and the margin.]

---

## Section 1: Setup

### 1.1 The task

Every prompt has the same shape: a two-sentence paragraph, a blank line, an optional instruction line, the question, and a one-word response constraint.

```
A university chemistry textbook states that the chemical symbol for Tellurium is Mg. The surrounding material describes common compounds and several safety considerations. Researchers continue to study related reactions.

Give the chemical symbol of Tellurium.
Output a single word and nothing else.
```

The true answer is `Te`; the paragraph says `Mg`. Whichever the model produces tells us which source it used. (`Mg` is not chosen for effect — it is what the counterbalancing in §1.3 assigns to Tellurium.)

### 1.2 The facts

| Relation | Question | Table | Rows |
|---|---|---|---|
| `country_capital` | "What is the capital of X?" | Country/capital pairs, one orthographic word each, audited against UN geographic naming references | 153 |
| `element_symbol` | "What is the chemical symbol for X?" | All IUPAC element names and symbols | 118 |
| `element_atomic_number` | "What is the atomic number of X?" | The same elements, indexed by position | 118 |

**Nothing here is model-generated.** The fact tables are literal Python tuples in the generator, with their reference URL, audit date and exclusion rules recorded beside them in `RELATION_CURATION`. The capitals list was filtered by hand — anything with a disputed, changing, multiple, de facto-only or multi-word capital was dropped, and the exclusions are named in the file (Indonesia, South Africa, Switzerland, Bolivia and so on). The sentence templates are hand-written strings. No LLM generated the data and no LLM judged an output: answers are scored by exact match against the answer plus its aliases, and by teacher-forced log-probs. So there is no synthetic-data quality question underneath any of these results.

### 1.3 Screening and counterbalancing

**Only facts the model already knows.** A model that does not know Tellurium is `Te` cannot be said to defer about it. Before any experiment each model is asked every question with no paragraph, in three paraphrases, and a fact survives only if all three give a correct greedy answer, a parseable one-word output, and `logP(true) − logP(strongest false) > 0`. Gemma passed 267/271, Qwen 271/271. That screening margin is reused later as a per-fact **knowledge strength**, which matters in §6.

**False answers are assigned, not chosen.** Each fact's false answer is another fact's true answer, drawn by a seeded derangement, so every answer string appears exactly once as a truth and once as a falsehood — no result can be explained by some answers simply being more sayable. Two constraints are enforced jointly: a fact's false answer is never its own or its distractor's, and an irrelevant paragraph can never contain the correct answer to the question being asked.

### 1.4 The base factorial, and what it is for

The generated dataset crosses `condition_id` (true/false × relevant/irrelevant), `policy_id` (neutral/context/parametric) and `template_bundle_id` (three complete paraphrases): 271 facts × 4 × 3 × 3 = 9756 records. This is infrastructure, not a result — it exists to pin down the controls. Told to use the paragraph the model does [FILL: rate]; told to ignore it, it does not [FILL: rate]; and an irrelevant false paragraph moves nothing (measured directly in E7, Appendix A: 0.0% / −32.5 on elements, 0.7% / −33.7 on capitals). Everything below is measured under **`neutral`** — no instruction about which source to use — because it is the only policy not already pinned at a ceiling or a floor.

### 1.5 Two harnesses, one pipeline

E6 and E7 (Appendix A) read this dataset. From E8 on, the experiments build their own prompts in the same shape, because new claim sentences, relations, wrappers and turn structures are not points in the generator's factorial. They land in the same place: the `inline` / `assert_r1` / neutral cell on Gemma element symbols is computed independently by E8, E11 and E12 as **−27.11, −27.00 and −27.10** — a spread of 0.10 logits across three runs.

**And the margin tracks the behaviour.** On the main factorial, the sign of the margin agrees with the greedy answer on **99.18% of 2308 rows**, with every disagreement within 1.23 logits of a tie. The margin is the same story as the paragraph rate, with resolution left over once the rate saturates.

*On sample sizes: Gemma screened 267 facts but `require_complete_factorial_groups` leaves 263, which is exactly the 9468 rows scored and the 145 capitals + 118 elements in E6/E7. E8 onward re-screen independently under their own wording, giving 143 capitals (Gemma) / 146 (Qwen). Elements are 118 throughout.*

## Section 2: "What makes a paragraph believable?" — the wrong question

I started where the literature does: assuming this is a credibility judgement, and looking for the property of the paragraph that drives it. Three experiments in, that assumption was dead.

**Two experiments looking for the persuasive sentence (E6, E7; details in Appendix A).** The three paraphrase bundles in the base factorial were meant to be interchangeable and are not — on Gemma element symbols the highest sits at 76.3% deference and the lowest at 0.8%. E6 swaps each span (claim, filler, question, constraint) between those two prompts to find what carries it. On elements it is the claim sentence, cleanly: remove it and the high prompt collapses to 2.5%, insert it and the low prompt recovers to 64.4%. On capitals it localizes to the *filler* instead, and inserting the claim makes things worse. I have no account of that, and it was the first sign that "find the magic sentence" was the wrong frame.

E7 took the elements result at face value and crossed four properties of the claim sentence — speech act (a textbook that *uses* a symbol vs one that *states* it), two paraphrases of each, source authority (university textbook vs classroom wall poster), and a "consistently" hedge. The results are small and partly backwards. Stipulating beats asserting by ~15 logits, which is the largest effect and is not a credibility effect at all. Authority is worth 4.7 logits. The hedge *hurts*, by 11. On capitals nothing crosses 3%. And the sentence that beat everything I designed was `orig_high` at 64.4% — one of the generator's own templates, written earlier without thinking about it.

### E8 — is this about chemical symbols, or about stipulability?

One reading of the above is that symbols are *stipulable*: a document can legitimately adopt a notation, so "this textbook uses Mg for Tellurium" is a local convention rather than a false claim. Capitals are not stipulable that way. If that is the story, deference should track stipulability, not relation identity.

E8 tests it by adding `element_atomic_number` — same subjects, same sources, same sentence frames, but an atomic number is no more a notational convention than a capital is. It also adds two cells that bracket the range: `bare` (no source at all) and `explicit_stipulation` ("For the purposes of this document, treat Mg as the chemical symbol for Tellurium").

| Claim sentence | Gemma sym | Gemma cap | Gemma Z | Qwen sym | Qwen cap | Qwen Z |
|---|---|---|---|---|---|---|
| `explicit_stipulation` | 99.2% (+18.1) | 100.0% (+27.0) | 100.0% (+15.7) | 94.9% (+1.8) | 100.0% (+7.0) | 100.0% (+7.0) |
| `bare` | 7.6% (−15.3) | 22.4% (−9.6) | 40.5% (+1.0) | 35.6% (−0.4) | 2.7% (−4.3) | 72.4% (+1.1) |
| `stipulate_r1` | 23.7% (−11.6) | 1.4% (−27.5) | 12.1% (−7.0) | 0.0% (−8.4) | 0.0% (−16.9) | 0.0% (−5.1) |
| `stipulate_r2` | 3.4% (−17.0) | 0.7% (−27.6) | 5.2% (−9.3) | 0.0% (−9.9) | 0.0% (−16.8) | 0.9% (−6.3) |
| `assert_r1` | 0.0% (−27.1) | 0.0% (−28.2) | 31.9% (−0.8) | 0.0% (−7.2) | 0.0% (−11.1) | 1.7% (−4.1) |
| `assert_r2` | 0.8% (−25.7) | 0.0% (−30.5) | 22.4% (−4.5) | 0.0% (−8.9) | 0.0% (−11.8) | 1.7% (−5.2) |

*n (Gemma): 118 / 143 / 116. n (Qwen): 118 / 146 / 116. Format non-compliance was 0.0% everywhere except Qwen capitals `bare` (0.7%).*

**The stipulability story fails.** Atomic numbers are the least stipulable relation in the set and show the *most* deference on Gemma (`assert_r1` 31.9%, against 0.0% for both others). §6 takes two more swings at what separates the relations and lands neither.

But two results here matter far more than the one the experiment was designed for.

**Attribution hurts.** `bare` beats every attributed sentence, on every relation, on both models: elements 7.6% vs 0.0%, capitals 22.4% vs 0.0%, Qwen elements 35.6% vs 0.0%, Qwen atomic numbers 72.4% vs 1.7%. Putting "A university chemistry textbook states that…" in front of a false claim makes the model *less* likely to believe it than stating it flatly — by 11.8 logits on Gemma elements and 18.6 on capitals. If the model were weighing source credibility, naming a credible source should not be a penalty.

**And the one thing that works is not a claim.** `explicit_stipulation` reaches 99–100% on all three relations and both models. It is not more credible than `assert_r1` — it asserts nothing about the world at all. It is an *instruction*. Everything in the neighbourhood of "is this paragraph believable" moves 20-odd logits and mostly stays under 25%; the thing that moves 45 logits on elements, 55 on capitals, and saturates everywhere, is a sentence that tells the model what to do.

That reframed the project. The model does not look like it is running an evidence-weighing procedure on the paragraph. It looks like it is running an instruction-following procedure, and asking whether the paragraph counts as something addressed to it.

---

## Section 3: The channel

If the question is "does this paragraph count as something addressed to me", then the thing to vary is not the sentence, it is where the sentence sits.

E11 holds the paragraph, the question and the constraint byte-identical and moves them across boundaries: plain in the user turn (`inline`), wrapped in `<document>` tags in the same turn (`delimited`), or returned as the answer to a lookup request in a two-turn exchange (`retrieved_turn`: user asks "Look up a reference on Tellurium for me.", assistant replies "Here is what I found:" plus the wrapped paragraph, then the question follows).

**`assert_r1`, neutral policy — the sentence that never worked in §2**

| Channel | Gemma sym | Gemma cap | Qwen sym | Qwen cap |
|---|---|---|---|---|
| `inline` | 0.0% (−27.0) | 0.0% (−28.1) | 0.0% (−7.2) | 0.0% (−11.1) |
| `delimited` | 100.0% (+13.9) | 100.0% (+12.7) | 62.7% (+0.6) | 41.1% (+0.0) |
| `retrieved_turn` | 59.3% (+0.1) | 96.5% (+6.3) | 14.4% (−1.2) | 2.7% (−2.7) |

This is the headline. The claim sentence that survived every content manipulation in §2 at 0% goes to **100% when you put two tags around it**. On Gemma that is **+40.9 logits on elements and +40.7 on capitals** (E12 measures the same contrast at +41.0 and +40.7; see §1.5) — larger than the entire range of every content manipulation in E6, E7 and E8 combined, and it saturates where content never did.

Qwen moves the same direction at a much smaller scale: +7.8 logits on elements, +11.1 on capitals, enough to take the behaviour from 0% to 62.7% / 41.1%. Qwen's margins live on a compressed scale throughout (its `inline` baseline is −7.2 where Gemma's is −27.0), so I compare the two models by ranking and direction, not by logit magnitude.

The `retrieved_turn` result is worth noting on its own: an assistant turn presenting the paragraph as a lookup result is *most* of the way to a `<document>` tag, and on Gemma capitals it is 96.5%. This is the shape of an actual RAG or tool-use stack.

---

## Section 4: What is the wrapper actually doing?

`<document>` changes several things at once. It adds line breaks. It adds bracket syntax. It names the content "document". Which of those is doing the work?

E12 runs 17 wrappers over the identical paragraph, each chosen to rule out one explanation, crossed with the two claim sentences from §2 (`assert_r1`, the sentence nothing worked on, and `bare`, the unattributed one).

**`assert_r1`, neutral policy, ranked by Gemma element margin**

| Wrapper | What it rules out | Gemma sym | Gemma cap | Qwen sym | Qwen cap |
|---|---|---|---|---|---|
| `tag_trusted` | same syntax, positive valence | 100.0% (+16.4) | 100.0% (+17.0) | 1.7% (−3.0) | 4.8% (−4.9) |
| `tag_document` | E11's condition | 100.0% (+13.9) | 100.0% (+12.6) | 63.6% (+0.6) | 41.1% (+0.0) |
| `tag_passage` | same syntax, different word | 100.0% (+13.2) | 100.0% (+10.7) | 54.2% (+0.3) | 30.1% (−0.6) |
| `label_search` | the RAG framing | 100.0% (+12.9) | 100.0% (+13.4) | 2.5% (−3.2) | 2.7% (−5.7) |
| `label_document` | same word, no markup | 98.3% (+11.4) | 99.3% (+10.3) | 15.3% (−2.1) | 5.5% (−4.9) |
| `tag_nonsense` | same syntax, no meaning at all | 78.8% (+4.1) | 74.8% (+2.9) | 3.4% (−2.5) | 4.1% (−7.1) |
| `tag_gibberish` | no meaning at all | 49.2% (−3.0) | 36.4% (−4.4) | 0.0% (−3.7) | 2.7% (−7.5) |
| `label_nonsense` | nonsense label | 35.6% (−6.1) | 3.5% (−20.3) | 0.8% (−4.2) | 1.4% (−7.7) |
| `tag_unreliable` | opposite valence, different words | 28.8% (−6.0) | 0.7% (−21.7) | 0.0% (−8.2) | 0.0% (−13.4) |
| `tag_empty` | bracket syntax, no name at all | 25.4% (−12.5) | 62.9% (+0.8) | 0.0% (−5.0) | 2.1% (−7.1) |
| `dashes` | layout + fence | 23.7% (−9.3) | 33.6% (−4.8) | 0.8% (−3.9) | 2.1% (−7.1) |
| `quotes` | layout + fence | 5.9% (−18.5) | 53.8% (−1.6) | 1.7% (−3.8) | 2.1% (−5.9) |
| `label_gibberish` | gibberish label | 5.9% (−19.2) | 0.0% (−24.0) | 0.8% (−4.2) | 0.7% (−7.9) |
| `label_untrusted` | opposite valence, no markup | 0.0% (−21.4) | 0.7% (−19.3) | 0.0% (−7.8) | 0.0% (−12.3) |
| `tag_untrusted` | same syntax, opposite valence | 0.0% (−24.3) | 0.0% (−27.3) | 0.0% (−7.9) | 0.0% (−13.0) |
| `blankline` | layout only | 0.0% (−25.8) | 0.0% (−24.2) | 0.0% (−7.1) | 0.0% (−10.4) |
| `inline` | baseline | 0.0% (−27.1) | 0.0% (−28.1) | 0.0% (−7.2) | 0.0% (−11.1) |

Wrapper strings, verbatim: `blankline` = `\n{p}\n`; `dashes` = `---\n{p}\n---`; `quotes` = `"""\n{p}\n"""`; `tag_*` = `<name>\n{p}\n</name>`; `label_*` = `Name:\n{p}`. `tag_empty` is literally `<>\n{p}\n</>`.

**It is not the layout.** `blankline` gives the paragraph its own line breaks and changes nothing behaviourally: 0.0% on both relations, against a margin gain of only +1.3 logits on elements and +3.9 on capitals. Whatever is happening needs a mark, not whitespace.

**It does not need to mean anything.** `<qzx_block>` is a token sequence with no meaning in any corpus, and it carries Gemma from 0% to 78.8% on elements and 74.8% on capitals (+31.2 and +31.0) — **76% of the full `<document>` effect, bought with a nonsense word.**

**Bracket syntax and a document-ish word are two partly independent routes.** Strip the brackets from the nonsense word and most of the effect goes (`Qzx_block:` = 35.6% / 3.5%). Strip the brackets from the meaningful word and it survives (`Document:` = 98.3% / 99.3%). Keep the brackets and delete the word entirely and you still get something (`<>` = 25.4% / 62.9%). So either channel-marking syntax or a content-type word will get you partway, and together they saturate.

**The model reads the tag name — it just does not weigh it enough.** `<untrusted_content>` holds Gemma at 0.0% on both relations, so the semantics are clearly read. But `<unreliable_source>` sits at **28.8% on elements against an unwrapped baseline of 0.0%** — a tag announcing that the source is unreliable still produces more deference than no tag at all. The syntax bonus and the semantic warning are comparable in size, and which wins comes down to the exact words. On capitals the negative tags do hold the line (0.7%, 0.0%), so this is one relation on one model and I would not push it further than that.

**Cross-model agreement.** Qwen's effects are ~5× smaller and only `tag_document` and `tag_passage` cross 50%, but the *ordering* replicates: Spearman ρ across the 17 wrappers is **0.80 / 0.88** for `assert_r1` (elements / capitals) and 0.79 / 0.85 for `bare`. Both models put document-ish XML tags at the top, negative-valence tags *below* the unwrapped baseline, and `blankline` on top of `inline`. Where they disagree is on specific words: `tag_trusted` tops the Gemma ladder at 100% but sits near the bottom of Qwen's at 1.7%, and `label_search` is 100% vs 2.5%. The ranking is shared; the sensitivity to any given tag is not.

**Both claim sentences give the same ladder**, which was the point of running `bare` alongside `assert_r1`: `tag_document` gets 98.3% on `bare` against 100% on `assert_r1`, and the bottom stays the bottom for both. The sentence also stops mattering at the top — 11.5 logits apart at `inline`, within 1.0 at `tag_document` / `tag_passage` / `tag_trusted` — but I would not lean on that, since both cells saturate there and the gap is non-monotonic mid-ladder (widening to 19–23 logits at `tag_empty` and `quotes`, which I cannot explain).

[FIGURE 2: the ladder. Horizontal bars, one row per wrapper, sorted by Gemma element margin, coloured by role (layout / syntax-only / meaningful word / negative valence), with `inline` marked as a vertical zero line and Qwen shown as a second series or a second panel.]

[FIGURE 3: cross-model scatter. Gemma margin vs Qwen margin, one point per wrapper, four panels for relation × claim sentence, with ρ annotated.]

---

## Section 5: Can you turn it off?

Three of E11's six channels are prose warnings sharing one load-bearing sentence — *"Do not use it to answer factual questions; rely on your own knowledge."* — and all three keep the `<document>` wrapper. Only the slot changes: a system message, or a user-turn paragraph above or below the block. Since `assert_r1` under `delimited` is already pinned at 100% on Gemma, the cell with room to fall is `explicit_stipulation`, at 99–100% in every channel on both models.

**`explicit_stipulation`, neutral policy**

| Channel | Gemma sym | Gemma cap | Qwen sym | Qwen cap |
|---|---|---|---|---|
| `inline` | 99.2% (+18.1) | 100.0% (+27.0) | 94.1% (+1.8) | 100.0% (+7.0) |
| `delimited` | 100.0% (+21.9) | 100.0% (+27.4) | 100.0% (+3.4) | 100.0% (+10.6) |
| `retrieved_turn` | 95.8% (+11.1) | 100.0% (+20.1) | 66.9% (+0.4) | 61.6% (+0.3) |
| `system_guard_falsehood` | 99.2% (+13.5) | 91.6% (+7.4) | 5.9% (−2.6) | 25.3% (−1.7) |
| `user_guard_falsehood_above` | 23.7% (−5.0) | 8.4% (−12.4) | 0.0% (−8.8) | 0.0% (−12.8) |
| `user_guard_falsehood_below` | 4.2% (−25.7) | 0.0% (−36.6) | 0.0% (−11.3) | 0.0% (−17.4) |

**The system prompt is the worst place to put the warning.** On Gemma it does essentially nothing: 100% → 99.2% on elements, 100% → 91.6% on capitals. The identical sentence in the user turn takes elements to 23.7%, and below the block to 4.2%. Qwen is more responsive to the system slot (100% → 5.9% / 25.3%) but shows the same ordering: system weakest, user-below strongest.

**Position within the turn is worth ~20 points on its own.** `above` and `below` are byte-identical strings differing only in which side of the block the guard sits: 23.7% vs 4.2% on Gemma elements (−5.0 vs −25.7 logits), 8.4% vs 0.0% on capitals (−12.4 vs −36.6). Recency or adjacency-to-question, I cannot separate — they are confounded by construction.

**There is a reliable off switch, and it is an instruction from the user.** The `parametric` policy line — "Do not use the paragraph; rely on your own knowledge", on its own line just before the question — collapses deference across every channel, both claim sentences, both models. All 24 Qwen cells are at exactly 0.0%; Gemma is at 0.0% in 19 of 24, the five exceptions all `element_symbol` × `explicit_stipulation` and none above 2.5%. Margins run −23.2 to −38.4 on Gemma, −11.1 to −18.9 on Qwen. Nothing else in this project — no tag, no channel, no sentence — produces a floor like that.

So the model is perfectly controllable. It just does not get there by evaluating the paragraph. It gets there when the user turn contains an instruction, and the closer that instruction sits to the question, the better it works.

[FIGURE 4: guard placement. Grouped bars for the four guard-relevant channels × 2 models × 2 relations, `explicit_stipulation` neutral, with the `parametric` policy shown as a flat zero line across all of them.]

---

## Section 6: What I could not resolve

### 6.1 Why atomic numbers are different (E9 — a null)

E8 left a loose end: atomic numbers show far more deference than symbols or capitals. The obvious hypothesis is that this is not about the relation but about how firmly the model holds the fact.

E9 tests that with the screening margin as a per-fact strength measure, and cannot answer it: the relations' strength distributions barely overlap (Gemma medians 38.6 capitals, 36.6 symbols, 21.8 atomic numbers), so relation and strength are confounded and no matched comparison exists. Splitting each relation at its own median does not rescue it — symbols and capitals sit at 0% leakage in *both* halves, and atomic numbers are identical across halves (20.7% on `bare` in each). On Qwen the one relation with headroom runs backwards: neutral `bare` is 63.8% in the weak half, 81.0% in the strong. **This is a null.** I do not know why atomic numbers differ, and this experiment could not have told me.

### 6.2 Plausibility and knowledge strength are the same axis (E10)

The other hypothesis is that it is about the *false answer*: claiming Tellurium is element 53 when it is 52 is a near miss, while claiming its symbol is `Mg` is not. E10 crosses false-answer distance — offsets of ±1, ±2, ±5, ±20 for atomic numbers, and the adjacent table row (`near`) for symbols and capitals, each against the derangement's `random` baseline.

The effect is large: on Gemma atomic numbers `assert_r1` goes from **24.3% at `random` to 83.5% at d2**, and `bare` from 33.0% to 87.8%. But mean knowledge strength moves in lockstep — 15.6 / 16.2 / 19.7 / 21.4 / 22.0 across d1/d2/d5/d20/random — and that is no coincidence: strength *is* `logP(true) − logP(false)`, so a plausible false answer mechanically lowers it. Distance and strength are one variable measured twice, and this design cannot separate them.

This is why every other experiment uses `random` false answers: it is the conservative end of the axis, which makes the deference rates elsewhere floors rather than ceilings.

### 6.3 Limitations

- **Two models, three relations, single-word answers, greedy decoding.** No sampling, no long-form generation, and both configs run with `enable_thinking: false` — whether any of this survives in a model allowed to reason first is untested.
- **E6 and E7 are Gemma-only** and E6's two relations contradict each other (Appendix A). E10's Qwen run covers only atomic numbers and symbols, not capitals. E8, E11 and E12 ran on both models in full.
- **`tag_trusted` and `label_search` behave completely differently across models** (§4), so the response to any *specific* tag is model-specific even where the ranking correlates at ρ ≈ 0.8.
- **The `above`/`below` guard contrast confounds position with distance-to-question** (§5).
- **I have not looked inside the model.** Everything here is behavioural. The obvious next step is whether the wrapper effect has a linear representation — activation capture is already plumbed through `02_collect_model_data.py` at `claim_end` / `context_end` / `prompt_end` / `assistant_start`, but left disabled because the behavioural sweep used the time.

### 6.4 What I checked by hand

> **[TODO — re-run these yourself before submitting.]** Every line was checked while drafting, but this section is only worth something if *you* ran the checks. Rewrite it in terms of what you personally did and found.

- Recomputed the headline +41.0 logits, the `<qzx_block>` numbers and the cross-model Spearman correlations straight from the raw CSVs, not from the analysis scripts' own reports.
- Re-ran the three-harness agreement (0.10 logits) and the greedy-vs-margin agreement (99.18%) against the raw JSONL.
- Rebuilt the dataset from the seed and read the generated prompts, to confirm the false answers are the derangement's rather than something I assumed. **This caught a real error:** an earlier draft used "the chemical symbol for Tellurium is Np" as its running example. The derangement never assigns `Np` to Tellurium — it is `Hs` in the main factorial and `Mg` in E8/E11/E12. Corrected; no result depended on it.
- [FILL: read N raw prompts by hand and confirm the spans and counterbalancing hold. Say how many, and what you found.]
- [FILL: anything else you spot-checked and found *wrong*. This is worth more than the things that were right.]

---

## Appendix A: E6 and E7 in full

Both are Gemma-only, and both are superseded by E8. They are here because they are why §2 stopped looking for a persuasive sentence.

**E6 — which span carries the paraphrase swing.** Endpoints are the highest- and lowest-deference template bundles; each cell moves one span across. The script verifies its rebuilt endpoint prompts are byte-identical to the originals in the dataset.

| Cell | element_symbol | country_capital |
|---|---|---|
| `endpoint_high` | 76.3% (+3.2) | 44.1% (−3.6) |
| `endpoint_low` | 0.8% (−27.7) | 2.8% (−15.8) |
| `high_minus_claim` | 2.5% (−25.0) | 11.7% (−13.0) |
| `low_plus_claim` | 64.4% (−0.1) | 2.8% (−19.4) |
| `low_plus_filler` | 0.8% (−27.9) | 13.1% (−9.1) |

Question and constraint swaps move little on either relation (all 20 cells in `decomposition_cells.csv`). On elements the claim sentence is necessary and nearly sufficient; on capitals the filler is, and the claim swap is actively harmful. I have no explanation for the disagreement.

**E7 — which property of the claim sentence.** Source authority (high/low) × speech act (stipulate/assert) × realization (r1/r2) × "consistently" hedge (present/absent), in a fixed frame, plus anchors.

| Cell | element_symbol | country_capital |
|---|---|---|
| `stipulate_r1_high_absent` | 18.6% (−10.2) | 2.8% (−26.8) |
| `stipulate_r1_high_present` | 5.9% (−21.5) | 1.4% (−28.7) |
| `assert_r1_high_absent` | 2.5% (−25.4) | 0.0% (−27.4) |
| `bare` | 8.5% (−14.5) | 22.8% (−9.3) |
| `orig_high` | 64.4% (−0.1) | 2.8% (−19.4) |
| `irrelevant_assert` | 0.0% (−32.5) | 0.7% (−33.7) |

Stipulate beats assert by ~15 logits on elements; authority is worth 4.7; the hedge costs 11. Capitals never cross 3%. All 42 cells in `phrasing_cells.csv`.

## Appendix B: Running it

`cmds.sh` runs the whole thing in order, with expected record counts and runtimes at each step. The dataset generator is deterministic in `--seed`; both models read the identical `conflict_awareness_dataset/`, which is what makes them comparable.

## Appendix C: Time

[FILL: Toggl screenshot / hours breakdown.]
