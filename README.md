# Skills

My personal skills for everyday development using AI.

The repo is the source of truth. I symlink it into whichever agent I use, so the skills travel with me. Each `SKILL.md` is plain Markdown with `name` and `description` only.

`lazy` breaks that rule on purpose. It pins its own model, so it carries three Claude Code keys: `model`, `effort`, and `argument-hint`. An agent ignores keys it does not know, so `lazy` still runs elsewhere — on whatever model that agent already uses. The pin degrades. The skill does not break.

## Install

```sh
rm -f ~/.claude/skills && ln -s /home/gian/skills/skills ~/.claude/skills
```

The `rm -f` matters. If `~/.claude/skills` already exists, plain `ln -s` links *into* it and creates a nested `skills/skills` instead of replacing the link. `rm -f` deletes a symlink but refuses to delete a real directory, so it cannot destroy skills that live there for real.

## Skills

Two of these pair up. Two stand alone.

- **grill** — interviews me until the core idea is clear, then summarises and waits. Asks one question at a time, discovers facts itself, and defaults anything cheap to change. Ends with an **Assumed** list of every default it took. I change defaults and it summarises again; I confirm and it runs `/spec`.
- **spec** — turns the conversation into a spec at `docs/specs/<name>.md`. No interview, no issue tracker, no setup step. It reports the path and stops.
- **lazy** — builds what a spec describes, on a small model. I invoke it when I want the build done cheaply.
- **create-sandbox** — writes a `.devcontainer/` that runs Claude with permission checks off, behind a deny-by-default firewall. It interviews me the way `grill` does, shows its decisions, and waits before writing.

All four use one house style, taken from Simplified Technical English (ASD-STE100) without its controlled vocabulary: one idea per sentence, active voice, one word for one meaning. Shorter specs cost fewer tokens and leave a smaller model less room to guess.

## Models

The interview needs the best model. The build does not always.

`grill`, `spec`, and `create-sandbox` carry no `model` key. They run on the session model, which is my best one.

`lazy` sets `model: sonnet`. Claude Code switches the main loop to that model for the run, then returns to the session model on my next message. I switch nothing by hand.

That pin is why `lazy` is its own step rather than the tail of `/spec`. Some specs deserve the big model and some do not, and only I know which. So `/spec` stops at the path. If I want the cheap build, I type `/lazy`. If I want the good one, I build in the main chat and never invoke it.

Before `/lazy`, I run `/compact`. The build stays in the main chat, so it inherits the conversation that produced the spec. Compaction clears the interview, and the small model reads a short definition instead of a long argument.

The build stays in the main chat for a reason. It prompts me for permission like any other work. A forked skill cannot — Claude Code suppresses a fork's prompts, so a forked build cannot run the tests it just wrote. That rules the fork out, at the cost of a shared context.

## Sandboxing

`create-sandbox` exists so I can turn permission checks off without turning safety off.

It reads the project, reuses the image the project already has, and detects whether that image runs as root. Root matters: Claude Code refuses bypass mode as root unless `IS_SANDBOX=1` is set.

It enables bypass mode in both places I start Claude. The VSCode extension needs two settings keys. The container shell needs a `--dangerously-skip-permissions` alias. Setting one and not the other still leaves me answering prompts.

The container denies network egress by default and allows a short list of hosts. That is the part that makes the trade sound — the flag's own warning says to use it only without open internet. A script inside the container drops the rules when a one-off task needs them gone, with no rebuild.

It mounts one file from the host: `~/.claude/.credentials.json`, read-write, so token refresh survives. Nothing else from `~/.claude` goes in. A permission-free Claude does not get my other projects' transcripts.

## Goals

`grill`, `spec`, and `lazy` are simplifications of Matt Pocock's skills. His versions are excellent but slow to produce a result, so mine trade depth for speed.

- `grill` replaces the exhaustive decision-tree walk with the questions whose answers change the shape of the work.
- `spec` keeps every section of his template and cuts the prose, rather than cutting content.
- `lazy` moves the build off the best model, because a spec that is clear enough does not need one.

Matt's originals stay installed. When a decision deserves fifty questions, `/grill-me` is still there.
