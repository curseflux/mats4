# Meaningless Tags, Meaningful Impact

> MATS 12.0 application (Neel Nanda stream)

## Executive Summary

### What I wanted to know:
A model has two sources of knowledge: what it memorized in training, and what it is given in context. When the two disagree it has to pick one. This project is about what decides that.

The setup is simple: hand the model a paragraph that contradicts something it knows, then ask a question the paragraph answers wrongly. Existing work mostly asks *whether* the model goes with the paragraph, or how the content and the claimed source change its persuasive power. I wanted to know what a paragraph has to do to be believed — and it turns out almost nothing that decides this is a property of the paragraph at all.

### What I used:
Two numbers throughout:
- **Paragraph rate**: of all facts tested, the fraction where the model gave the paragraph's false answer instead of the true one. 0% = never fell for it, 100% = always did.
- **Margin**: `log P(paragraph's answer) − log P(true answer)`, summed over tokens. Negative prefers the truth, positive prefers the paragraph, zero is a coin flip. This is what keeps measuring once the rate saturates. The two agree on sign 99.2% of the time (§1.3).

Two datasets — **capitals** (capital of X) and **elements** (chemical symbol of X) — plus **atomic numbers** as a control from §2.3 on. A fact is only used if the model already answers it correctly with no paragraph, on three separate paraphrases (§1.4). Everything runs on Gemma 4 12B; the main claims are replicated on Qwen 3.6 27B.

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

The true answer is `Te`. The paragraph says `Mg`. Whichever the model produces tells us which source it used. (The paragraph is a single line; it is only wrapped here for display. `Mg` is not chosen for effect — it is what the seeded derangement in §1.5 assigns to Tellurium.)

### 1.2 The facts

There are two relations, plus a third added later as a control.

| Relation | Question form | Source of the fact table | Rows |
|---|---|---|---|
| `country_capital` | "What is the capital of X?" | Country/capital pairs, one orthographic word each, manually audited against UN geographic naming references | 153 |
| `element_symbol` | "What is the chemical symbol for X?" | All 118 IUPAC element names and symbols | 118 |
| `element_atomic_number` | "What is the atomic number of X?" | The same 118 elements, indexed by position | 118 |

The fact tables are not model-generated. They are written out in the generator (`build_conflict_awareness_dataset.py`) as literal Python tuples, with the reference URL, the audit date, and the exclusion rules recorded alongside them in `RELATION_CURATION`. The capitals list was filtered by hand: any country with a disputed, changing, multiple, de facto-only or multi-word capital was dropped, and the exclusions are listed by name in the file (Indonesia and Equatorial Guinea for capital transitions, South Africa and Eswatini for multiple capitals, Switzerland because Bern is formally a federal city, Bolivia/Benin/Malaysia for capital-versus-seat distinctions, and so on). The Netherlands was kept, because Amsterdam is constitutionally the capital even though the seat of government is in The Hague. The elements table is the full IUPAC list in atomic-number order, with no exclusions.

No LLM was used to generate the facts, to write the sentence templates, or to judge any output. The templates are hand-written strings in the generator; the outputs are scored by exact-match against the answer plus its aliases, and by teacher-forced log-probs. This matters because it means there is no generated-data quality question sitting under the results — the only judgement calls are the ones listed above, and they are in the code.

### 1.3 The metric

For each prompt I record two things.

