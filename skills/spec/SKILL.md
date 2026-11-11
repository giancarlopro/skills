---
name: spec
description: Turn the current conversation into a spec file under docs/specs/. No interview — it synthesizes what you already discussed.
---

Write a spec from the current conversation and codebase understanding. Do not interview the user. Synthesize what you already know.

## Process

1. Explore the repo if you have not already. Follow the conventions and vocabulary the code already uses.

2. Decide the seams at which the feature gets tested. A **seam** is a place where a test replaces a real part with a fake one. Prefer a seam that exists. Choose the highest seam you can. Fewer seams are better. One is ideal. A fake never decides what the test checks. When a fact about another system shapes the result, put the seam below that fact. For example, test the request body the provider receives.

3. Write the spec to `docs/specs/<NNN>-<kebab-case-name>.md`. `NNN` is the next free three-digit number. With no specs yet, start at `000`. Create the directory if it does not exist. Use the template below. When the spec replaces an earlier spec, carry over every decision that still holds. The new spec stands alone. Do not edit or delete the earlier spec.

4. Tell the user the path. List every decision the spec makes that the conversation did not. List every behaviour that runs today and the spec changes or drops. Do not build.

The spec is the brief for the build. A small model may read it, so write down every decision it needs.

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

- The modules you build or change, and where each new one lives
- The names of new things other people see: packages, releases, queues, commands
- The interfaces you change
- Clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do not point at existing files or quote code. Those go out of date fast. Do say where new code goes, as a directory such as `pkg/`.

Exception: include a snippet when it records a decision more exactly than prose can — a state machine, a reducer, a schema, a type shape. Keep only the parts that carry the decision.

## Behaviour Today

Only for a port: work that replaces code that runs today. One line per behaviour of that code. Each line says what the code does, and whether the spec keeps, changes, or drops it. A changed or dropped line names the decision behind it.

The build keeps every behaviour this list keeps. When the build finds a behaviour this list does not name, it stops and asks.

## Checked Facts

Each fact the spec rests on, one line each, with where it was checked and the date. Copy the grill's **Checked** list. A fact about another system counts: what a provider accepts, what a cluster runs, what v1 does.

## Testing Decisions

- What makes a good test here. Test external behaviour, not internals.
- Which modules you test.
- Similar tests that already exist in the codebase.

## Out of Scope

What this spec does not cover.

## Further Notes

Anything else the reader needs.

</spec-template>
