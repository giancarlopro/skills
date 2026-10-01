# retro

## Problem Statement

`grill` and `spec` make me faster. But they repeat the same mistakes across sessions.

When a skill gets something wrong, I interrupt and say exactly what is wrong. The fix holds for that session only. It never reaches the `SKILL.md`, so the next session makes the same mistake.

I do not remember every correction I made. The corrections live in old conversations I never reopen.

Claude Code saves every session as a **transcript**: a JSONL file under `~/.claude/projects/`. So the corrections are on disk. But Claude Code deletes transcripts after 30 days by default, so the record expires.

## Solution

A `retro` skill.

I run `/retro` when I want. It reads the transcripts of sessions that used a skill from this repo. It finds the messages where I corrected the agent. It traces each correction to a line in a skill and proposes an edit to that line.

It writes the findings to a report in this repo and stops. I pick the findings I want. It applies those edits to the `SKILL.md` files. It does not commit.

Each report records which sessions it read. The next run skips them.

A one-time settings change keeps transcripts for a year, so the record lasts long enough to mine.

## User Stories

1. As a developer, I want to run `/retro` at any time, so that I review my skills when it suits me.
2. As a developer, I want the skill to read saved transcripts, so that corrections from past sessions count.
3. As a developer, I want transcripts from every project read, so that a mistake in any repo reaches the skill.
4. As a developer, I want only sessions that used a skill from this repo read, so that unrelated sessions add no noise.
5. As a developer, I want subagent transcripts left out, so that only my own messages count.
6. As a developer, I want the skill to find my corrections without interrupt markers, so that plain "no, that is wrong" messages count.
7. As a developer, I want answers to interview questions kept apart from corrections, so that "yes" and normal answers are not findings.
8. As a developer, I want each correction shown next to the agent message before it, so that I see what I corrected.
9. As a developer, I want each finding traced to a skill and a line, so that I know exactly what to change.
10. As a developer, I want a proposed edit for each finding, so that I accept a change instead of writing one.
11. As a developer, I want corrections in a main-chat build traced to the spec, so that spec gaps get fixed.
12. As a developer, I want repeated corrections ranked first, so that patterns get fixed before one-off slips.
13. As a developer, I want one-off corrections in a separate section, so that I can still see them.
14. As a developer, I want corrections that no skill caused listed briefly, so that I know the skill saw them.
15. As a developer, I want a quote and a session ID with each finding, so that I can check the evidence.
16. As a developer, I want the report saved in this repo, so that the reason for each skill change stays on record.
17. As a developer, I want the skill to stop after the report, so that nothing changes before I choose.
18. As a developer, I want to pick which findings to apply, so that I reject the ones I disagree with.
19. As a developer, I want the skill to report again after I change my picks, so that I see the final set before edits.
20. As a developer, I want the edits written in the house style, so that the skills stay consistent.
21. As a developer, I want the skill to leave commits to me, so that I review the diff first.
22. As a developer, I want sessions from earlier reports skipped, so that one correction is not counted twice.
23. As a developer, I want transcripts kept for a year, so that corrections do not expire before I mine them.
24. As a developer, I want `retro` in the README, so that the skill list stays complete.

## Implementation Decisions

### The skill file

Build one skill at `skills/retro/SKILL.md`.

The frontmatter carries `name` and `description` only. It carries no `model` key. The skill runs on the session model, the same as `grill`.

The repo installs skills through a symlink from `~/.claude/skills`. The new directory needs no install step.

The skill file follows the house style in `skills/grill/SKILL.md`. It ends with the same House style section as the other skills.

### The target skills

The **target skills** are the skills in this repo's `skills/` directory. The `synced/` directory is not a target. It holds skills synced from elsewhere.

`grill` and `spec` are the focus. `lazy` and `create-sandbox` count when a session used them. The developer does not use `lazy` yet.

### The extract script

A script pulls the evidence out of the transcripts. The model reads the script's output, not the raw transcripts. Transcripts are large, and most of their lines are tool results.

The script lives in the skill directory as `extract.py`. It uses Python 3 and the standard library only.

Input:

- The transcripts root. Default: `~/.claude/projects`.
- The target skill names. Default: every directory name in the skill's parent directory, except `synced`.
- A list of session IDs to skip.

Process:

1. Read every `*.jsonl` file under the root.
2. Skip lines where `isSidechain` is true. Those are subagent lines.
3. Keep a session only if it invokes a target skill. An invocation is one of two things:
   - A human message that contains `<command-name>/<skill></command-name>`.
   - An assistant `Skill` tool call whose `skill` input names the skill. `grill` starts `spec` this way.
4. Skip sessions whose ID is in the skip list.
5. For each kept session, emit every human message with the agent text that came before it.

A **human message** is a line with `type` equal to `user` and `origin.kind` equal to `human`. Tool results, skill bodies, and task notifications carry a different `origin.kind` or none. The message content is either a string or an array of parts. Join the `text` parts of an array.

Clean each human message before output:

- Strip `<ide_opened_file>` and `<ide_selection>` blocks.
- Drop the message if nothing is left.
- Drop the message if it is a bare confirmation: `yes`, `ok`, `continue`, or `yes, continue`, in any case.

The agent text is the joined `text` parts of the assistant lines since the last human message. Leave out tool calls and thinking. Cut it to its last 1500 characters.