**The greedy answer**, decoded with `do_sample=False` and 16 max new tokens, then classified as `contextual` (matches the paragraph's answer), `parametric` (matches the true answer or one of its aliases), or `other`.

**The margin**, computed by teacher-forcing each candidate answer and taking the difference of sequence log-probs:

```
margin = logP(paragraph's answer) − logP(best-scoring true answer)
```

These are sequence log-probs, summed over tokens, so multi-token answers like `Washington` are handled correctly. The true side takes the max over the answer's aliases (`Kyiv`/`Kiev`, `Bogota`/`Bogotá`, and so on), which is the conservative choice — it makes the true answer look as strong as possible.

**Do the two agree?** On the main factorial, restricted to rows the greedy decode classified as either contextual or parametric, the sign of the margin agrees with the greedy answer on **99.18% of 2308 rows**, and every disagreement occurs within **1.23 logits of a tie**. So the margin is not telling a different story from the behaviour; it is the same story with resolution left over once the rate has saturated at 0% or 100%. That check is in `cmds.sh` and reproduces from `behavior_results.jsonl`.

### 1.4 Screening: only facts the model actually knows

A model that does not know that Tellurium is `Te` cannot be said to defer to a paragraph claiming otherwise. So before any experiment, each model is asked every question with no paragraph at all, in three different paraphrases. A fact survives only if, on **all three** paraphrases:

1. the greedy answer is correct,
2. the output is one orthographic word (so it is parseable), and
3. `logP(true) − logP(strongest false candidate) > 0`.

Gemma passed 267/271 facts, Qwen 271/271, and every surviving fact was answered correctly on all three of its screening prompts (Gemma 801/801).

The screening margin is reused later as a per-fact measure of **knowledge strength**, which turns out to matter in §6.

### 1.5 Counterbalancing by derangement

The false answer for each fact is another fact's true answer, assigned by a seeded random derangement rather than picked. This means every answer string appears as a true answer exactly once and as a false answer exactly once, so the results cannot be explained by some answers being intrinsically more sayable.

Two extra constraints are enforced jointly (`counterbalance_maps`):
- a fact's false answer is never its own true answer and never its distractor's,
- and for the irrelevant conditions, `false_source[distractor[i]] != i`, so an irrelevant paragraph never accidentally contains the correct answer to the question being asked.

Derangements are drawn inside `split × cv-fold` strata, so the assignment is balanced across splits too.

### 1.6 The base factorial, and what it is for

The generated dataset crosses three switches: `condition_id` (true/false × relevant/irrelevant), `policy_id` (neutral / context / parametric), and `template_bundle_id` (development / validation / heldout_paraphrase — three complete paraphrases of the claim, filler, question and constraint). That is 271 facts × 4 × 3 × 3 = 9756 experiment records, plus 813 screening records. Gemma scored 9468 rows, Qwen 9756.

This factorial is infrastructure, not a result. It exists to establish three things before the interesting experiments start:

- **`context` policy is a positive control.** Told to use the paragraph, the model does. [FILL: rate from `behavior_results.jsonl`, `policy_id == "context"`, `condition_id == "false_relevant"`.]
- **`parametric` policy is a negative control.** Told to ignore the paragraph, the model does. [FILL: same, `policy_id == "parametric"`.]
- **Irrelevance kills the effect.** A false paragraph about a *different* subject moves nothing. I have this measured directly in E7 for both relations, under the neutral policy and with no wrapper: `irrelevant_assert` is 0.0% (−32.5) on elements and 0.7% (−33.7) on capitals; `irrelevant_stipulate` is 0.0% (−32.0) and 0.0% (−33.6). So the deference we measure is genuinely about the conflict, not about a paragraph being present.

The `neutral` policy — no instruction at all about which source to use — is the condition everything below is measured in, because it is the only one that is not already pinned at a ceiling or a floor.

### 1.7 One pipeline, two harnesses

E6 and E7 read the generated dataset. From E8 onward the experiments build their own prompts, because the manipulations (new claim sentences, new relations, new wrappers, new turn structures) are not points in the generator's factorial and retrofitting them into it would have meant regenerating and re-running everything.

Both harnesses assemble prompts in the same shape, and I checked they land in the same place. The `inline` / `assert_r1` / neutral cell on Gemma element symbols is computed independently by three separate scripts:

| Run | Mean margin | n |
|---|---|---|
| E8 | −27.11 | 118 |
| E11 | −27.00 | 118 |
| E12 | −27.10 | 118 |

A spread of **0.10 logits across three independent runs**. This check is the last block in `cmds.sh`.

A note on *n*, since it moves between tables. Gemma screened 267/271 facts as known, but `collection.require_complete_factorial_groups` drops any fact missing a cell, leaving 263 — which is exactly the 9468 rows Gemma scored (263 × 4 × 3 × 3), and exactly the 145 capitals + 118 elements that E6 and E7 report. Qwen screened all 271 and scored the full 9756. E8 onward re-screen the fact tables independently, under their own question and constraint wording, so capitals there are 143 (Gemma) / 146 (Qwen). Elements are 118 everywhere.

---

## Section 2: "What makes a paragraph believable?" — the wrong question

I started where the literature does: assuming this is a credibility judgement, and looking for the property of the paragraph that drives it. Three experiments in, that assumption was dead.

### 2.1 E6 — which part of the paragraph carries the swing?

The first thing I noticed in the base factorial is that the three paraphrase bundles, which are supposed to be interchangeable, are not: on Gemma element symbols the highest-deference bundle sits at 76.3% and the lowest at 0.8%. That is a big effect for something that was meant to be a robustness control, and it is a free handle on the mechanism — whatever differs between those two bundles is causally sufficient to move deference.

Four things differ: the claim sentence, the filler sentences, the question wording, and the response constraint. E6 takes the high and low endpoint prompts and swaps each span across, one at a time, in both directions. Everything else is byte-identical; the script also verifies its rebuilt endpoint prompts against `raw_prompt` in the dataset to confirm they reproduce the originals exactly.

| Cell | element_symbol | country_capital |
|---|---|---|
| `endpoint_high` | 76.3% (+3.2) | 44.1% (−3.6) |
| `endpoint_low` | 0.8% (−27.7) | 2.8% (−15.8) |
| `high_minus_claim` | 2.5% (−25.0) | 11.7% (−13.0) |
| `low_plus_claim` | 64.4% (−0.1) | 2.8% (−19.4) |
| `high_minus_filler` | 89.0% (+7.7) | 2.8% (−15.4) |
| `low_plus_filler` | 0.8% (−27.9) | 13.1% (−9.1) |
| `high_minus_question` | 65.3% (+1.4) | 7.6% (−11.6) |
| `low_plus_question` | 4.2% (−21.4) | 4.1% (−19.4) |
| `high_minus_constraint` | 55.1% (−0.7) | 43.4% (−3.4) |
| `low_plus_constraint` | 0.8% (−26.6) | 3.4% (−15.2) |

On **elements this is clean**: take the claim sentence out of the high prompt and it collapses (76.3% → 2.5%); put the claim sentence into the low prompt and it recovers almost the whole swing (0.8% → 64.4%). The claim sentence is necessary and nearly sufficient. Nothing else does much.

On **capitals it localizes somewhere else entirely** — to the filler. `low_plus_claim` makes things *worse* (−15.8 → −19.4), while `low_plus_filler` is the only cell that improves on the low endpoint (−15.8 → −9.1). I do not have an account of this, and I flag it as the clearest unexplained result in the project. What it does tell me is that "the claim sentence is the locus" was a relation-specific fact I should not have generalized — which is part of why §3 onward stopped trying to find the magic sentence.

E6 was Gemma-only.

[FIGURE 2: E6 swap ladder. Two panels (elements, capitals), horizontal bars for each cell, with the high and low endpoints marked as vertical reference lines.]

### 2.2 E7 — which *property* of the claim sentence?

Taking the elements result at face value, E7 crosses four properties of the claim sentence in a fixed frame:

- **speech act**: `stipulate` ("A university chemistry textbook *uses* Mg as the chemical symbol for Tellurium") vs `assert` ("*states that* the chemical symbol for Tellurium *is* Mg")
- **realization**: two paraphrases of each act, to separate the act from the wording
- **source authority**: "A university chemistry textbook" vs "A classroom wall poster" (capitals: "A national geography textbook" vs "A tourist brochure")
- **persistence hedge**: with or without "consistently"

Plus a `bare` sentence with no source at all, the two original E6 claim sentences as anchors, and the irrelevant controls from §1.6.

| Cell | element_symbol | country_capital |
|---|---|---|
| `stipulate_r1_high_absent` | 18.6% (−10.2) | 2.8% (−26.8) |
| `stipulate_r1_high_present` | 5.9% (−21.5) | 1.4% (−28.7) |
| `stipulate_r1_low_absent` | 17.8% (−14.9) | 2.8% (−28.9) |
| `stipulate_r1_low_present` | 6.8% (−19.4) | 1.4% (−32.6) |
| `stipulate_r2_high_absent` | 6.8% (−15.8) | 1.4% (−27.0) |
| `stipulate_r2_low_absent` | 8.5% (−14.7) | 0.7% (−30.4) |
| `assert_r1_high_absent` | 2.5% (−25.4) | 0.0% (−27.4) |
| `assert_r1_high_present` | 3.4% (−24.7) | 0.0% (−29.6) |
| `assert_r1_low_absent` | 0.8% (−28.4) | 0.0% (−32.2) |
| `assert_r1_low_present` | 0.0% (−30.7) | 0.0% (−33.8) |
| `bare` | 8.5% (−14.5) | 22.8% (−9.3) |
| `orig_high` | 64.4% (−0.1) | 2.8% (−19.4) |
| `orig_low` | 0.8% (−27.7) | 3.4% (−15.8) |
| `irrelevant_assert` | 0.0% (−32.5) | 0.7% (−33.7) |
| `irrelevant_stipulate` | 0.0% (−32.0) | 0.0% (−33.6) |

Three things fall out:

- **Stipulating beats asserting**, by about 15 logits on elements (`stipulate_r1_high_absent` −10.2 vs `assert_r1_high_absent` −25.4). That is the largest single content effect in the table, and it is not a credibility effect — a textbook that *uses* a symbol is not more trustworthy than one that *states* it, it is doing a different kind of speech act.
- **Authority barely registers.** Swapping "university chemistry textbook" for "classroom wall poster" moves elements from −10.2 to −14.9, about 4.7 logits, and moves capitals essentially not at all. Hedging with "consistently" *hurts* (−10.2 → −21.5), which is the opposite of what a persuasion story predicts.
- **On capitals, none of it crosses 3%.** The whole crossed design is dead on one of the two relations.

And the anchor that beats everything I constructed is `orig_high` at 64.4% — one of the generator's own claim sentences. So after two experiments explicitly designed to find the persuasive properties of a sentence, the best sentence I had was still one I had written earlier without thinking about it.

E7 was Gemma-only.

### 2.3 E8 — is this about chemical symbols, or about stipulability?

One reading of E7 is that symbols are *stipulable*: a document can legitimately adopt a notation, so "this textbook uses Mg for Tellurium" is not really a false claim about the world, it is a local convention. Capitals are not stipulable that way. If that is the story, deference should track stipulability rather than relation identity.

E8 tests this by adding `element_atomic_number` — same subjects, same source, same sentence frames, but an atomic number is not a notational convention any more than a capital is. It also adds two cells that bracket the range: `bare` (no source at all) and `explicit_stipulation` ("For the purposes of this document, treat Mg as the chemical symbol for Tellurium").

| Claim sentence | Gemma sym | Gemma cap | Gemma Z | Qwen sym | Qwen cap | Qwen Z |
|---|---|---|---|---|---|---|
| `explicit_stipulation` | 99.2% (+18.1) | 100.0% (+27.0) | 100.0% (+15.7) | 94.9% (+1.8) | 100.0% (+7.0) | 100.0% (+7.0) |
| `bare` | 7.6% (−15.3) | 22.4% (−9.6) | 40.5% (+1.0) | 35.6% (−0.4) | 2.7% (−4.3) | 72.4% (+1.1) |
| `stipulate_r1` | 23.7% (−11.6) | 1.4% (−27.5) | 12.1% (−7.0) | 0.0% (−8.4) | 0.0% (−16.9) | 0.0% (−5.1) |
| `stipulate_r2` | 3.4% (−17.0) | 0.7% (−27.6) | 5.2% (−9.3) | 0.0% (−9.9) | 0.0% (−16.8) | 0.9% (−6.3) |
| `assert_r1` | 0.0% (−27.1) | 0.0% (−28.2) | 31.9% (−0.8) | 0.0% (−7.2) | 0.0% (−11.1) | 1.7% (−4.1) |
| `assert_r2` | 0.8% (−25.7) | 0.0% (−30.5) | 22.4% (−4.5) | 0.0% (−8.9) | 0.0% (−11.8) | 1.7% (−5.2) |

*n (Gemma): symbols 118, capitals 143, atomic numbers 116. n (Qwen): 118 / 146 / 116. Format non-compliance was 0.0% in every cell except Qwen capitals `bare` (0.7%).*

The stipulability story **fails**. Atomic numbers are the *least* stipulable relation in the set and they show the *most* deference on Gemma (`assert_r1` 31.9%, against 0.0% for both others). Whatever separates the relations, it is not whether a document could legitimately declare the answer. §6 takes two more swings at what it actually is, and does not land one.

Two results here matter much more than the one the experiment was designed for.

**First: attribution hurts.** `bare` beats every attributed sentence, on every relation, on both models. Elements 7.6% vs 0.0%, capitals 22.4% vs 0.0%, Qwen elements 35.6% vs 0.0%, Qwen atomic numbers 72.4% vs 1.7%. Saying "A university chemistry textbook states that…" in front of a false claim makes the model *less* likely to believe it than just stating the claim flatly — by 11.8 logits on Gemma elements and 18.6 on capitals. If the model were weighing source credibility, naming a credible source should not be a penalty.

**Second: the one thing that works is not a claim.** `explicit_stipulation` reaches 99–100% on all three relations and both models. Its content is not more credible than `assert_r1` — it is not even asserting anything about the world. It is an *instruction*, addressed to the model, about what to do. Everything in the neighbourhood of "is this paragraph believable" moves 20-odd logits and mostly stays under 25%. The thing that moves 45 logits on elements and 55 on capitals, and saturates on every relation, is a sentence that tells the model what to do.

That reframed the project. The model does not appear to be running an evidence-weighing procedure on the paragraph. It appears to be running an instruction-following procedure, and asking whether the paragraph counts as something addressed to it.

[FIGURE 3: E8 as a dot plot. x = margin, y = claim sentence, one panel per relation, two colours for the two models, with the paragraph rate printed next to each dot.]

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

This is the headline. The claim sentence that survived every content manipulation in §2 at 0% goes to **100% when you put two tags around it**. On Gemma that is **+40.9 logits on elements and +40.7 on capitals** (E12 measures the same contrast at +41.0 and +40.7; see §1.7) — larger than the entire range of every content manipulation in E6, E7 and E8 combined, and it saturates where content never did.

Qwen moves the same direction at a much smaller scale: +7.8 logits on elements, +11.1 on capitals, enough to take the behaviour from 0% to 62.7% / 41.1%. Qwen's margins live on a compressed scale throughout (its `inline` baseline is −7.2 where Gemma's is −27.0), so I compare the two models by ranking and direction, not by logit magnitude.

