---
name: spec
description: Turn the current conversation into a spec file under docs/specs/. No interview — it synthesizes what you already discussed.
---

Write a spec from the current conversation and codebase understanding. Do not interview the user. Synthesize what you already know.

## Process

1. Explore the repo if you have not already. Follow the conventions and vocabulary the code already uses.

2. Decide the seams at which the feature gets tested. A **seam** is a place where a test replaces a real part with a fake one. Prefer a seam that exists. Choose the highest seam you can. Fewer seams are better. One is ideal.

3. Write the spec to `docs/specs/<kebab-case-name>.md`. Create the directory if it does not exist. Use the template below.

4. Tell the user the path. Then give them the next command: `/implement <path>`. Do not build.

The spec is the whole brief for the build. `/implement` runs in its own scope and cannot see this conversation. Write down every decision it needs.

## Style

Write every sentence in this style. It comes from Simplified Technical English (ASD-STE100), without the controlled vocabulary.

- One idea per sentence. Keep sentences under 20 words.
- Active voice, present tense.
- One word for one meaning. Do not switch synonyms.
- Define jargon on first use.
- Say what the thing is, not what it is like.
- Prefer the short word to the long one.
- Cut words that carry no meaning.

## Template

<spec-template>

## Problem Statement

The problem the user has, from the user's view.

## Solution

The solution to that problem, from the user's view.

## User Stories

A long numbered list. Each story uses this format:

1. As an <actor>, I want <feature>, so that <benefit>

Cover every part of the feature.

## Implementation Decisions

The decisions that shape the build:

- The modules you build or change
- The interfaces you change
- Clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do not include file paths or code snippets. They go out of date fast.

Exception: include a snippet when it records a decision more exactly than prose can — a state machine, a reducer, a schema, a type shape. Keep only the parts that carry the decision.

## Testing Decisions

- What makes a good test here. Test external behaviour, not internals.
- Which modules you test.
- Similar tests that already exist in the codebase.

## Out of Scope

What this spec does not cover.

## Further Notes

Anything else the reader needs.

</spec-template>
