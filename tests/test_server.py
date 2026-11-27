"""Tests for the Squad MCP server. Run with: python -m unittest discover -s tests -v"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SERVER = REPO / "squad-kit" / "mcp" / "server.py"
spec = importlib.util.spec_from_file_location("squad_server", SERVER)
srv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(srv)


def write(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")


BAD_PROJECT = {
    "package.json": '{"name":"x","scripts":{"lint":"next lint","typecheck":"tsc --noEmit","build":"next build","test":"vitest run"}}',
    "next.config.mjs": "export default {}\n",
    "supabase/migrations/001_init.sql": """
        create table public.items (id uuid primary key, user_id uuid, price numeric);
        create table if not exists public.subscribers (id uuid primary key, phone text);
        alter table public.subscribers enable row level security;
        create policy "all" on public.subscribers for select using (true);
        create or replace function public.do_admin() returns void
        language plpgsql as $$ begin delete from items; end; $$
        security definer;
    """,
    "app/api/items/route.ts": "export async function POST(req: Request) { return Response.json(await req.json()) }\n",
    "app/api/webhook/route.ts": "export async function POST(req: Request) { const s = req.headers.get('x-hub-signature'); return new Response('ok') }\n",
    "components/Admin.tsx": """
        'use client'
        const k = process.env.NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY
        export default function A(){ fetch('/x').catch(() => {}); return <div>12.345</div> }
    """,
    "lib/actions.ts": """
        'use server'
        export async function save(x){ await supabase.from('items').insert(x) }
        const stripe = "sk_live_abcdefghijklmnop1234"
    """,
    "lib/job.py": "try:\n    x()\nexcept Exception:\n    pass\n",
    ".env": "SECRET=1\n",
    ".gitignore": "node_modules\n",
}

GOOD_OVERRIDES = {
    "supabase/migrations/001_init.sql": """
        create table public.items (id uuid primary key, user_id uuid, price numeric);
        alter table public.items enable row level security;
        create policy "own" on public.items for select using (auth.uid() = user_id);
        create or replace function public.do_admin() returns void
        language plpgsql security definer set search_path = '' as $$ begin delete from public.items; end; $$;
    """,
    "app/api/items/route.ts": "export async function POST(req: Request) { const { data } = await supabase.auth.getUser(); return Response.json(data) }\n",
    "components/Admin.tsx": "'use client'\nconst k = process.env.NEXT_PUBLIC_SUPABASE_URL\nexport default function A(){ return <div>ok</div> }\n",
    "lib/actions.ts": "'use server'\nexport async function save(x){ await supabase.auth.getUser(); await supabase.from('items').insert(x) }\n",
    "lib/job.py": "try:\n    x()\nexcept Exception as e:\n    log(e)\n",
    ".gitignore": "node_modules\n.env*\n",
    "tests/rls.test.ts": "// two users rls\n",
}


class ProjectCase(unittest.TestCase):
    def make(self, files: dict[str, str]) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        write(root, files)
        return root


class SecurityAuditTests(ProjectCase):
    def test_bad_project_findings(self):
        root = self.make(BAD_PROJECT)
        result = srv.audit_security_controls({"project_root": str(root)})
        text = "\n".join(result["findings"])
        self.assertEqual(result["verdict"], "REJECTED")
        self.assertEqual(result["supabase_rls"]["tables_without_rls"], ["items"])
        for expected in ("Table without RLS", "using (true)", "security definer", "NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY",
                         "Privileged Supabase key", "Stripe secret key", ".env files present", "app/api/items/route.ts",
                         "Server Action writes data", "No automated security tests"):
            self.assertIn(expected, text)
        self.assertNotIn("app/api/webhook/route.ts", text, "signed webhook must not be flagged")

    def test_good_project_is_clean(self):
        root = self.make({**BAD_PROJECT, **GOOD_OVERRIDES})
        result = srv.audit_security_controls({"project_root": str(root)})
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["verdict"], "APPROVED")


class CodeDeliveryTests(ProjectCase):
    def test_bad_project(self):
        result = srv.audit_code_delivery({"project_root": str(self.make(BAD_PROJECT))})
        text = "\n".join(result["findings"])
        self.assertIn("Hardcoded metric", text)
        self.assertIn("Swallowed error (empty catch/except) in components/Admin.tsx", text)
        self.assertIn("Swallowed error (empty catch/except) in lib/job.py", text)

    def test_good_project(self):
        result = srv.audit_code_delivery({"project_root": str(self.make({**BAD_PROJECT, **GOOD_OVERRIDES}))})
        self.assertEqual(result["findings"], [])


class InspectAndChecksTests(ProjectCase):
    def test_stack_markers_and_integration_paths(self):
        result = srv.inspect_project({"project_root": str(self.make({**BAD_PROJECT, **GOOD_OVERRIDES}))})
        self.assertTrue({"Node", "Next.js", "Supabase"} <= set(result["stack_markers"]))
        self.assertIn("tests/rls.test.ts", result["project_inventory"]["integration_test_paths"])

    def test_detect_checks(self):
        root = self.make(BAD_PROJECT)
        kinds = [(c["kind"], " ".join(c["cmd"])) for c in srv._detect_checks(root, srv.list_files(root))]
        self.assertEqual(kinds, [("lint", "npm run lint"), ("typecheck", "npm run typecheck"), ("build", "npm run build"), ("test", "npm test")])

    def test_run_checks_rejects_unknown_kind(self):
        with self.assertRaises(srv.SquadError):
            srv.run_checks({"project_root": str(self.make(BAD_PROJECT)), "only": ["deploy"]})


class ArtifactTests(ProjectCase):
    def test_initialized_docs_have_every_required_heading(self):
        root = self.make({"README.md": "x"})
        created = srv.initialize_docs({"project_root": str(root)})["created"]
        self.assertIn(".squad/product/field-research.md", created)
        self.assertIn(".squad/quality/finalizer.md", created)
        self.assertIn(".squad/", (root / ".gitignore").read_text(encoding="utf-8"))
        result = srv.validate_artifacts({"project_root": str(root)})
        missing = [a for a in result["artifacts"] if a["missing_sections"]]
        self.assertEqual(missing, [], "templates and validator must agree on headings")

    def test_initialize_never_overwrites(self):
        root = self.make({".squad/coordination/roadmap.md": "# mine\n"})
        srv.initialize_docs({"project_root": str(root)})
        self.assertEqual((root / ".squad/coordination/roadmap.md").read_text(encoding="utf-8"), "# mine\n")

    def test_update_report_rejects_unknown_agent_and_path_escape(self):
        root = self.make({"README.md": "x"})
        with self.assertRaises(srv.SquadError):
            srv.update_report({"project_root": str(root), "agent": "../evil", "content": "x"})
        with self.assertRaises(srv.SquadError):
            srv.safe_path(root, "../outside.md")


class FinalizerGateTests(ProjectCase):
    def _fill(self, root: Path, authz_evidence: str, status: str = "APPROVED") -> dict:
        srv.initialize_docs({"project_root": str(root)})
        path = root / ".squad/quality/finalizer.md"
        lines = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("| Server-side authorization"):
                line = f"| {srv.CHK_AUTHZ} | {status} | {authz_evidence} |"
            lines.append(line)
        path.write_text("\n".join(lines), encoding="utf-8")
        return srv.validate_completion_checklist({"project_root": str(root)})

    def authz_issues(self, result: dict) -> list[str]:
        return [i for i in result["issues"] if i.startswith(srv.CHK_AUTHZ)]

    def test_placeholder_blocks(self):
        root = self.make({"README.md": "x"})
        srv.initialize_docs({"project_root": str(root)})
        result = srv.validate_completion_checklist({"project_root": str(root)})
        self.assertFalse(result["valid"])
        self.assertTrue(any("placeholder" in i for i in result["issues"]))

    def test_authz_requires_two_users(self):
        root = self.make({"README.md": "x"})
        self.assertTrue(self.authz_issues(self._fill(root, "Command: npm test; Result: ok")))

    def test_authz_two_users_passes_row(self):
        root = self.make({"README.md": "x"})
        self.assertEqual(self.authz_issues(self._fill(root, "Command: npm test tests/rls.test.ts; Result: 3 passed, two users A and B")), [])

    def test_portuguese_status_and_evidence_accepted(self):
        root = self.make({"README.md": "x"})
        result = self._fill(root, "Comando: npm test; Resultado: 3 passaram, dois usuários A e B", status="APROVADO")
        self.assertEqual(self.authz_issues(result), [])

    def test_final_verdict_must_be_approved(self):
        root = self.make({"README.md": "x"})
        result = self._fill(root, "Command: x; Result: two users ok")
        self.assertIn("The final verdict must be explicitly APPROVED.", result["issues"])


class ProtocolTests(unittest.TestCase):
    def test_stdio_roundtrip(self):
        msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "nope", "arguments": {}}},
                {"jsonrpc": "2.0", "id": 4, "method": "unknown/method"}]
        payload = "\ufeff" + "\n".join(json.dumps(m) for m in msgs) + "\n\nnot json\n"
        proc = subprocess.run([sys.executable, str(SERVER)], input=payload, capture_output=True, text=True, encoding="utf-8", timeout=60)
        replies = {r.get("id"): r for r in map(json.loads, proc.stdout.splitlines())}
        self.assertEqual(replies[1]["result"]["serverInfo"]["version"], srv.SERVER_VERSION)
        names = {t["name"] for t in replies[2]["result"]["tools"]}
        self.assertEqual(names, set(srv.HANDLERS))
        self.assertTrue(replies[3]["result"]["isError"])
        self.assertEqual(replies[4]["error"]["code"], -32601)
        self.assertEqual(replies[None]["error"]["code"], -32700)


if __name__ == "__main__":
    unittest.main()