The `retrieved_turn` result is worth noting on its own: an assistant turn presenting the paragraph as a lookup result is *most* of the way to a `<document>` tag, and on Gemma capitals it is 96.5%. This is the shape of an actual RAG or tool-use stack.

[FIGURE 4: E11. Slope chart, `inline` → `delimited` → `retrieved_turn`, one line per (model, relation), margin on the y-axis, paragraph rate labelled at each point.]

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

**It does not need to mean anything.** `<qzx_block>` is a token sequence with no meaning in any corpus, and it carries Gemma from 0% to 78.8% on elements and 74.8% on capitals (+31.2 and +31.0 logits). That is ~76% of the full `<document>` effect, bought with a nonsense word.

**Bracket syntax and a document-ish word are two partly independent routes.** Strip the brackets from the nonsense word and most of the effect goes (`Qzx_block:` = 35.6% / 3.5%). Strip the brackets from the meaningful word and it survives (`Document:` = 98.3% / 99.3%). Keep the brackets and delete the word entirely and you still get something (`<>` = 25.4% / 62.9%). So either channel-marking syntax or a content-type word will get you partway, and together they saturate.

**The model reads the tag name — it just does not weigh it enough.** This is the part I find most interesting. `<untrusted_content>` holds Gemma at 0.0% on both relations, so the semantics are clearly being read. But `<unreliable_source>` sits at **28.8% on elements against an unwrapped baseline of 0.0%** — a tag that explicitly announces the source is unreliable still produces more deference than no tag at all. The syntax bonus and the semantic warning are roughly the same size, and which one wins comes down to the exact words. On capitals the negative tags do hold the line (0.7% and 0.0%), so this is one relation on one model and I would not push it further than "the two effects are comparable in magnitude".

