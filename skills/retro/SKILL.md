---
name: retro
description: Read past Claude Code transcripts, find where the user corrected the agent, trace each correction to a line in a skill from this repo, and write a report with proposed edits. Use when the user wants a retrospective on their skills, or asks why the same mistake keeps happening.
---

Find the corrections the user made in past sessions. Trace each one to a skill. Propose an edit. Write a report and wait.

Until the user picks findings, change no skill file.

**This repo** is the repo that holds this skill. Resolve the skill directory's symlinks with `realpath`. The repo is two directories up. The user can run `/retro` from any project, so do not use the current directory.

A **transcript** is the JSONL file Claude Code saves for each session, under `~/.claude/projects/`. A **target skill** is a directory in this repo's `skills/` directory, except `synced/`.

## Process

1. Collect the skip list.
2. Run the extract script.
3. Read the target skills.
4. Classify each turn.
5. Group the corrections.
6. Write the report.
7. Stop at the gate.

## 1. Collect the skip list

Read every report in `docs/retros/` in this repo. Collect the session IDs from each **Sessions read** section. These sessions are already read. Skip them.

No reports yet means no skip list.

## 2. Run the extract script

`extract.py` sits beside this file. It uses Python 3 and the standard library only.

```sh
python3 <skill-dir>/extract.py --skip <id>,<id>,... > <scratchpad>/retro.json
```

Write the output to a file. It can be large. Read it in parts.

The output lists each session that invoked a target skill. Each session holds its `id`, `project`, `date`, `skills`, and `turns`. A **turn** is one user message with the agent text before it. `interrupted` is true when the user stopped the agent mid-turn.

The script already drops bare confirmations such as "yes". It drops subagent lines, tool results, and skill bodies.

No sessions means nothing to do. Say so and stop.

## 3. Read the target skills

Read every target `SKILL.md` before you trace a cause. Trace to the current text, not the text at session time.

## 4. Classify each turn

Sort each turn into one kind:

- **Answer**: a reply to a question the agent asked. Not a finding.
- **Correction**: a message that rejects or fixes what the agent just did or said.
- **Instruction**: a new request. Not a finding.

Answers and corrections look alike. "No, use X" after a question is an answer. It is a correction only when the agent had already stated a choice. A rejected recommendation counts only when the recommendation broke a rule in the skill.

For each correction, decide the cause:

- **Skill**: a line in a target skill caused it, or a missing line would have prevented it.
- **Elsewhere**: a project fact, a plain coding slip, or anything no skill line controls.

A correction during a main-chat build counts when the spec left the decision out. Then the cause is the `spec` skill.

Facts that belong in a project `CLAUDE.md` or in memory are Elsewhere.

## 5. Group the corrections

Group the skill corrections that share one cause.

- A **pattern** is a group with corrections from two or more sessions.
- A **one-off** is a group from one session.

## 6. Write the report

Write the report to `docs/retros/<YYYY-MM-DD>.md` in this repo. Create the directory if it does not exist. If the file exists, append `-2`, `-3`, and so on.

Sections, in order:

1. **Summary**: counts of sessions read, corrections found, patterns, and one-offs.
2. **Patterns**: one entry per pattern, most sessions first.
3. **One-offs**: one entry per one-off.
4. **Elsewhere**: one line per correction, with a short reason. No proposed edit.
5. **Sessions read**: one line per session, as `` `<id>` — <project>, <date> ``. List every session the script returned, with or without findings.

Number the entries across Patterns and One-offs. Each entry holds:

- A one-line title
- The target skill and the line it traces to, quoted. For a missing line, the section where the new line goes.
- Each correction quoted, with its session ID and date
- The proposed edit, as the old line and the new line

Write the proposed edits in the house style below.

## 7. Stop at the gate

Print the report path and a short list of the numbered findings. Then stop.

The user answers in one of three ways:

- **Picks findings by number.** Apply those edits to the `SKILL.md` files. Mark them applied in the report. Mark the rest rejected.
- **Changes a proposed edit.** Update the report. Print the list again and wait again. Repeat as often as the user needs.
- **Rejects all.** Change no skill file. Mark every finding rejected in the report.

Do not commit. Report which files you changed.

## Transcript expiry

Claude Code deletes transcripts older than `cleanupPeriodDays` in `~/.claude/settings.json`. The default is 30.

On each run, read the setting. If it is missing or under 90, warn in your closing message. Recommend 365.

## House style

Write definitions in this style. It comes from Simplified Technical English (ASD-STE100), without the controlled vocabulary.

- One idea per sentence. Keep sentences under 20 words.
- Active voice, present tense.
- One word for one meaning. Do not switch synonyms.
- Define jargon on first use.
- Say what the thing is, not what it is like.
- Prefer the short word to the long one.
- Cut words that carry no meaning.
