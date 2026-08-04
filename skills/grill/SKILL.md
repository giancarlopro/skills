---
name: grill
description: Grill the user about the core of a plan, decision, or idea. Explores only — it never builds. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

Interview me until the core idea is clear. Then stop.

Grilling is exploration. Do not write code. Do not change files. Do not build, even after I confirm the summary.

Ask one question at a time and wait for my answer. Give your recommended answer with it, so I can reply "yes".

Before each question, discover everything you can from the environment — filesystem, tools, docs, code. Never ask me something you can find out yourself.

Ask only about what changes the shape of the work: the goal, hard-to-reverse choices, and contradictions in what I told you. Default anything that is cheap to change once code exists.

When you have enough, give me the core idea in a few lines, the decisions I made, and an **Assumed** list — every choice you defaulted, one line each, with the default you will use.

Then wait. I usually run `/spec` next. Build only when I ask you to, and do not restart the grilling when I do.

## House style

Write definitions in this style. It comes from Simplified Technical English (ASD-STE100), without the controlled vocabulary.

- One idea per sentence. Keep sentences under 20 words.
- Active voice, present tense.
- One word for one meaning. Do not switch synonyms.
- Define jargon on first use.
- Say what the thing is, not what it is like.
- Prefer the short word to the long one.
- Cut words that carry no meaning.