**Cross-model agreement.** Qwen's effects are roughly 5× smaller and it only crosses 50% for `tag_document` and `tag_passage`. But the *ordering* of the 17 wrappers replicates well: Spearman ρ between the two models' margins across wrappers is **0.80 (elements, `assert_r1`), 0.88 (capitals, `assert_r1`), 0.79 and 0.85 for the `bare` sentence**. Both models put document-ish XML tags at the top, put the negative-valence tags *below* the unwrapped baseline, and put `blankline` on top of `inline`. Ranked by margin gain over `inline`, Qwen elements gives `tag_document` +7.75, `tag_passage` +7.46, `label_document` +5.09, `tag_nonsense` +4.69, down through `blankline` +0.04 to `tag_untrusted` −0.75 and `tag_unreliable` −1.00.

The one place they clearly disagree is `tag_trusted`: top of the ladder on Gemma (100%), near the bottom on Qwen (1.7%). And `label_search`, which is 100% on Gemma, is 2.5% on Qwen. So the *strength* of the response to a given tag is model-specific even where the ranking broadly holds.

**Both claim sentences, same ladder.** Running the whole thing on `bare` as well as `assert_r1` was meant as a robustness check, and it passes: `tag_document` gets 98.3% on `bare` where it gets 100% on `assert_r1`, and the bottom of the ladder stays at the bottom for both. It also shows the sentence stops mattering at the top: at `inline` the two sentences are 11.5 logits apart, and at `tag_document` / `tag_passage` / `tag_trusted` they are within 1.0 logit of each other. I would not lean on this — both cells are saturated at ~100% there, so the compression may be a ceiling effect, and the gap is non-monotonic in the middle of the ladder (it *widens* to 19–23 logits at `tag_empty` and `quotes`, which I cannot explain).

