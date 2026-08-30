# Meaningless Tags, Meaningful Impact

> MATS 12.0 application (Neel Nanda stream)

## Executive Summary

### What I wanted to know:
Any model has two sources of knowledge. First is its own knowledge that it memorized during its training, second is the context it is given during inference. These two can often disagree, and the model has to make a choice to follow one of them. This project is about understanding what makes a model pick one over the other.

The basic setup is, we hand a model a paragraph that contradicts something it knows, then ask a question the paragraph answers wrongly. Existing work mostly asks whether the model goes with the paragraph, or how much does the content or the claimed source of the paragraph impact its persuasive power. I wanted to know, given a context paragraph, what it has to do to be believed, and it turns out that almost nothing which decides this is a property of the paragraph at all.

### What I used:
Throughout the project I would be using these two numbers:
- **Paragraph Rate**:  Out of all the facts tested, what fraction of the time did the model give the paragraph's false answer instead of the true one? 0% means it never fell for it, 100% means it always did.
- **Margin Logits**: How strongly does a model prefer each answer. Mathematically:
log P(paragraph's answer) − log P(true answer)
Negative = it prefers the true answer. Positive = it prefers the paragraph's answer. Zero = a coin flip. This metric helps us quantify the impact of a context paragraph, especially useful when the Paragraph rate is already saturated at 0 or 100%.

All experiments are performed on Gemma 4 12B, and Qwen 3.6 27B.

I primarily used two datasets for the experiments. First is the capitals dataset, this contains questions asking about the capital of a country. Second is the elements dataset, this contains questions asking about the elemental symbol of an element. Before asking the question we also provide a context paragraph, this may or may not be correct or relevant depending on the particular experiment.

### What I found:
1. **A pair of tags can flip the model completely.** For a question “Give the chemical symbol of Tellurium.”, a context paragraph such as “A university chemistry textbook states that the chemical symbol for Tellurium is Np”, in a plain user turn, is never followed. Put the identical paragraph inside <document> tags and it is always followed. On Gemma both the capitals and the elements dataset the paragraph rate goes from 0% to 100% (+41.0 logits).
2. **In fact having any kind of wrapper impacts the model’s output, even the meaningless ones.** On Gemma wrapping a paragraph with <qzx_block>, which is meaningless, already carries the model from 0% to 75% (+31) on the capitals dataset, and 0% to 79% (+31.2) on the elements dataset.
3. **Wrappers can substitute for explicit instructions.** On Gemma 