Output is JSON on stdout. Shape:

```json
{
  "sessions": [
    {
      "id": "55f42192-...",
      "project": "/home/gian/palver/nucleus",
      "date": "2026-09-28",
      "skills": ["grill", "spec"],
      "turns": [
        { "agent": "…last agent text…", "human": "…cleaned human message…", "interrupted": false }
      ]
    }
  ]
}
```

`project` comes from the `cwd` field. `date` comes from the first line's `timestamp`. `skills` lists the target skills the session invoked, in order. `interrupted` is true when the agent turn ended with a `[Request interrupted by user` marker.

### Classifying turns

The model reads the script output and sorts each turn into one of three kinds:

- **Answer**: a reply to a question the agent asked. Not a finding.
- **Correction**: a message that rejects or fixes what the agent just did or said.
- **Instruction**: a new request. Not a finding.

For each correction, the model decides the cause:

- **Skill**: a line in a target skill caused it, or a missing line would have prevented it. A correction in a main-chat build counts when the spec left the decision out. Then the cause is the `spec` skill.
- **Elsewhere**: a project fact, a plain coding slip, or anything no skill line controls.

The model reads the current target `SKILL.md` files before it traces a cause. It traces to the current text, not the text at session time.

### Grouping

The model groups skill corrections that share one cause. A **pattern** is a group with corrections from two or more sessions. A **one-off** is a group from one session.

### The report

The skill writes the report to `docs/retros/<YYYY-MM-DD>.md` in this repo. It creates the directory if it does not exist. A second run on the same day appends `-2`, `-3`, and so on.

The report is in the house style. Its sections, in order:

1. **Summary**: counts of sessions read, corrections found, patterns, and one-offs.
2. **Patterns**: one entry per pattern, most sessions first.
3. **One-offs**: one entry per one-off.
4. **Elsewhere**: one line per correction, with a short reason. No proposed edit.
5. **Sessions read**: one line per session ID, with its project and date.

Each pattern and one-off entry is numbered across both sections. It holds:

- A one-line title
- The target skill and the line it traces to, quoted. For a missing line, the section where the new line goes.
- Each correction quoted, with its session ID and date
- The proposed edit, as the old line and the new line

### Skipping read sessions

Before it runs the script, the skill reads every report in `docs/retros/`. It collects the session IDs from each **Sessions read** section. It passes them to the script as the skip list.

A session still open when a report is written gets skipped later. That is accepted. See Further Notes.

### The gate

After it writes the report, the skill prints the path and a short list of the numbered findings. Then it stops.

The developer answers in one of three ways:

- **Picks findings by number.** The skill applies those edits to the `SKILL.md` files.
- **Changes a proposed edit.** The skill updates the report, prints the list again, and waits again. This repeats as often as the developer needs.
- **Rejects all.** The skill changes no skill file.

The skill marks each finding in the report as applied or rejected. The report keeps the record either way.

When it applies edits, the skill follows the house style. It does not commit. It reports which files it changed.

### Transcript expiry

Claude Code deletes transcripts older than `cleanupPeriodDays`. The default is 30.

As part of this build, set `cleanupPeriodDays` to 365 in `~/.claude/settings.json`. Keep the file's other keys. This file is outside the repo, so the build reports the change.

The skill also checks the setting on each run. If it is under 90, the skill warns in its closing message.

### README

Add `retro` to the Skills list in the README. Change the line "Two of these pair up. Two stand alone." to match the new count. Add a short section that explains the transcript source and the 365-day setting.

## Testing Decisions

The one seam is the extract script's interface: a transcripts root in, JSON out. The test replaces the real `~/.claude/projects` with a fixture directory.

A good test builds a small fixture transcript and checks the JSON. It tests behaviour, not the script's internals.

Cover:

- A session that invokes a target skill is kept. A session that invokes none is dropped.
- A session in the skip list is dropped.
- Sidechain lines are ignored.
- Tool results and skill bodies do not appear as human messages.
- `<ide_opened_file>` and `<ide_selection>` blocks are stripped.
- Bare confirmations are dropped.
- Agent text pairs with the human message after it, and tool calls are left out.
- The interrupt marker sets `interrupted`.
- Both string and array content parse.

Use Python's `unittest`. Put the test beside the script as `test_extract.py`. The repo has no tests today, so this sets the pattern.

The classification and the report are model work. They have no automated test. Check them by running `/retro` once on the real transcripts.

## Out of Scope

- Live capture during a session. The skill reads transcripts after the fact.
- Changing `grill`, `spec`, `lazy`, or `create-sandbox` as part of this build. Edits come from the skill's own runs.
- Skills outside this repo, including `synced/` and Matt Pocock's originals.
- Corrections that belong in a project `CLAUDE.md` or in memory. The report lists them under Elsewhere and goes no further.
- Commits and pushes.
- Running on a schedule.

## Further Notes

A session that is still open when a report is written is marked as read. Corrections made in it later are missed. This is a small loss. Running `/retro` from a fresh session avoids it.

The `/retro` session itself invokes no target skill, so it does not count itself. If a future run does invoke one, the skip list removes it the next time.

Answers and corrections can look alike. A grill answer that says "no, use X" can be a plain answer or a correction of a bad default. Treat it as a correction only when the agent had already stated a choice. A recommended answer the developer rejects counts when the recommendation broke a rule in the skill.
