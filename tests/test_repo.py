"""Repository consistency tests: installer conversion, agent frontmatter, references and language policy."""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KIT = REPO / "squad-kit"
spec = importlib.util.spec_from_file_location("install_claude", REPO / "install_claude.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

# Third-party folders keep their upstream text and are not checked by the language policy.
THIRD_PARTY = ("skills/design-reference/design-md/", "skills/design-taste-frontend/", "skills/playwright-cli/")
PORTUGUESE = re.compile(r"\b(não|você|também|então|aplicação|usuário|configuração|obrigatório|relatório)\b", re.IGNORECASE)


def own_markdown() -> list[Path]:
    files = [p for p in KIT.rglob("*.md") if not any(part in p.relative_to(KIT).as_posix() for part in THIRD_PARTY)]
    for name in ("SKILL.md",):
        files += [p for p in (KIT / "skills").glob(f"*/{name}") if p not in files]
    return sorted(set(files))


class AgentTests(unittest.TestCase):
    def test_frontmatter_and_skill_references(self):
        skills = {p.name for p in (KIT / "skills").iterdir() if p.is_dir()}
        for agent in sorted((KIT / "agents").glob("*.md")):
            text = agent.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), agent.name)
            head = text.split("\n---", 1)[0]
            self.assertRegex(head, rf"(?m)^name: {agent.stem}$", agent.name)
            self.assertRegex(head, r"(?m)^description: .+", agent.name)
            for ref in re.findall(r"(?m)^\s+- \.\./skills/([\w-]+)$", head):
                self.assertIn(ref, skills, f"{agent.name} references missing skill {ref}")

    def test_every_mcp_agent_has_a_profile(self):
        spec_srv = importlib.util.spec_from_file_location("srv", KIT / "mcp" / "server.py")
        srv = importlib.util.module_from_spec(spec_srv)
        spec_srv.loader.exec_module(srv)
        profiles = {p.stem for p in (KIT / "agents").glob("*.md")}
        self.assertEqual(set(srv.AGENTS), profiles)

    def test_agents_write_to_the_paths_the_mcp_expects(self):
        spec_srv = importlib.util.spec_from_file_location("srv", KIT / "mcp" / "server.py")
        srv = importlib.util.module_from_spec(spec_srv)
        spec_srv.loader.exec_module(srv)
        for agent, rel in srv.AGENTS.items():
            text = (KIT / "agents" / f"{agent}.md").read_text(encoding="utf-8")
            self.assertIn(f".squad/{rel}", text, f"{agent}.md must mention .squad/{rel}")
            for heading in srv.ROLE_REQUIRED_HEADINGS.get(agent, []):
                if agent != "finalizer":
                    self.assertIn(heading, text, f"{agent}.md must name the required heading '{heading}'")


class InstallerTests(unittest.TestCase):
    def test_convert_agent_keeps_skills_as_instruction(self):
        out = installer.convert_agent((KIT / "agents" / "qa.md").read_text(encoding="utf-8"), {"quality-validation"})
        head = out.split("\n---", 1)[0]
        self.assertNotIn("skills:", head)
        self.assertNotIn("subagent:", head)
        self.assertIn("[squad] Use ONLY", head)
        self.assertIn("`.claude/skills/quality-validation/SKILL.md`", out)
        self.assertIn("playwright-cli", out)

    def test_install_into_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run([sys.executable, str(REPO / "install_claude.py"), "--project", tmp], capture_output=True, text=True, timeout=120)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            base = Path(tmp) / ".claude"
            self.assertTrue((base / "skills" / "squad" / "references" / "rules.md").is_file())
            self.assertTrue((base / "mcp" / "server.py").is_file())
            self.assertEqual(len(list((base / "agents").glob("*.md"))), 14)
            self.assertIn(".squad/", (Path(tmp) / ".gitignore").read_text(encoding="utf-8"))


class ReferenceTests(unittest.TestCase):
    def test_squad_skill_references_exist(self):
        skill = KIT / "skills" / "squad"
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        for ref in set(re.findall(r"`((?:references|templates)/[\w.-]+\.md)`", text)):
            if ref == "references/rules.md":
                self.assertTrue((KIT / "rules" / "squad-context.md").is_file())
                continue
            self.assertTrue((skill / ref).is_file(), f"missing {ref}")

    def test_third_party_licenses_present(self):
        for folder in ("design-taste-frontend", "playwright-cli"):
            self.assertTrue((KIT / "skills" / folder / "LICENSE").is_file(), f"{folder} needs its upstream LICENSE")
            self.assertTrue((KIT / "skills" / folder / "UPSTREAM.md").is_file(), f"{folder} needs UPSTREAM.md")
        self.assertTrue((KIT / "skills" / "design-reference" / "design-md" / "LICENSE").is_file())
        self.assertTrue((KIT / "skills" / "design-reference" / "UPSTREAM.md").is_file())


class LanguagePolicyTests(unittest.TestCase):
    def test_own_files_are_in_english(self):
        offenders = []
        for path in own_markdown():
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if PORTUGUESE.search(line) and "pt-BR" not in line and "em português" not in line and "use a skill squad" not in line:
                    offenders.append(f"{path.relative_to(REPO)}:{n}: {line.strip()[:80]}")
        self.assertEqual(offenders, [], "Own files must be in English (translations go in *.pt-BR.md):\n" + "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
