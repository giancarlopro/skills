# Skills

My personal skills for everyday development using AI.

The repo is the source of truth. I symlink it into whichever agent I use, so the skills travel with me. Each `SKILL.md` is plain Markdown with `name` and `description` only.

`implement` breaks that rule on purpose. It pins its own model, so it carries three Claude Code keys: `model`, `effort`, and `argument-hint`. An agent ignores keys it does not know, so `implement` still runs elsewhere — on whatever model that agent already uses. The pin degrades. The skill does not break.

## Install

```sh
rm -f ~/.claude/skills && ln -s /home/gian/skills/skills ~/.claude/skills
```

The `rm -f` matters. If `~/.claude/skills` already exists, plain `ln -s` links *into* it and creates a nested `skills/skills` instead of replacing the link. `rm -f` deletes a symlink but refuses to delete a real directory, so it cannot destroy skills that live there for real.

## Skills

The flow is `/grill`, then `/spec`, then `/implement`.

- **grill** — interviews me until the core idea is clear, then summarises and waits. Asks one question at a time, discovers facts itself, and defaults anything cheap to change. Ends with an **Assumed** list of every default it took. I change defaults and it summarises again; I confirm and it runs `/spec`.
- **spec** — turns the conversation into a spec at `docs/specs/<name>.md`. No interview, no issue tracker, no setup step.
- **implement** — builds what the spec describes, then reports.

All three use one house style, taken from Simplified Technical English (ASD-STE100) without its controlled vocabulary: one idea per sentence, active voice, one word for one meaning. Shorter specs cost fewer tokens and leave a smaller model less room to guess.

## Models

The interview needs the best model. The build does not. So each step pins what it needs.

`grill` and `spec` carry no `model` key. They run on the session model, which is my best one.

`implement` sets `model: sonnet`. Claude Code switches the main loop to that model for the run, then returns to the session model on my next message. I switch nothing by hand.

The build stays in the main chat, so it prompts me for permission like any other work. A forked skill cannot. Claude Code suppresses a fork's prompts, so a forked build cannot run the tests it just wrote. That rules the fork out, at the cost of a shared context.

The shared context is why `/spec` asks for `/compact` first. The spec file is the brief, and `/grill` always ends at one. Compaction clears the interview that produced it, so the small model reads a short definition instead of a long argument.

## Goals

These are simplifications of Matt Pocock's skills. His versions are excellent but slow to produce a result, so mine trade depth for speed.

- `grill` replaces the exhaustive decision-tree walk with the questions whose answers change the shape of the work.
- `spec` keeps every section of his template and cuts the prose, rather than cutting content.
- `implement` moves the build off the best model, because a spec that is clear enough does not need one.

Matt's originals stay installed. When a decision deserves fifty questions, `/grill-me` is still there.