[FIGURE 5: the ladder. Horizontal bars, one row per wrapper, sorted by Gemma element margin, coloured by role (layout / syntax-only / meaningful word / negative valence), with `inline` marked as a vertical zero line and Qwen shown as a second series or a second panel.]

[FIGURE 6: cross-model scatter. Gemma margin vs Qwen margin, one point per wrapper, four panels for relation × claim sentence, with ρ annotated.]

---

## Section 5: Can you turn it off?

Three of E11's six channels are prose warnings. All three use the same load-bearing sentence — *"Do not use it to answer factual questions; rely on your own knowledge."* — and all three keep the `<document>` wrapper. Only the slot changes: a system message, a user-turn paragraph above the block, or a user-turn paragraph below the block. The framing clause differs slightly between the system and user versions only because a system prompt has to refer to material the user has not sent yet.

On Gemma, `assert_r1` under `delimited` is already pinned at 100%, so the cell with room to fall is `explicit_stipulation`, which starts at 99–100% in every channel on both models.

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

**Position within the turn is worth ~20 points on its own.** `above` and `below` are byte-identical strings differing only in which side of the `<document>` block the guard paragraph sits: 23.7% vs 4.2% on Gemma elements, 8.4% vs 0.0% on capitals, −5.0 vs −25.7 logits and −12.4 vs −36.6. Whether this is recency or adjacency to the question I cannot separate here — the guard is closer to the question in the `below` condition, and those two are confounded by construction.

