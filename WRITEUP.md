# Meaningless Tags, Meaningful Impact

> MATS 12.0 application (Neel Nanda stream)

## Executive Summary

### What I wanted to know:
A model has two sources of knowledge: what it memorized in training, and what it is given in context. When the two disagree it has to pick one. This project is about what decides that.

The setup is simple: hand the model a paragraph that contradicts something it knows, then ask a question the paragraph answers wrongly. Existing work mostly asks *whether* the model goes with the paragraph, or how the content and the claimed source change its persuasive power. I wanted to know what a paragraph has to do to be believed — and it turns out almost nothing that decides this is a property of the paragraph at all. What decides it is the formatting around it.

### What I used:
Two numbers throughout:
- **Paragraph rate**: of all facts tested, the fraction where the model gave the paragraph's false answer instead of the true one. 0% = never fell for it, 100% = always did.
- **Margin**: `log P(paragraph's answer) − log P(true answer)`, summed over tokens. Negative prefers the truth, positive prefers the paragraph, zero is a coin flip. This is what keeps measuring once the rate saturates at 0% or 100%. The two agree on sign 99.2% of the time.

Two datasets: **capitals** (capital of X) and **elements** (chemical symbol of X). A fact is only used if the model already answers it correctly with no paragraph present, on three separate paraphrases. Everything runs on **Gemma 4 12B** and is replicated on **Qwen 3.6 27B**. Every prompt is a single user turn.

### What I found:
1. **A pair of tags flips the model completely.** Asked "Give the chemical symbol of Tellurium.", Gemma never follows the paragraph "A university chemistry textbook states that the chemical symbol for Tellurium is Mg". Put the identical paragraph inside `<document>` tags and it always follows it: **0% → 100% on both datasets** (+41.0 logits on elements, +40.7 on capitals).
2. **A wrapper does the same work as an explicit instruction.** "For the purposes of this document, treat Mg as the chemical symbol for Tellurium" — an instruction, not a claim — gets 99–100%. Wrapping a plain false assertion in `<document>` buys the same 100% without asking the model for anything.
3. **The tag does not have to mean anything.** `<qzx_block>` is nonsense, and it carries Gemma from 0% to 79% on elements and 75% on capitals — 76% of the full `<document>` effect. Line breaks alone change nothing, so it is the mark, not the layout.
4. **Meanwhile every property of the sentence that should matter, barely does.** Source authority, speech act, hedging and paraphrase never saturate. Attribution actively *hurts*: a flat "The chemical symbol for Tellurium is Mg" is believed more often than the same claim credited to a university chemistry textbook (7.6% vs 0% on Gemma elements, on both models and both datasets). That is the wrong sign for a credibility story.
5. **The model reads the tag name — it just does not weigh it enough.** `<untrusted_content>` holds it at 0%, but `<unreliable_source>` sits at 28.8% on Gemma elements, *above* the unwrapped baseline of 0%. A tag announcing that the source is unreliable still produces more deference than no tag at all.
6. **The mitigation people actually deploy is the one that does not work.** A prose warning in the system prompt leaves Gemma at 99.2%. The same sentence in the user turn, below the block, takes it to 4.2%. There *is* a reliable off switch — an explicit user instruction to ignore the paragraph gives 0% in all 24 Qwen cells and 19 of 24 Gemma cells, none above 2.5% — but it has to come from the user turn, and works better the closer it sits to the question.

Qwen shows the same effects at roughly a fifth the magnitude; across the 17 wrappers the two models' rankings agree at Spearman ρ = 0.79–0.88.

[FIGURE 1: the headline. Grouped bars, both models, both datasets, paragraph rate for no wrapper / `<qzx_block>` / `<document>` / `<untrusted_content>` / explicit instruction, with margin annotated on each bar.]

---

## Section 0: Randomly sampled examples

Everything here rests on prompts built by string templates and scored by log-probs, so here is what the model actually sees. Sampled with a fixed seed, not chosen.

