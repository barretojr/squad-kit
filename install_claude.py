#!/usr/bin/env python3
"""Installs the Squad for Claude Code (skills, agents and the optional MCP server).

Usage:
  python install_claude.py --project /path/to/your-app   # .claude/ inside the project
  python install_claude.py --global                      # ~/.claude/
Options:
  --with-heavy-skills   also installs design-taste-frontend (taste-skill, MIT) and playwright-cli (~60 MB)
  --register-mcp        runs `claude mcp add` (scope local to the project; only with --project)
No external dependencies. Agents are converted to the Claude Code format and only run when the
squad skill calls them (each description says so).
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "squad-kit"
LIGHT_SKILLS = ["squad", "product-research", "product-brand-design", "quality-validation",
                "security-validation", "frontend-integration", "design-reference", "spatial-design"]
HEAVY_SKILLS = ["design-taste-frontend", "playwright-cli"]
DROP_KEYS = ("subagent:", "mainAgent:", "inheritCustomizations:", "commandExecutionPolicy:")
PREFIX = "[squad] Use ONLY when the squad skill calls this agent by name. "


def convert_agent(text: str, installed_skills: set[str] | None = None) -> str:
    """Converts the Antigravity frontmatter to Claude Code.

    Claude Code does not understand the agents' `skills:` key; instead of dropping it, it becomes
    an instruction in the body pointing at each installed skill's SKILL.md.
    """
    text = text.lstrip("﻿").replace("\r\n", "\n")
    if not text.startswith("---"):
        return text
    head, _, body = text[3:].partition("\n---")
    out, skills, in_skills = [], [], False
    for line in head.splitlines():
        if in_skills and (line.startswith(" ") or line.startswith("-")):
            item = line.strip().lstrip("-").strip().strip("\"'")
            if item:
                skills.append(Path(item).name)
            continue
        in_skills = False
        if line.startswith("skills:"):
            in_skills = True
            continue
        if line.startswith(DROP_KEYS):
            continue
        if line.startswith("description:"):
            line = "description: " + _yaml_quote(PREFIX + line[len("description:"):].strip())
        out.append(line)
    if skills:
        available = [s for s in skills if installed_skills is None or s in installed_skills]
        missing = [s for s in skills if s not in available]
        if available:
            note = "\n\n> **Skills for this agent:** before acting, read " + ", ".join(
                f"`.claude/skills/{s}/SKILL.md`" for s in available) + " (look in `~/.claude/skills/` if it is not in the project)."
            if missing:
                note += f" Not installed on this machine (install with `--with-heavy-skills` if needed): {', '.join(missing)}."
        else:
            note = f"\n\n> **Skills for this agent not installed:** {', '.join(missing)} (use `--with-heavy-skills`)."
        first, _, rest = body.partition("\n")
        body = first + note + "\n\n" + rest.lstrip("\n")
    return "---" + "\n".join(out) + "\n---" + body


def _yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def copy_tree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "node_modules"))


def ensure_gitignore(project: Path) -> None:
    gi = project / ".gitignore"
    current = gi.read_text(encoding="utf-8", errors="ignore") if gi.is_file() else ""
    if ".squad/" not in current.splitlines():
        with open(gi, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(("\n" if current and not current.endswith("\n") else "") + "\n# Squad artifacts\n.squad/\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    where = ap.add_mutually_exclusive_group(required=True)
    where.add_argument("--project", help="target project root")
    where.add_argument("--global", dest="is_global", action="store_true", help="install into ~/.claude")
    ap.add_argument("--with-heavy-skills", action="store_true")
    ap.add_argument("--register-mcp", action="store_true")
    args = ap.parse_args()

    if not SRC.is_dir():
        print(f"Source folder not found: {SRC}", file=sys.stderr)
        return 1
    if args.is_global:
        base = Path.home() / ".claude"
        proj = None
    else:
        proj = Path(args.project).expanduser().resolve()
        if not proj.is_dir():
            print(f"Project not found: {proj}", file=sys.stderr)
            return 1
        base = proj / ".claude"

    skills = LIGHT_SKILLS + (HEAVY_SKILLS if args.with_heavy_skills else [])
    for name in skills:
        if (SRC / "skills" / name).is_dir():
            copy_tree(SRC / "skills" / name, base / "skills" / name)
    rules = SRC / "rules" / "squad-context.md"
    if rules.is_file():
        shutil.copyfile(rules, base / "skills" / "squad" / "references" / "rules.md")

    (base / "agents").mkdir(parents=True, exist_ok=True)
    for agent in sorted((SRC / "agents").glob("*.md")):
        converted = convert_agent(agent.read_text(encoding="utf-8"), set(skills))
        (base / "agents" / agent.name).write_text(converted, encoding="utf-8", newline="\n")

    (base / "mcp").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC / "mcp" / "server.py", base / "mcp" / "server.py")
    server = (base / "mcp" / "server.py").as_posix()

    if proj is not None:
        ensure_gitignore(proj)

    print(f"Skills ({len(skills)}), agents and MCP server installed in {base}")
    cmd = ["claude", "mcp", "add", "squad", "--scope", "local", "--", sys.executable, server]
    if args.register_mcp and proj is not None:
        if shutil.which("claude"):
            subprocess.run(cmd, cwd=str(proj), check=False)
        else:
            print("`claude` is not on PATH; run the command below by hand.")
    print("\nThe MCP is optional and was NOT registered globally. To enable it only in the project that needs it, run inside it:")
    print("  " + " ".join(f'"{c}"' if " " in c else c for c in cmd))
    print('\nUse: /squad <your request>  or  "use the squad skill and build ..."  (any language)')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