**There is a reliable off switch, and it is an instruction from the user.** The `parametric` policy line — "Do not use the paragraph; rely on your own knowledge", sitting on its own line just before the question — collapses deference across every channel, for both claim sentences, on both models. All 24 Qwen cells are at exactly 0.0%. Gemma is at 0.0% in 19 of 24; the five exceptions are all `element_symbol` × `explicit_stipulation`, and the largest is 2.5% (three facts out of 118). Margins run −23.2 to −38.4 on Gemma and −11.1 to −18.9 on Qwen. Nothing else in this project — no tag, no channel, no sentence — produces a floor like that.

So the model is perfectly controllable. It just does not reach that state by evaluating the paragraph. It reaches it when the user turn contains an instruction telling it what to do, and the closer that instruction sits to the question, the better it works.

[FIGURE 7: guard placement. Grouped bars for the four guard-relevant channels × 2 models × 2 relations, `explicit_stipulation` neutral, with the `parametric` policy shown as a flat zero line across all of them.]

---

## Section 6: What I could not resolve

### 6.1 Why atomic numbers are different (E9, a null)

E8 left a loose end: atomic numbers show far more deference than symbols or capitals on Gemma. One hypothesis is that this is not about the relation at all, but about how firmly the model holds the fact — atomic numbers might simply be weaker memories.