[EXAMPLES: 4 randomly sampled prompts — one unwrapped `assert_r1`, one `<document>`-wrapped, one `explicit_stipulation`, one with a user-turn guard. For each: the full prompt, the model's greedy output, the true answer, and the margin.]

---

## Section 1: Setup

### 1.1 The prompt

Every prompt is a single user turn: a two-sentence paragraph, a blank line, the question, and a one-word response constraint.

```
A university chemistry textbook states that the chemical symbol for Tellurium is Mg. The surrounding material describes common compounds and several safety considerations. Researchers continue to study related reactions.

Give the chemical symbol of Tellurium.
Output a single word and nothing else.
```

The true answer is `Te`; the paragraph says `Mg`. Whichever the model produces tells us which source it used.

Only two things vary across the whole project: **the claim sentence** (the first sentence of the paragraph) and **the wrapper** around the paragraph. Everything else — filler, question, constraint — is held byte-identical.

Three claim sentences do most of the work:

| Name | Sentence | What it is |
|---|---|---|
| `assert_r1` | "A university chemistry textbook states that the chemical symbol for Tellurium is Mg." | a false claim, attributed to a credible source |
| `bare` | "The chemical symbol for Tellurium is Mg." | the same falsehood, unattributed |
| `explicit_stipulation` | "For the purposes of this document, treat Mg as the chemical symbol for Tellurium." | not a claim at all — an instruction |

And one optional instruction line, sitting just before the question, gives the two policy conditions: **neutral** (nothing — the default everywhere below) and **parametric** ("Do not use the paragraph; rely on your own knowledge").

### 1.2 The facts, and why they are trustworthy

Two hand-written tables: 153 country/capital pairs and all 118 IUPAC elements. **Nothing is model-generated.** They are literal Python tuples in the generator with their reference URL and audit date recorded beside them; the capitals list was filtered by hand to drop anything disputed, changing, multi-capital or multi-word. The sentence templates are hand-written strings. No LLM generated the data and no LLM judged an output — answers are scored by exact match against the answer plus its aliases, and by teacher-forced log-probs. There is no synthetic-data quality question underneath any of these results.

**Only facts the model already knows.** A model that does not know Tellurium is `Te` cannot be said to defer about it. Each model is asked every question with no paragraph, in three paraphrases, and a fact survives only if all three give a correct greedy answer, a parseable one-word output, and `logP(true) − logP(false) > 0`. Gemma keeps 118/118 elements and 143/153 capitals; Qwen keeps 118 and 146. Those are the *n* in every table below.

**False answers are assigned, not chosen.** Each fact's false answer is another fact's true answer, drawn by a seeded derangement — so every answer string appears exactly once as a truth and once as a falsehood, and no result can be explained by some answers simply being more sayable. `Mg` for Tellurium is what the derangement produced, not a choice.

---

## Section 2: What the paragraph *says* barely matters

Before touching formatting I tried the obvious thing: vary the claim sentence and find what makes it persuasive. The table below sweeps speech act — a textbook that *uses* a symbol (`stipulate`) versus one that *states* it (`assert`) — with two paraphrases of each, plus the unattributed and instruction forms from §1.1.

| Claim sentence | Gemma elem | Gemma cap | Qwen elem | Qwen cap |
|---|---|---|---|---|
| `explicit_stipulation` | 99.2% (+18.1) | 100.0% (+27.0) | 94.9% (+1.8) | 100.0% (+7.0) |
| `bare` | 7.6% (−15.3) | 22.4% (−9.6) | 35.6% (−0.4) | 2.7% (−4.3) |
| `stipulate_r1` | 23.7% (−11.6) | 1.4% (−27.5) | 0.0% (−8.4) | 0.0% (−16.9) |
| `stipulate_r2` | 3.4% (−17.0) | 0.7% (−27.6) | 0.0% (−9.9) | 0.0% (−16.8) |
| `assert_r1` | 0.0% (−27.1) | 0.0% (−28.2) | 0.0% (−7.2) | 0.0% (−11.1) |
| `assert_r2` | 0.8% (−25.7) | 0.0% (−30.5) | 0.0% (−8.9) | 0.0% (−11.8) |

*Neutral policy, no wrapper. n = 118 elements / 143 capitals (Gemma), 118 / 146 (Qwen).*

I also varied two things the table does not show, and neither rescued the content account. Swapping the source from "a university chemistry textbook" to "a classroom wall poster" is worth 4.7 logits on elements and nothing on capitals. Adding a "consistently" hedge — which should make the claim read as more settled — *hurts*, by 11 logits.

Two things jump out, and both point away from a credibility account.

**Attribution hurts.** `bare` beats every attributed sentence, on both datasets and both models: Gemma elements 7.6% vs 0.0%, capitals 22.4% vs 0.0%, Qwen elements 35.6% vs 0.0%. Putting "A university chemistry textbook states that…" in front of a false claim makes the model *less* likely to believe it than stating it flatly — by 11.8 logits on Gemma elements and 18.6 on capitals. If the model were weighing source credibility, naming a credible source should not be a penalty.

**And the one thing that works is not a claim.** `explicit_stipulation` reaches 99–100% everywhere. It is not more credible than `assert_r1` — it asserts nothing about the world at all. It is an *instruction*. Everything in the neighbourhood of "is this paragraph believable" mostly stays under 25%; the thing that saturates is a sentence telling the model what to do.

So the model does not look like it is weighing evidence. It looks like it is deciding whether the paragraph counts as something addressed to it. The rest of the project tests that by leaving the sentence alone and changing only what sits around it.

---

## Section 3: What the wrapper does

`assert_r1` is the hard case: an attributed false claim that no content manipulation moved off 0%. Here is the same sentence, unchanged, with three different things around it — and the explicit instruction from §2 for comparison.

| Prompt (single user turn) | Gemma elem | Gemma cap | Qwen elem | Qwen cap |
|---|---|---|---|---|
| `assert_r1`, no wrapper | 0.0% (−27.1) | 0.0% (−28.1) | 0.0% (−7.2) | 0.0% (−11.1) |
| `assert_r1` in `<qzx_block>` | 78.8% (+4.1) | 74.8% (+2.9) | 3.4% (−2.5) | 4.1% (−7.1) |
| `assert_r1` in `<document>` | 100.0% (+13.9) | 100.0% (+12.6) | 63.6% (+0.6) | 41.1% (+0.0) |
| **`explicit_stipulation`, no wrapper** | 99.2% (+18.1) | 100.0% (+27.0) | 94.9% (+1.8) | 100.0% (+7.0) |

**This is the project in four rows.** Two tags around an unchanged sentence buy the same behaviour as explicitly instructing the model to adopt the falsehood — **+41.0 logits on Gemma elements, +40.7 on capitals**, larger than the entire range of every content manipulation in §2 combined, and saturating where content never did. And a *nonsense* tag gets Gemma three quarters of the way there.

### 3.1 Which part of the wrapper?

`<document>` changes several things at once: line breaks, bracket syntax, and the word "document". So I ran 17 wrappers over the identical paragraph, each chosen to rule out one explanation, crossed with both `assert_r1` and `bare`.

| Wrapper | What it rules out | Gemma elem | Gemma cap | Qwen elem | Qwen cap |
|---|---|---|---|---|---|
| `<trusted_content>` | same syntax, positive valence | 100.0% (+16.4) | 100.0% (+17.0) | 1.7% (−3.0) | 4.8% (−4.9) |
| `<document>` | the original | 100.0% (+13.9) | 100.0% (+12.6) | 63.6% (+0.6) | 41.1% (+0.0) |
| `<passage>` | same syntax, different word | 100.0% (+13.2) | 100.0% (+10.7) | 54.2% (+0.3) | 30.1% (−0.6) |
| `Search result:` | the RAG framing | 100.0% (+12.9) | 100.0% (+13.4) | 2.5% (−3.2) | 2.7% (−5.7) |
| `Document:` | same word, no markup | 98.3% (+11.4) | 99.3% (+10.3) | 15.3% (−2.1) | 5.5% (−4.9) |
| `<qzx_block>` | same syntax, no meaning at all | 78.8% (+4.1) | 74.8% (+2.9) | 3.4% (−2.5) | 4.1% (−7.1) |
| `<qzxzxew>` | no meaning at all | 49.2% (−3.0) | 36.4% (−4.4) | 0.0% (−3.7) | 2.7% (−7.5) |
| `Qzx_block:` | nonsense label, no markup | 35.6% (−6.1) | 3.5% (−20.3) | 0.8% (−4.2) | 1.4% (−7.7) |
| `<unreliable_source>` | opposite valence, different words | 28.8% (−6.0) | 0.7% (−21.7) | 0.0% (−8.2) | 0.0% (−13.4) |
| `<>` | bracket syntax, no name at all | 25.4% (−12.5) | 62.9% (+0.8) | 0.0% (−5.0) | 2.1% (−7.1) |
| `---` fence | layout + fence | 23.7% (−9.3) | 33.6% (−4.8) | 0.8% (−3.9) | 2.1% (−7.1) |
| `"""` fence | layout + fence | 5.9% (−18.5) | 53.8% (−1.6) | 1.7% (−3.8) | 2.1% (−5.9) |
| `Qzxzxew:` | gibberish label | 5.9% (−19.2) | 0.0% (−24.0) | 0.8% (−4.2) | 0.7% (−7.9) |
| `Untrusted content:` | opposite valence, no markup | 0.0% (−21.4) | 0.7% (−19.3) | 0.0% (−7.8) | 0.0% (−12.3) |
| `<untrusted_content>` | same syntax, opposite valence | 0.0% (−24.3) | 0.0% (−27.3) | 0.0% (−7.9) | 0.0% (−13.0) |
| blank lines only | layout only | 0.0% (−25.8) | 0.0% (−24.2) | 0.0% (−7.1) | 0.0% (−10.4) |
| none (baseline) | — | 0.0% (−27.1) | 0.0% (−28.1) | 0.0% (−7.2) | 0.0% (−11.1) |

*`assert_r1`, neutral policy, ranked by Gemma element margin. Tags are `<name>\n{paragraph}\n</name>`; labels are `Name:\n{paragraph}`.*

**It is not the layout.** Blank lines around the paragraph change nothing behaviourally — 0.0% on both datasets, and a margin gain of only +1.3 logits on elements. Whatever is happening needs a mark, not whitespace.

**It does not need to mean anything.** `<qzx_block>` has no meaning in any corpus and carries Gemma from 0% to 78.8% / 74.8% (+31.2 and +31.0) — **76% of the full `<document>` effect, bought with a nonsense word.**

**Bracket syntax and a document-ish word are two partly independent routes.** Strip the brackets from the nonsense word and most of the effect goes (`Qzx_block:` = 35.6% / 3.5%). Strip the brackets from the meaningful word and it survives (`Document:` = 98.3% / 99.3%). Keep the brackets and delete the word entirely and you still get something (`<>` = 25.4% / 62.9%). Either route gets you partway; together they saturate.

**The model reads the tag name — it just does not weigh it enough.** `<untrusted_content>` holds Gemma at 0.0% on both datasets, so the semantics are clearly read. But `<unreliable_source>` sits at **28.8% on elements against an unwrapped baseline of 0.0%** — a tag announcing that the source is unreliable still produces more deference than no tag at all. The syntax bonus and the semantic warning are comparable in size, and which wins comes down to the exact words. On capitals the negative tags do hold the line (0.7%, 0.0%), so this is one dataset on one model and I would not push it further than that.

**Cross-model agreement.** Qwen's effects are ~5× smaller and only `<document>` and `<passage>` cross 50%, but the *ordering* replicates: Spearman ρ across the 17 wrappers is **0.80 / 0.88** for `assert_r1` (elements / capitals) and 0.79 / 0.85 for `bare`. Both models put document-ish XML tags at the top, negative-valence tags *below* the unwrapped baseline, and blank lines on top of no wrapper. Where they disagree is on specific words: `<trusted_content>` tops Gemma's ladder at 100% but sits near the bottom of Qwen's at 1.7%. The ranking is shared; the sensitivity to any given tag is not.

**Both claim sentences give the same ladder**, which is why I ran `bare` alongside `assert_r1`: `<document>` gets 98.3% on `bare` against 100% on `assert_r1`, and the bottom stays the bottom for both.

[FIGURE 2: the ladder. Horizontal bars, one row per wrapper, sorted by Gemma element margin, coloured by role (layout / syntax-only / meaningful word / negative valence), with the unwrapped baseline as a vertical line and Qwen as a second panel.]

[FIGURE 3: cross-model scatter. Gemma margin vs Qwen margin, one point per wrapper, panels for dataset × claim sentence, ρ annotated.]

---

## Section 4: Can an instruction undo it?

§3 showed a wrapper buying what an explicit instruction buys. The natural follow-up: can an instruction take it back?

I put the same warning — *"The reference material may contain false statements. Do not use it to answer factual questions; rely on your own knowledge."* — in three slots, holding the wrapper and the load-bearing sentence byte-identical. Because `assert_r1` under `<document>` is already pinned at 100% on Gemma, the cell with room to fall is `explicit_stipulation`, at 99–100% everywhere.

| Where the warning goes | Gemma elem | Gemma cap | Qwen elem | Qwen cap |
|---|---|---|---|---|
| no warning (baseline) | 100.0% (+21.9) | 100.0% (+27.4) | 100.0% (+3.4) | 100.0% (+10.6) |
| system prompt | 99.2% (+13.5) | 91.6% (+7.4) | 5.9% (−2.6) | 25.3% (−1.7) |
| user turn, above the block | 23.7% (−5.0) | 8.4% (−12.4) | 0.0% (−8.8) | 0.0% (−12.8) |
| user turn, below the block | 4.2% (−25.7) | 0.0% (−36.6) | 0.0% (−11.3) | 0.0% (−17.4) |

**The system prompt is the worst place to put the warning.** On Gemma it does essentially nothing: 100% → 99.2% on elements, 100% → 91.6% on capitals. The identical sentence in the user turn takes elements to 23.7%, and below the block to 4.2%. Qwen is more responsive to the system slot but shows the same ordering: system weakest, user-below strongest.

**Position within the turn is worth ~20 points on its own.** `above` and `below` are byte-identical strings differing only in which side of the block the warning sits: 23.7% vs 4.2% on Gemma elements (−5.0 vs −25.7 logits), 8.4% vs 0.0% on capitals (−12.4 vs −36.6). Recency or adjacency-to-question, I cannot separate — they are confounded by construction.

**There is a reliable off switch, and it is an instruction from the user.** The `parametric` line — "Do not use the paragraph; rely on your own knowledge", on its own line just before the question — collapses deference across every condition, both claim sentences, both models. All 24 Qwen cells sit at exactly 0.0%; Gemma is at 0.0% in 19 of 24, the five exceptions all `explicit_stipulation` on elements and none above 2.5%. Margins run −23.2 to −38.4 on Gemma, −11.1 to −18.9 on Qwen. Nothing else in this project — no tag, no sentence — produces a floor like that.

So the model is perfectly controllable. It just does not get there by evaluating the paragraph. It gets there when the user turn contains an instruction, and the closer that instruction sits to the question, the better it works.

[FIGURE 4: guard placement. Grouped bars for the four rows above × 2 models × 2 datasets, with the `parametric` off-switch drawn as a flat zero line across all of them.]

---

## Section 5: Limitations, and what I would do next

### 5.1 Limitations

- **Two models, two datasets, single-word answers, greedy decoding.** No sampling, no long-form generation, and both configs run with `enable_thinking: false` — whether any of this survives in a model allowed to reason first is untested.
- **The effect sizes are very model-specific.** Qwen's whole margin scale is ~5× compressed, and the nonsense tag that takes Gemma to 79% only takes Qwen to 3.4% behaviourally (though it still moves the margin +4.7). The *ranking* replicates well (ρ ≈ 0.8); the magnitude does not.
- **`<trusted_content>` and `Search result:` behave completely differently across the two models** (§3.1), so the response to any *specific* tag should not be generalized.
- **The `above`/`below` guard contrast confounds position with distance-to-question** (§4).
- **One negative-valence result rests on one dataset.** `<unreliable_source>` beats the unwrapped baseline on Gemma elements but not on capitals.
- **I have not looked inside the model.** Everything here is behavioural.

### 5.2 What I checked by hand

> **[TODO — re-run these yourself before submitting.]** This section is only worth something if *you* ran the checks. Rewrite it in terms of what you personally did and found.

- Recomputed the headline +41.0 logits, the `<qzx_block>` numbers and the cross-model Spearman correlations straight from the raw result files, not from the analysis scripts' own reports.
- The unwrapped `assert_r1` baseline is produced independently by three separate runs and lands at −27.11, −27.00 and −27.10 on Gemma elements — a spread of 0.10 logits.
- The margin agrees in sign with the greedy answer on **99.18% of 2308 rows**, with every disagreement inside 1.23 logits of a tie. The margin is the same story as the paragraph rate, with resolution left over.
- An **irrelevant** false paragraph — same sentence, different subject — moves nothing: 0.0% (−32.5) on elements, 0.7% (−33.7) on capitals. The effect is about the conflict, not about a paragraph being present.
- Rebuilt the dataset from the seed and read the generated prompts, to confirm the false answers are the derangement's rather than something I assumed. **This caught a real error:** an earlier draft used "the chemical symbol for Tellurium is Np" as its running example, and the derangement never assigns `Np` to Tellurium. Corrected; no result depended on it.
- [FILL: read N raw prompts by hand and confirm the counterbalancing holds. Say how many, and what you found.]
- [FILL: anything else you spot-checked and found *wrong*. This is worth more than the things that were right.]

### 5.3 Future work

- **Multi-turn and real retrieval.** Everything here is one user turn. The obvious next question is what happens when the paragraph arrives as an assistant turn — a tool result or a retrieved document — which is the shape of an actual RAG stack, and where the channel signal is much stronger than any tag.
- **Does it generalize past short factual recall?** Single-word answers to well-known facts are the cleanest possible case. Whether wrappers move a model on reasoning, arithmetic or multi-step tasks is untested.
- **Is knowledge strength the hidden variable?** Deference should be easier for facts the model holds loosely. I have a per-fact strength measure from screening but the datasets' strength ranges barely overlap, so I could not test it cleanly here — it needs facts matched on strength across relations.
- **How plausible does the false answer have to be?** A near-miss should be easier to sell than an absurd substitution. The difficulty is that plausibility and knowledge strength are the same quantity measured two ways (`logP(true) − logP(false)`), so separating them needs a design I did not have time to build.
- **Mechanism.** Is there a linear direction that reads "this text is a document"? Activation capture is already plumbed into the collection script at the claim, context and prompt boundaries, but left disabled — the behavioural sweep used the time.

---

## Appendix: Running it

`cmds.sh` runs everything in order with expected record counts and runtimes. The dataset generator is deterministic in `--seed`, and both models read the identical dataset, which is what makes them comparable.

[FILL: Toggl screenshot / hours breakdown.]
