import json
import tempfile
import unittest
from pathlib import Path

from extract import extract

SKILLS = ["grill", "spec"]


def human(text, ts="2026-09-28T10:00:00.000Z", cwd="/home/gian/proj", sidechain=False):
    return {
        "type": "user",
        "origin": {"kind": "human"},
        "isSidechain": sidechain,
        "cwd": cwd,
        "timestamp": ts,
        "message": {"role": "user", "content": text},
    }


def agent(*parts, sidechain=False):
    return {
        "type": "assistant",
        "isSidechain": sidechain,
        "message": {"role": "assistant", "content": list(parts)},
    }


def text(t):
    return {"type": "text", "text": t}


def tool_use():
    return {"type": "tool_use", "id": "toolu_1", "name": "Bash", "input": {"command": "ls"}}


def thinking():
    return {"type": "thinking", "thinking": "private thought"}


def tool_result():
    return {
        "type": "user",
        "isSidechain": False,
        "message": {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": "TOOL OUTPUT"}],
        },
    }


def skill_body():
    return {
        "type": "user",
        "isMeta": True,
        "isSidechain": False,
        "message": {"role": "user", "content": [text("SKILL BODY")]},
    }


def interrupt():
    return {
        "type": "user",
        "isSidechain": False,
        "message": {"role": "user", "content": [text("[Request interrupted by user for tool use]")]},
    }


GRILL = "<command-message>grill</command-message>\n<command-name>/grill</command-name>\n<command-args>build a thing</command-args>"


class ExtractTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, session_id, lines, project="-home-gian-proj"):
        d = self.root / project
        d.mkdir(parents=True, exist_ok=True)
        with open(d / f"{session_id}.jsonl", "w") as f:
            f.write("\n".join(json.dumps(line) for line in lines) + "\n")

    def run_extract(self, skip=()):
        return extract(self.root, SKILLS, set(skip))["sessions"]

    def only(self, **kw):
        sessions = self.run_extract(**kw)
        self.assertEqual(len(sessions), 1)
        return sessions[0]

    def test_keeps_session_that_invokes_target_skill(self):
        self.write("s1", [human(GRILL), agent(text("Question?")), human("no, use rocky")])
        s = self.only()
        self.assertEqual(s["id"], "s1")
        self.assertEqual(s["project"], "/home/gian/proj")
        self.assertEqual(s["date"], "2026-09-28")
        self.assertEqual(s["skills"], ["grill"])

    def test_drops_session_that_invokes_no_target_skill(self):
        self.write("s1", [human("<command-name>/other</command-name>"), agent(text("hi"))])
        self.write("s2", [human("plain chat"), agent(text("hi"))])
        self.assertEqual(self.run_extract(), [])

    def test_lists_invoked_skills_in_order(self):
        self.write("s1", [human(GRILL), human("<command-name>/spec</command-name>"), human(GRILL)])
        self.assertEqual(self.only()["skills"], ["grill", "spec"])

    def test_skill_tool_call_counts_as_invocation(self):
        call = {"type": "tool_use", "id": "t", "name": "Skill", "input": {"skill": "spec"}}
        other = {"type": "tool_use", "id": "u", "name": "Skill", "input": {"skill": "dataviz"}}
        self.write("s1", [human(GRILL), agent(call, other)])
        self.write("s2", [human("plain"), agent(call)])
        sessions = self.run_extract()
        self.assertEqual([(s["id"], s["skills"]) for s in sessions], [("s1", ["grill", "spec"]), ("s2", ["spec"])])

    def test_drops_session_in_skip_list(self):
        self.write("s1", [human(GRILL)])
        self.write("s2", [human(GRILL)])
        self.assertEqual([s["id"] for s in self.run_extract(skip=["s1"])], ["s2"])

    def test_ignores_sidechain_lines(self):
        self.write(
            "s1",
            [
                human(GRILL),
                agent(text("SIDE AGENT"), sidechain=True),
                human("SIDE HUMAN", sidechain=True),
                agent(text("main agent")),
                human("fix it"),
            ],
        )
        turns = self.only()["turns"]
        self.assertEqual([t["human"] for t in turns], [GRILL, "fix it"])
        self.assertEqual(turns[1]["agent"], "main agent")

    def test_sidechain_invocation_does_not_keep_session(self):
        self.write("s1", [human(GRILL, sidechain=True)])
        self.assertEqual(self.run_extract(), [])

    def test_tool_results_and_skill_bodies_are_not_human_messages(self):
        self.write("s1", [human(GRILL), skill_body(), agent(tool_use()), tool_result(), human("wrong")])
        humans = [t["human"] for t in self.only()["turns"]]
        self.assertEqual(humans, [GRILL, "wrong"])

    def test_strips_ide_blocks(self):
        msg = "<ide_opened_file>The user opened x.py</ide_opened_file>\n<ide_selection>a\nb</ide_selection>use tabs"
        self.write("s1", [human(GRILL), human(msg)])
        self.assertEqual(self.only()["turns"][1]["human"], "use tabs")

    def test_drops_message_left_empty_after_strip(self):
        self.write("s1", [human(GRILL), human("<ide_opened_file>x</ide_opened_file>")])
        self.assertEqual(len(self.only()["turns"]), 1)

    def test_drops_bare_confirmations(self):
        lines = [human(GRILL)] + [human(m) for m in ["yes", "OK", " Continue ", "Yes, continue", "yes, but use X"]]
        self.write("s1", lines)
        humans = [t["human"] for t in self.only()["turns"]]
        self.assertEqual(humans, [GRILL, "yes, but use X"])

    def test_pairs_agent_text_with_next_human_message(self):
        self.write(
            "s1",
            [
                human(GRILL),
                agent(thinking()),
                agent(text("first")),
                agent(tool_use()),
                tool_result(),
                agent(text("second")),
                human("no"),
                agent(text("third")),
                human("better"),
            ],
        )
        turns = self.only()["turns"]
        self.assertEqual(turns[0]["agent"], "")
        self.assertEqual(turns[1]["agent"], "first\n\nsecond")
        self.assertEqual(turns[2]["agent"], "third")
        for t in turns:
            self.assertNotIn("private thought", t["agent"])
            self.assertNotIn("TOOL OUTPUT", t["agent"])

    def test_agent_text_resets_after_dropped_confirmation(self):
        self.write("s1", [human(GRILL), agent(text("old")), human("yes"), agent(text("new")), human("wrong")])
        self.assertEqual(self.only()["turns"][1]["agent"], "new")

    def test_cuts_agent_text_to_last_1500_characters(self):
        long = "a" * 1000 + "b" * 1500
        self.write("s1", [human(GRILL), agent(text(long)), human("no")])
        self.assertEqual(self.only()["turns"][1]["agent"], "b" * 1500)

    def test_interrupt_marker_sets_interrupted(self):
        self.write(
            "s1",
            [human(GRILL), agent(text("doing"), tool_use()), interrupt(), human("stop, wrong file"), agent(text("ok")), human("now this")],
        )
        turns = self.only()["turns"]
        self.assertEqual([t["interrupted"] for t in turns], [False, True, False])

    def test_parses_string_and_array_content(self):
        array_msg = human("unused")
        array_msg["message"]["content"] = [text("part one"), {"type": "image"}, text("part two")]
        self.write("s1", [human(GRILL), array_msg])
        self.assertEqual(self.only()["turns"][1]["human"], "part one\npart two")


if __name__ == "__main__":
    unittest.main()
