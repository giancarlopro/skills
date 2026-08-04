# Skills

My personal skills for everyday development using AI.

The repo is the source of truth. I symlink it into whichever agent I use, so the skills travel with me. Each `SKILL.md` is plain Markdown with `name` and `description` only — no agent-specific keys.

## Install

```sh
ln -s /home/gian/skills/skills ~/.claude/skills
```

## Skills

The usual flow is `/grill`, then either `/spec` or a build.

- **grill** — interviews me until the core idea is clear, then summarises and waits. Asks one question at a time, discovers facts itself, and defaults anything cheap to change. Ends with an **Assumed** list of every default it took. I change defaults and it summarises again; I confirm and it builds; I ask for a spec and it runs `/spec`.
- **spec** — turns the conversation into a spec at `docs/specs/<name>.md`. No interview, no issue tracker, no setup step.

Both use one house style, taken from Simplified Technical English (ASD-STE100) without its controlled vocabulary: one idea per sentence, active voice, one word for one meaning. Shorter specs cost fewer tokens and leave a smaller model less room to guess.

## Goals

These are simplifications of Matt Pocock's skills. His versions are excellent but slow to produce a result, so mine trade depth for speed.

- `grill` replaces the exhaustive decision-tree walk with the questions whose answers change the shape of the work.
- `spec` keeps every section of his template and cuts the prose, rather than cutting content.

Matt's originals stay installed. When a decision deserves fifty questions, `/grill-me` is still there.