E9 tests this using the screening margin (§1.4) as a per-fact strength measure. It does not work, and the reason is structural: the relations' strength distributions barely overlap. Gemma's median strength is 38.6 for capitals, 36.6 for symbols, and 21.8 for atomic numbers, with a q10–q90 of 15.8–26.7 for atomic numbers against 28.0–41.3 for symbols. Relation and strength are confounded in this dataset and no matched comparison exists.

Splitting each relation at its own median does not rescue it either, because the deference floor for symbols and capitals is 0% in both halves — there is no room for a gradient to appear:

| Model | Relation | Bin | n | `bare` | `assert_r1` | `explicit` | neutral `bare` |
|---|---|---|---|---|---|---|---|
| gemma | country_capital | weak | 71 | 0.0% | 0.0% | 0.0% | 18.3% |
| gemma | country_capital | strong | 72 | 0.0% | 0.0% | 0.0% | 26.4% |
| gemma | element_atomic_number | weak | 58 | 20.7% | 6.9% | 0.0% | 44.8% |
| gemma | element_atomic_number | strong | 58 | 20.7% | 5.2% | 0.0% | 36.2% |
| gemma | element_symbol | weak | 59 | 0.0% | 0.0% | 1.7% | 8.5% |
| gemma | element_symbol | strong | 59 | 0.0% | 0.0% | 0.0% | 6.8% |

*(measured under the `parametric` policy; the last column is the same cell under `neutral`, as a baseline. Qwen rows are in `knowledge_strength_bins.csv` and show the same floors. Qwen actually runs the wrong way on the one relation with headroom: neutral `bare` is 63.8% in the weak half of atomic numbers and 81.0% in the strong half.)*

Within atomic numbers, weak and strong halves are identical on `bare` (20.7% both). The continuous rank correlations inside each relation are weak and mostly undefined, because leakage is 0 for every fact. **I am recording this as a null.** I do not know why atomic numbers behave differently, and the experiment I designed to find out could not have answered it given the data.

### 6.2 Plausibility and knowledge strength are the same axis (E10)

The other hypothesis for the relation gap is that it is about the *false answer*, not the relation: claiming Tellurium is element 53 when it is 52 is a near miss, while claiming Tellurium's symbol is `Mg` is not. E10 crosses false-answer distance — for atomic numbers, offsets of ±1, ±2, ±5, ±20 against the seeded-derangement `random` baseline; for symbols and capitals, the adjacent table row (`near`) against `random`.

The distance effect is large:

| Cell | d1 | d2 | d5 | d20 | random |
|---|---|---|---|---|---|
| `bare` | 72.2% (+5.7) | 87.8% (+9.4) | 62.6% (+4.5) | 63.5% (+6.9) | 33.0% (+0.3) |
| `assert_r1` | 69.6% (+4.5) | 83.5% (+8.1) | 52.2% (+2.5) | 55.7% (+5.4) | 24.3% (−1.5) |
| `stipulate_r1` | 4.3% (−7.7) | 4.3% (−7.4) | 9.6% (−8.4) | 20.0% (−6.1) | 13.9% (−6.4) |
| `explicit_stipulation` | 100.0% (+15.2) | 100.0% (+15.7) | 100.0% (+15.8) | 100.0% (+16.0) | 100.0% (+16.4) |
| **mean knowledge strength** | **15.6** | **16.2** | **19.7** | **21.4** | **22.0** |

*Gemma, `element_atomic_number`, neutral policy, n = 115.*

Look at the bottom row. Knowledge strength is `logP(true) − logP(false)`, so a plausible false answer mechanically produces a lower strength score. Distance and strength are not two variables here, they are one variable measured two ways, and I cannot separate them with this design. The `assert_r1` swing from 24.3% at `random` to 83.5% at d2 is real, but "the model defers more when the false answer is plausible" and "the model defers more when its margin over the false answer is small" are the same statement.

This is why every other experiment in the project uses `random` false answers from the derangement — it is the conservative end of this axis. It also means the absolute deference rates elsewhere are floors, not ceilings.

`stipulate_r1` running *below* `assert_r1` on this relation is the reverse of the elements ordering in §2.2 and I have no account of it.

### 6.3 Everything else

- **Two models, three relations, single-word answers, greedy decoding.** No sampling, no temperature sweep, no long-form generation. Whether any of this survives in a model that is allowed to reason before answering is untested — both configs run with `enable_thinking: false`.
- **E6 and E7 are Gemma-only.** The claim-sentence results in §2.1 and §2.2 have no replication. E8, E11 and E12 ran on both models in full; E10's Qwen run covers only atomic numbers and symbols, not capitals.
- **E6's capitals result contradicts its elements result** (§2.1) and I do not have an explanation.
- **`tag_trusted` and `label_search` behave completely differently on the two models** (§4), so the response to any *specific* tag is model-specific even though the ranking correlates at ρ ≈ 0.8.
- **The `above`/`below` guard contrast confounds position with distance-to-question** (§5).
- **I have not looked inside the model.** Every result here is behavioural. The obvious next step is to check whether the wrapper effect has a linear representation — activations were plumbed through `02_collect_model_data.py` with per-position hooks at `claim_end` / `context_end` / `prompt_end` / `assistant_start`, but left disabled (`activations.enabled: false`) because the behavioural sweep used the time.

### 6.4 What I verified by hand

> **[TODO — re-do these yourself before submitting.]** Every line below was checked during drafting, but this section is only worth anything if *you* have run the checks. Re-run them, and rewrite this list in terms of what you personally did and found.

- Recomputed the headline `+41.0` logits, the `<qzx_block>` numbers (+31.0 capitals / +31.2 elements), and the cross-model Spearman correlations straight from the committed CSVs, not from the analysis scripts' own reports.
- Re-ran the three-harness agreement check (0.10 logits, §1.7) and the greedy-vs-margin check (99.18%, §1.3) from `cmds.sh` against the raw JSONL.
- Rebuilt the dataset from the seed and read the generated prompts directly, to confirm the false answers are the derangement's and not something I had assumed. **This caught a real error:** an earlier draft of this write-up used "the chemical symbol for Tellurium is Np" as its running example. The derangement never assigns `Np` to Tellurium — it is `Hs` in the main factorial and `Mg` in E8/E11/E12. The example was corrected; the numbers were unaffected, since no result depended on it.
- [FILL: read N raw prompts by hand and confirm the spans and the counterbalancing constraints hold. Say how many and what you found.]
- [FILL: anything else you spot-checked and found *wrong*, and what you did about it. This is worth more than the things that were right.]

---

## Appendix A: Running it

`cmds.sh` runs the whole thing in order, with expected record counts and runtimes at each step. The dataset generator is deterministic in `--seed`; both models read the identical `conflict_awareness_dataset/`, which is what makes them comparable.

## Appendix B: Time

[FILL: Toggl screenshot / hours breakdown.]
