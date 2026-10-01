#!/usr/bin/env python3
"""Pull human messages and the agent text before them out of Claude Code transcripts.

Prints JSON on stdout. See SKILL.md for the shape.
"""

import argparse
import json
import re
import sys
from pathlib import Path

AGENT_LIMIT = 1500
INTERRUPT = "[Request interrupted by user"
CONFIRMATIONS = {"yes", "ok", "continue", "yes, continue"}
IDE_BLOCK = re.compile(r"<(ide_opened_file|ide_selection)>.*?</\1>", re.DOTALL)


def default_skills():
    skills_dir = Path(__file__).resolve().parent.parent
    return sorted(
        p.name for p in skills_dir.iterdir() if p.is_dir() and p.name != "synced"
    )


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        )
    return ""


def skill_calls(content):
    if not isinstance(content, list):
        return []
    return [
        (part.get("input") or {}).get("skill")
        for part in content
        if isinstance(part, dict)
        and part.get("type") == "tool_use"
        and part.get("name") == "Skill"
    ]


def is_human(line):
    origin = line.get("origin") or {}
    return line.get("type") == "user" and origin.get("kind") == "human"


def clean(text):
    text = IDE_BLOCK.sub("", text).strip()
    if text.lower() in CONFIRMATIONS:
        return ""
    return text


def read_lines(path):
    with open(path, encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                yield json.loads(raw)
            except json.JSONDecodeError:
                continue


def read_session(path, skills):
    project = None
    date = None
    invoked = []
    turns = []
    agent = []
    interrupted = False

    for line in read_lines(path):
        if date is None and line.get("timestamp"):
            date = line["timestamp"][:10]
        if line.get("isSidechain"):
            continue
        if project is None and line.get("cwd"):
            project = line["cwd"]

        message = line.get("message")
        content = message.get("content") if isinstance(message, dict) else None

        if line.get("type") == "assistant":
            for skill in skill_calls(content):
                if skill in skills and skill not in invoked:
                    invoked.append(skill)
            text = text_of(content).strip()
            if text:
                agent.append(text)
            continue

        if line.get("type") != "user":
            continue

        if not is_human(line):
            if INTERRUPT in text_of(content):
                interrupted = True
            continue

        raw = text_of(content)
        for skill in skills:
            if f"<command-name>/{skill}</command-name>" in raw and skill not in invoked:
                invoked.append(skill)

        human = clean(raw)
        if human:
            turns.append(
                {
                    "agent": "\n\n".join(agent)[-AGENT_LIMIT:],
                    "human": human,
                    "interrupted": interrupted,
                }
            )
        agent = []
        interrupted = False

    if not invoked:
        return None
    return {
        "id": path.stem,
        "project": project,
        "date": date,
        "skills": invoked,
        "turns": turns,
    }


def extract(root, skills, skip):
    sessions = []
    for path in sorted(Path(root).rglob("*.jsonl")):
        if path.stem in skip:
            continue
        session = read_session(path, skills)
        if session:
            sessions.append(session)
    sessions.sort(key=lambda s: (s["date"] or "", s["id"]))
    return {"sessions": sessions}


def split_list(values):
    return [v for value in values or [] for v in value.split(",") if v.strip()]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path.home() / ".claude" / "projects"))
    parser.add_argument(
        "--skills", action="append", help="target skill names, comma separated"
    )
    parser.add_argument(
        "--skip", action="append", help="session IDs to skip, comma separated"
    )
    args = parser.parse_args(argv)

    skills = split_list(args.skills) or default_skills()
    skip = set(split_list(args.skip))
    json.dump(extract(args.root, skills, skip), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
