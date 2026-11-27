#!/usr/bin/env python3
"""Small, dependency-free MCP stdio server for Squad artifacts, architecture auditing and adversarial code review.

Contract notes:
- Paths under `.squad/` and the required `##` headings are a fixed machine contract and are always in English.
- Report bodies may be written in the user's language. Status keywords are accepted in English and Portuguese
  (APPROVED/APROVADO, REJECTED/REPROVADO, N/A).
- Every audit is a heuristic: findings are leads to confirm by reading the code.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = "2024-11-05"
SERVER_VERSION = "2.0.0"
DOCS_DIR = ".squad"

AGENTS = {
    "pm": "product/field-research.md",
    "coord": "coordination/coord.md",
    "designer": "design/visual-direction.md",
    "design_system": "design/DESIGN.md",
    "dba": "data/dba.md",
    "backend": "backend/backend.md",
    "frontend": "frontend/frontend.md",
    "frontend_reviewer": "frontend/visual-review.md",
    "appsec": "security/appsec.md",
    "qa": "quality/qa.md",
    "devops": "operations/devops.md",
    "code_critic_blind": "quality/blind-code-critique.md",
    "code_critic_spec": "quality/spec-critique.md",
    "finalizer": "quality/finalizer.md",
}
ROADMAP = "coordination/roadmap.md"
DISCOVERY = "product/discovery.md"
PROJECT_MAP = "PROJECT_MAP.md"
EVIDENCE_DIR = "evidence"

BASE_HEADINGS = [
    "Context and evidence",
    "Decisions and recommendations",
    "What needs to be done",
    "Plan and dependencies",
    "What was done",
    "Validation and evidence",
    "Open items and risks",
    "Sources",
]
BASE_PLACEHOLDERS = {
    "Context and evidence": "[Facts, sources and labelled assumptions.]",
    "Decisions and recommendations": "[Relevant decisions.]",
    "What needs to be done": "[Tasks with roadmap IDs, criteria and priority.]",
    "Plan and dependencies": "[Plan and dependencies.]",
    "What was done": "No product implementation in this phase.",
    "Validation and evidence": "Not run.",
    "Open items and risks": "[Open items.]",
    "Sources": "[Direct URLs and access date, if any.]",
}
# Headings checked by validate_squad_artifacts (prefix match on the `## ` line).
BASE_REQUIRED = ["Context and evidence", "What needs to be done", "Plan", "What was done", "Validation", "Open items"]

ROLE_HEADINGS: dict[str, list[tuple[str, str]]] = {
    "pm": [
        ("API and integration research", "For each external service in `.squad/stack.md`: official API, auth flow, limits, account approvals, webhooks and usage policies, with direct URL and access date. If there is none, write \"No external integration planned\" and why."),
        ("Credentials and configuration", "Where and how credentials, tokens and webhooks are configured and stored securely, and how the app behaves without them (empty state, never fake data)."),
    ],
    "dba": [
        ("Physical persistence", "Where the data physically lives (PostgreSQL, Supabase, SQL Server, SQLite...) and how the schema is versioned. In-memory storage is never DONE."),
    ],
    "appsec": [
        ("Authentication and encryption", "Login/session flow, password hashing (Argon2, bcrypt, PBKDF2), token protection and encryption of third-party credentials."),
        ("Security tests and PoCs", "Safe reproductions and automated security tests covering authorization on mutations (two users), secrets handling and input validation."),
    ],
    "frontend": [("User language and anti-jargon", "The UI shows no framework/infra names, tech badges or backend jargon.")],
    "designer": [("User language and anti-jargon", "UI vocabulary is about the user's domain and journey; no tech jargon or fake metrics.")],
    "code_critic_blind": [
        ("Blind critic verdict", "APPROVED or REJECTED, from a cold read of the diff and code."),
        ("Quality violations and anti-patterns", "Disguised mocks, fake data/metrics, simulated latency, swallowed errors, persistence or security gaps."),
        ("Points for the spec critic", "Questions to debate with the specification critic."),
    ],
    "code_critic_spec": [
        ("Spec critic verdict", "APPROVED or REJECTED against the roadmap and PM research."),
        ("Roadmap and PRD compliance", "Item-by-item check of acceptance criteria, integrations, credentials and auth."),
        ("Debate synthesis", "Outcome of the debate with the blind critic."),
    ],
}
ROLE_REQUIRED_HEADINGS = {role: [h for h, _ in items] for role, items in ROLE_HEADINGS.items()}
ROLE_REQUIRED_HEADINGS["finalizer"] = ["Completion checklist", "Final verdict", "Blocking items"]

FINALIZER_CHECKS = [
    "Real project inventory and separate client",
    "Browser/frontend integration with real backend endpoints",
    "Local database connection and initialization",
    "Connection string and Visual Studio access when applicable",
    "Migrations or schema",
    "Local logs and exception handling",
    "Build",
    "Unit tests",
    "Integration tests",
    "Main flows in the browser",
    "Server-side authorization or RLS tested with two users",
]
(CHK_INVENTORY, CHK_BROWSER, CHK_DB, CHK_VS, CHK_MIGRATIONS, CHK_LOGS,
 CHK_BUILD, CHK_UNIT, CHK_INTEGRATION, CHK_FLOWS, CHK_AUTHZ) = FINALIZER_CHECKS

STATUS_ALIASES = {
    "APPROVED": "APPROVED", "APROVADO": "APPROVED", "PASS": "APPROVED", "PASSED": "APPROVED",
    "REJECTED": "REJECTED", "REPROVADO": "REJECTED", "FAIL": "REJECTED", "FAILED": "REJECTED",
    "N/A": "N/A", "NA": "N/A", "NOT APPLICABLE": "N/A", "NÃO APLICÁVEL": "N/A", "NAO APLICAVEL": "N/A",
}

SERVER_AUTH_MARKERS = re.compile(
    r"getUser\s*\(|auth\s*\(\s*\)|getServerSession|currentUser\s*\(|requireUser|requireAuth|withAuth|verifyToken|jwtVerify|"
    r"verifySignature|constructEvent|x-hub-signature|stripe-signature|CRON_SECRET|timingSafeEqual|authorization['\"]?\s*\)|"
    r"\[Authorize|Depends\(\s*get_current_user|@UseGuards|preHandler",
    re.IGNORECASE)
SECRET_VALUE_PATTERNS = [
    ("Stripe secret key", re.compile(r"\bsk_live_[0-9A-Za-z]{10,}")),
    ("Supabase secret key", re.compile(r"\bsb_secret_[0-9A-Za-z_-]{10,}")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("Private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]
PUBLIC_SECRET_ENV = re.compile(r"\b(?:NEXT_PUBLIC_|VITE_|PUBLIC_|EXPO_PUBLIC_)\w*(?:SERVICE_ROLE|SECRET|PRIVATE|PASSWORD)\w*", re.IGNORECASE)
JARGON_PATTERN = re.compile(
    r"(\.NET\s*\d+|React\s*\d+|Vue\s*\d+|Angular\s*\d+|Next\.?js\s*\d+|Node\.?js\s*\d+|no\s+Backend|"
    r"API\s+(?:Conectada|Connected|Online)|Backend\s+(?:Conectado|Connected|Online)|Powered\s+by\s+\w+)",
    re.IGNORECASE)

IGNORED_DIRS = {".git", ".claude", ".agents", ".squad", "node_modules", ".venv", "venv", "bin", "obj", "dist", "build", ".next", ".output",
                "__pycache__", "coverage", ".vercel", ".turbo", ".svelte-kit", ".nuxt", ".pytest_cache", ".mypy_cache", ".ruff_cache",
                "playwright-report", "test-results"}
TEST_PATH_HINT = re.compile(r"(^|/)(tests?|__tests__|__mocks__|fixtures|stories|e2e|spec)(/|$)|\.(test|spec|stories)\.", re.IGNORECASE)


class SquadError(Exception):
    pass


# ---------------------------------------------------------------- helpers

def is_test_path(rel: str) -> bool:
    return bool(TEST_PATH_HINT.search(rel.replace("\\", "/")))


def list_files(root: Path, limit: int | None = None) -> list[str]:
    files: list[str] = []
    for current, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS)
        for name in sorted(names):
            files.append(Path(current, name).relative_to(root).as_posix())
            if limit and len(files) >= limit:
                return files
    return files


def project_root(value: str) -> Path:
    if not value or "\x00" in value:
        raise SquadError("project_root is required")
    root = Path(value).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise SquadError("project_root must be an existing folder")
    return root


def safe_path(root: Path, relative: str, *, allow_missing: bool = True) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or not relative or "\x00" in relative:
        raise SquadError("Use a relative path inside the target project")
    resolved = (root / candidate).resolve(strict=not allow_missing)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise SquadError("Path is outside the target project") from exc
    return resolved


def _read(root: Path, rel: str) -> str:
    try:
        return safe_path(root, rel).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def docs(rel: str) -> str:
    return f"{DOCS_DIR}/{rel}"


def normalize_status(value: str) -> str:
    return STATUS_ALIASES.get(value.strip().strip("`*").upper(), "INVALID")


def has_heading(content: str, heading: str) -> bool:
    return re.search(r"(?im)^##\s+" + re.escape(heading), content) is not None


def ensure_gitignore(root: Path) -> bool:
    """Adds `.squad/` to the project's .gitignore. Returns True when the file was changed."""
    path = root / ".gitignore"
    current = path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""
    if f"{DOCS_DIR}/" in current or DOCS_DIR in current.splitlines():
        return False
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(("\n" if current and not current.endswith("\n") else "") + ("\n" if current else "") + f"# Squad artifacts\n{DOCS_DIR}/\n")
    return True


def find_ui_jargon_leaks(root: Path, files: list[str]) -> list[dict[str, Any]]:
    leaks = []
    for rel in files:
        if rel.endswith((".tsx", ".jsx", ".html", ".vue", ".svelte", ".astro")) and not is_test_path(rel):
            matches = JARGON_PATTERN.findall(_read(root, rel))
            if matches:
                leaks.append({"file": rel, "matches": sorted(set(matches))})
    return leaks


# ---------------------------------------------------------------- inspect

def inspect_project(args: dict[str, Any]) -> dict[str, Any]:
    root = project_root(args.get("project_root", ""))
    files = list_files(root, limit=5000)

    markers = {".NET": ["*.sln", "*.slnx", "*.csproj"], "Node": ["package.json"],
               "Python": ["pyproject.toml", "requirements.txt", "setup.py"], "Rust": ["Cargo.toml"], "Go": ["go.mod"]}
    stacks = [label for label, patterns in markers.items() if any(Path(p).match(pt) for p in files for pt in patterns)]
    platform_markers = {
        "Next.js": lambda f: re.search(r"(^|/)next\.config\.(js|mjs|cjs|ts)$", f) is not None,
        "Vite": lambda f: re.search(r"(^|/)vite\.config\.(js|mjs|cjs|ts)$", f) is not None,
        "Vercel": lambda f: f == "vercel.json" or f.endswith("/vercel.json"),
        "Supabase": lambda f: f.startswith("supabase/") and (f.endswith("config.toml") or "/migrations/" in f),
    }
    stacks += [label for label, test in platform_markers.items() if any(test(f) for f in files)]

    db_files = [f for f in files if f.endswith((".db", ".sqlite", ".sqlite3"))]
    has_docker_db = any(
        "docker-compose" in f and f.endswith((".yml", ".yaml"))
        and any(k in _read(root, f).lower() for k in ("postgres", "mysql", "mariadb", "mongo", "redis"))
        for f in files)
    db_drivers = ("npgsql", "entityframeworkcore", "dapper", "prisma", "typeorm", "psycopg", "sqlalchemy", "better-sqlite3", "\"pg\"",
                  "supabase", "drizzle", "knex", "sequelize", "mongoose", "asyncpg", "sqlmodel", "gorm", "microsoft.data.sqlclient", "sqlite")
    db_driver_found = any(f.endswith((".csproj", "package.json", "requirements.txt", "pyproject.toml"))
                          and any(k in _read(root, f).lower() for k in db_drivers) for f in files)
    has_supabase_project = any(f.startswith("supabase/") for f in files)
    persistence_status = "database_configured" if (db_files or has_docker_db or db_driver_found or has_supabase_project) else "in_memory_or_unconfigured"

    auth_markers = ("addauthentication", "jwtbearer", "bcrypt", "argon2", "passwordhasher", "jsonwebtoken", "passport", "supabase.auth",
                    "auth.signin", "next-auth", "authjs", "clerk", "lucia", "oauth2passwordbearer", "passlib", "django.contrib.auth",
                    "addidentity", "enable row level security")
    has_auth = any(f.endswith((".cs", ".ts", ".tsx", ".js", ".py", ".sql")) and not is_test_path(f)
                   and any(k in _read(root, f).lower() for k in auth_markers) for f in files)

    config_files = [f for f in files if f.endswith((".env", ".env.example", "appsettings.json", "appsettings.Development.json", "config.yaml"))]
    gi_txt = _read(root, ".gitignore")
    integration_test_paths = []
    for f in files:
        if "test" not in f.lower() or not f.lower().endswith((".cs", ".ts", ".tsx", ".js", ".py", ".sql")):
            continue
        if re.search(r"(?i)integration|webapplicationfactory|testcontainer|testserver|httpclient|supertest|fastify\.inject|testclient|"
                     r"createClient\s*\(|supabase\s+start|plan\s*\(\s*\d+\s*\)|row level security|\brls\b", f + "\n" + _read(root, f)):
            integration_test_paths.append(f)

    stack_file = root / DOCS_DIR / "stack.md"
    return {
        "project_root": str(root),
        "docs_dir": DOCS_DIR,
        "declared_stack_md": stack_file.read_text(encoding="utf-8", errors="replace")[:4000] if stack_file.is_file() else None,
        "file_count_listed": len(files),
        "truncated": len(files) >= 5000,
        "stack_markers": stacks,
        "project_inventory": {
            "solution_files": [f for f in files if Path(f).suffix.lower() in (".sln", ".slnx")],
            "dotnet_projects": [f for f in files if f.lower().endswith(".csproj")],
            "package_manifests": [f for f in files if Path(f).name == "package.json"],
            "client_projects": [f for f in files if Path(f).name == "package.json" and any(p in f.lower().split("/") for p in ("client", "frontend", "web", "ui"))],
            "embedded_ui": [f for f in files if re.search(r"(^|/)wwwroot/index\.html$", f, re.IGNORECASE)],
            "migration_or_schema_files": [f for f in files if re.search(r"(^|/)(migrations?|schema)(/|\.)|\.sql$", f, re.IGNORECASE)],
            "test_projects": [f for f in files if "test" in Path(f).name.lower() and f.lower().endswith((".csproj", "package.json", "pyproject.toml"))],
            "integration_test_paths": integration_test_paths,
            "local_log_files": [f for f in files if f.lower().endswith((".log", ".log.1"))],
        },
        "architecture_audit": {
            "persistence_status": persistence_status,
            "persistence_details": {"db_files_found": db_files, "has_docker_db": has_docker_db, "db_driver_found": db_driver_found},
            "auth_status": "present" if has_auth else "missing_or_unimplemented",
            "config_files": config_files,
            "gitignore_has_docs": f"{DOCS_DIR}/" in gi_txt or DOCS_DIR in gi_txt.splitlines(),
            "ui_tech_jargon_leaks": find_ui_jargon_leaks(root, files),
        },
        "files": files,
    }


# ---------------------------------------------------------------- audits

def audit_code_delivery(args: dict[str, Any]) -> dict[str, Any]:
    """Mechanical scan for shortcuts: simulated latency, fake IDs/metrics, embedded mocks, swallowed errors, UI jargon."""
    root = project_root(args.get("project_root", ""))
    files = list_files(root)
    findings: list[str] = []

    for leak in find_ui_jargon_leaks(root, files):
        findings.append(f"Tech jargon in the UI ({leak['file']}): {leak['matches']}")

    timer_pattern = re.compile(r"setIs\w+\(true\)[^;]*;\s*setTimeout|setTimeout\s*\(\s*\(\)\s*=>\s*\{[^}]*set(?:Data|Items|Results|List|Rows|Records)\b", re.DOTALL | re.IGNORECASE)
    random_id_pattern = re.compile(r"Math\.random\(\)\.toString\(36\)", re.IGNORECASE)
    fake_metrics_pattern = re.compile(r">\s*(?:R\$|\$|€|£)?\s*\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?\s*<")
    mock_data_pattern = re.compile(r"(?:const|let|var)\s+(?:(?:FALLBACK|MOCK|DUMMY|FAKE)_\w+|(?:mock|dummy|fake)[A-Z]\w*)\b")
    for f in files:
        if not f.endswith((".tsx", ".jsx", ".ts", ".js")) or is_test_path(f):
            continue
        txt = _read(root, f)
        if timer_pattern.search(txt):
            findings.append(f"Simulated latency (setTimeout) in {f}. Do not fake network delay.")
        if random_id_pattern.search(txt):
            findings.append(f"Fake ID generation (Math.random) in {f}. IDs must come from the backend/database.")
        if f.endswith((".tsx", ".jsx")) and fake_metrics_pattern.search(txt):
            findings.append(f"Hardcoded metric in the UI in {f}. Remove invented numbers; show real data or an empty state.")
        if mock_data_pattern.search(txt):
            findings.append(f"Embedded mock data in {f}. Render an empty state or call the real API instead.")

    empty_catch = re.compile(r"catch\s*(?:\([^\)]*\))?\s*\{\s*\}", re.IGNORECASE)
    empty_promise_catch = re.compile(r"\.catch\(\s*(?:\(\s*\w*\s*\)|\w+)\s*=>\s*(?:\{\s*\}|null|undefined)\s*\)")
    py_except_pass = re.compile(r"^\s*except\b[^:\n]*:\s*(?:\n\s*)?pass\b", re.MULTILINE)
    go_ignored_err = re.compile(r"if\s+err\s*!=\s*nil\s*\{\s*\}")
    for f in files:
        if is_test_path(f) or not f.endswith((".cs", ".java", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".py", ".go")):
            continue
        txt = _read(root, f)
        if f.endswith(".py"):
            swallowed = py_except_pass.search(txt)
        elif f.endswith(".go"):
            swallowed = go_ignored_err.search(txt)
        else:
            swallowed = empty_catch.search(txt) or empty_promise_catch.search(txt)
        if swallowed:
            findings.append(f"Swallowed error (empty catch/except) in {f}.")
        if f.endswith(".cs") and "Thread.Sleep" in txt:
            findings.append(f"Blocking call (Thread.Sleep) in {f}.")

    return {"project_root": str(root), "verdict": "APPROVED" if not findings else "REJECTED", "clean": not findings,
            "findings_count": len(findings), "findings": findings}


def audit_security_controls(args: dict[str, Any]) -> dict[str, Any]:
    root = project_root(args.get("project_root", ""))
    files = list_files(root)
    findings: list[str] = []

    test_files = [f for f in files if "test" in f.lower() and f.endswith((".cs", ".ts", ".tsx", ".js", ".py", ".sql"))]
    security_tests = [f for f in test_files if any(k in Path(f).name.lower() for k in
                      ("security", "ssrf", "auth", "bola", "idor", "xss", "csrf", "crypto", "rls", "polic", "permission", "access"))]
    if not security_tests:
        findings.append("No automated security tests found (file names with security/auth/rls/policy/idor/permission...).")

    # .NET controllers without [Authorize]
    for f in files:
        if not f.endswith(".cs") or not any(k in f.lower() for k in ("controller", "routes", "endpoint")):
            continue
        if not any(c in f.lower() for c in ("integration", "admin", "payment", "billing", "account", "user")):
            continue
        txt = _read(root, f)
        if re.search(r"\[Authorize(?:Attribute)?\]", txt):
            continue
        for action in re.findall(r"\[Http(?:Post|Put|Delete|Patch)[^\]]*\]\s*(?:\[[^\]]+\]\s*)*public\s+[^\(]+\s+(\w+)\s*\(", txt):
            if "webhook" in action.lower():
                continue  # webhooks are authorized by signature, not by user token
            if not re.search(r"(\[[^\]]*Authorize[^\]]*\]\s*)+\[Http(?:Post|Put|Delete|Patch)[^\]]*\]\s*(?:\[[^\]]+\]\s*)*public\s+[^\(]+\s+" + re.escape(action), txt):
                findings.append(f"Unprotected mutation: action '{action}' in {f} has no [Authorize].")

    # third-party credentials stored without encryption
    has_credentials_entity = has_encryption = False
    for f in files:
        if not f.endswith((".cs", ".ts", ".py")):
            continue
        txt = _read(root, f)
        if "IntegrationConfig" in txt or "ConnectionSettings" in txt or ("ApiKey" in txt and ("ApiSecret" in txt or "AccessToken" in txt)):
            has_credentials_entity = True
        if any(k in txt for k in ("Aes", "DataProtection", "EncryptionService", "EncryptString", "ProtectedPersonalData", "createCipheriv",
                                  "Fernet", "AESGCM", "pgp_sym_encrypt", "vault.create_secret", "pgsodium")):
            has_encryption = True
    credentials_status = "present"
    if has_credentials_entity and not has_encryption:
        credentials_status = "plaintext_vulnerable"
        findings.append("Insecure storage: an entity stores third-party ApiKey/ApiSecret/tokens and no encryption service was found.")

    supabase = _audit_supabase_sql(root, files)
    findings.extend(supabase["findings"])
    findings.extend(_audit_client_secret_exposure(root, files))
    findings.extend(_audit_js_server_routes(root, files))

    return {"project_root": str(root), "verdict": "APPROVED" if not findings else "REJECTED", "clean": not findings,
            "findings_count": len(findings), "security_tests_found": security_tests,
            "credentials_encryption_status": credentials_status,
            "supabase_rls": {"tables_found": supabase["tables"], "tables_without_rls": supabase["without_rls"]},
            "note": "Heuristics: confirm each finding by reading the code; no findings does not prove the app is secure.",
            "findings": findings}


def _audit_supabase_sql(root: Path, files: list[str]) -> dict[str, Any]:
    sql_files = [f for f in files if f.endswith(".sql") and not is_test_path(f)]
    texts = {f: _read(root, f) for f in sql_files}
    all_sql = "\n".join(texts.values())
    if not all_sql:
        return {"tables": [], "without_rls": [], "findings": []}
    ident = r'(?:"?(\w+)"?\.)?"?(\w+)"?'
    created: dict[str, str] = {}
    for f, txt in texts.items():
        for m in re.finditer(r"(?i)\bcreate\s+table\s+(?:if\s+not\s+exists\s+)?" + ident, txt):
            if (m.group(1) or "public").lower() == "public":
                created.setdefault(m.group(2).lower(), f)
    rls_on = {m.group(2).lower() for m in re.finditer(
        r"(?i)\balter\s+table\s+(?:only\s+)?(?:if\s+exists\s+)?" + ident + r"\s+enable\s+row\s+level\s+security", all_sql)}
    without = sorted(t for t in created if t not in rls_on)
    findings = [f"Table without RLS (Supabase): '{t}' created in {created[t]} with no 'enable row level security'. Anyone with the anon key can reach it."
                for t in without]
    for f, txt in texts.items():
        if re.search(r"(?i)create\s+policy[^;]*\busing\s*\(\s*true\s*\)", txt):
            findings.append(f"Permissive policy 'using (true)' in {f}: confirm the table only holds public data.")
        starts = list(re.finditer(r"(?im)^\s*create\s+(?:or\s+replace\s+)?function\s+([\w.\"]+)", txt))
        for i, m in enumerate(starts):
            end = starts[i + 1].start() if i + 1 < len(starts) else len(txt)
            nxt = re.search(r"(?im)^\s*(?:create|alter|grant|revoke|drop|insert|comment)\s", txt[m.end():end])
            chunk = txt[m.start():m.end() + nxt.start()] if nxt else txt[m.start():end]
            if re.search(r"(?i)security\s+definer", chunk) and not re.search(r"(?i)set\s+search_path", chunk):
                findings.append(f"security definer function without 'set search_path' in {f} ({m.group(1)}).")
    return {"tables": sorted(created), "without_rls": without, "findings": findings}


def _audit_client_secret_exposure(root: Path, files: list[str]) -> list[str]:
    findings: list[str] = []
    code_ext = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte", ".astro", ".py", ".cs", ".go", ".json", ".yml", ".yaml", ".toml")
    for f in files:
        name = Path(f).name
        is_env = name.startswith(".env")
        if is_test_path(f) or not (f.endswith(code_ext) or is_env) or name in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock"):
            continue
        txt = _read(root, f)
        if not txt:
            continue
        if not is_env or name == ".env.example":
            for label, pattern in SECRET_VALUE_PATTERNS:
                if pattern.search(txt):
                    findings.append(f"Hardcoded secret ({label}) in {f}. Move it to an environment variable and revoke the exposed key.")
        for m in sorted(set(PUBLIC_SECRET_ENV.findall(txt))):
            findings.append(f"Public variable with a secret-like name in {f}: '{m}'. NEXT_PUBLIC_/VITE_ prefixes ship to the browser bundle.")
        if f.endswith((".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte")) and re.search(r"(?i)service_role|SERVICE_ROLE_KEY|SUPABASE_SECRET_KEY", txt):
            client_side = (re.search(r"^\s*['\"]use client['\"]", txt, re.MULTILINE) or re.search(r"import\.meta\.env", txt)
                           or (re.search(r"(^|/)(components|hooks|pages|src/(?!server|api))/", f) and not re.search(r"(^|/)(api|server)/", f)))
            if client_side:
                findings.append(f"Privileged Supabase key referenced in client code: {f}. The service_role/secret key must only exist on the server.")
    env_files = [f for f in files if Path(f).name in (".env", ".env.local", ".env.production", ".env.development")]
    gi = _read(root, ".gitignore")
    if env_files and not re.search(r"(?m)^\s*(?:\*\*/)?\.env(?:\*|\.\*|\.local)?\s*$", gi):
        findings.append(f".env files present ({', '.join(env_files)}) without a '.env*' rule in .gitignore: secrets may get committed.")
    return findings


def _audit_js_server_routes(root: Path, files: list[str]) -> list[str]:
    findings: list[str] = []
    mutating_export = re.compile(r"export\s+(?:async\s+)?(?:function\s+|const\s+)(POST|PUT|PATCH|DELETE)\b")
    db_write = re.compile(r"\.(?:insert|update|upsert|delete)\s*\(|prisma\.\w+\.(?:create|update|upsert|delete)|db\.(?:insert|update|delete)\s*\(")
    for f in files:
        if is_test_path(f) or not f.endswith((".ts", ".tsx", ".js", ".jsx", ".mjs")):
            continue
        txt = _read(root, f)
        if not txt or SERVER_AUTH_MARKERS.search(txt):
            continue
        app_route = re.search(r"(^|/)app/(.*/)?route\.(ts|js|mjs)$", f)
        pages_api = re.search(r"(^|/)pages/api/", f)
        if app_route or pages_api:
            verbs = sorted(set(mutating_export.findall(txt)))
            if not verbs and pages_api:
                verbs = sorted(set(re.findall(r"req\.method\s*===?\s*['\"](POST|PUT|PATCH|DELETE)['\"]", txt)))
            if verbs:
                findings.append(f"Mutation route without a user/signature check ({', '.join(verbs)}) in {f}. Validate the session on the server "
                                "(e.g. supabase.auth.getUser()) or the webhook signature / cron secret.")
        elif re.search(r"^\s*['\"]use server['\"]", txt, re.MULTILINE) and db_write.search(txt):
            findings.append(f"Server Action writes data without a user check in {f}. Confirm getUser() on the server or RLS covering the operation.")
    return findings


def audit_frontend_taste(args: dict[str, Any]) -> dict[str, Any]:
    root = project_root(args.get("project_root", ""))
    ai_cliches = ["unlock your potential", "unlock the power", "supercharge your", "game-changing", "game changer", "next-generation",
                  "next-gen", "cutting-edge", "seamless integration", "dive deep into", "elevate your", "revolutionize",
                  "discover the power", "in today's fast-paced world", "trusted by over", "trusted by fortune 500", "loved by 10,000+"]
    hex_re = re.compile(r"(?:bg|text|border|fill|stroke)-\[#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\]")
    px_re = re.compile(r"(?:p|px|py|m|mx|my|w|h|gap)-\[\d{2,}px\]")
    files_audited = 0
    issues: list[dict[str, Any]] = []
    for rel in list_files(root):
        if Path(rel).suffix.lower() not in {".tsx", ".jsx", ".html", ".vue", ".svelte", ".astro"}:
            continue
        files_audited += 1
        content = _read(root, rel)
        lower = content.lower()
        for cliche in ai_cliches:
            if cliche in lower:
                issues.append({"file": rel, "type": "ai_copy_cliche", "severity": "medium", "match": cliche,
                               "message": f"Generic AI/marketing copy ('{cliche}'). Use concise domain language."})
        hexes = hex_re.findall(content)
        if hexes:
            issues.append({"file": rel, "type": "hardcoded_hex_token", "severity": "low", "matches": sorted(set(hexes))[:5], "count": len(hexes),
                           "message": "Arbitrary hex colors in Tailwind classes. Use semantic tokens (primary, accent, muted, card, border)."})
        pxs = px_re.findall(content)
        if len(pxs) > 3:
            issues.append({"file": rel, "type": "arbitrary_spacing_dimensions", "severity": "low", "matches": sorted(set(pxs))[:5],
                           "message": "Many arbitrary pixel spacings. Use the design system spacing scale."})
        if content.count("animate-") > 2 and "motion-reduce" not in content and "prefers-reduced-motion" not in content:
            issues.append({"file": rel, "type": "missing_reduced_motion", "severity": "medium",
                           "message": "Animations without 'motion-reduce' / 'prefers-reduced-motion' handling (WCAG)."})
    return {"project_root": str(root), "files_audited": files_audited, "taste_score": max(0, 100 - len(issues) * 10),
            "passed": not any(i["severity"] in ("high", "medium") for i in issues), "total_issues": len(issues), "issues": issues,
            "recommendations": ["Use semantic tokens instead of arbitrary hex classes.",
                                "Replace generic AI copy with practical language about the user's real tasks.",
                                "Support prefers-reduced-motion."]}


# ---------------------------------------------------------------- .squad artifacts

def _agent_template(agent: str) -> str:
    extra = "".join(f"## {h}\n\n[{hint}]\n\n" for h, hint in ROLE_HEADINGS.get(agent, []))
    base = "".join(f"## {h}\n\n{BASE_PLACEHOLDERS[h]}\n\n" for h in BASE_HEADINGS)
    return (f"# {agent.replace('_', ' ').title()} — Report\n\n- **Status:** PLANNED\n- **Updated:** {date.today().isoformat()}\n"
            f"- **Request/roadmap:** [fill in]\n- **Owner:** {agent}\n\n> Headings are a fixed contract (English). Write the body in the language in `.squad/stack.md`.\n\n"
            + extra + base)


def _finalizer_template() -> str:
    h = ROLE_REQUIRED_HEADINGS["finalizer"]
    rows = "".join(f"| {check} | [fill in] | [fill in] |\n" for check in FINALIZER_CHECKS)
    return (f"# Finalizer — Report\n\n- **Status:** PLANNED\n- **Updated:** {date.today().isoformat()}\n- **Request/roadmap:** [fill in]\n"
            f"- **Owner:** independent final audit\n\n## {h[0]}\n\n"
            "Each row is `APPROVED`, `REJECTED` or `N/A` with verifiable evidence. N/A needs a reason. Approved tests record "
            "`Command: ...; Result: ...`. Unit tests do not prove integration. Report UI embedded in the API. LocalDB/Visual Studio only applies to .NET on Windows.\n\n"
            "| Check | Status | Evidence (file/route; command and result for tests) |\n|---|---|---|\n" + rows +
            f"\n## {h[1]}\n\n**Final verdict:** [APPROVED or REJECTED]\n\n## {h[2]}\n\n[None, or concrete tasks linked to the roadmap.]\n\n"
            + "".join(f"## {x}\n\n[Fill in.]\n\n" for x in BASE_HEADINGS))


def initialize_docs(args: dict[str, Any]) -> dict[str, Any]:
    root = project_root(args.get("project_root", ""))
    (root / DOCS_DIR).mkdir(parents=True, exist_ok=True)
    index = ("# Squad documentation\n\nRequest: [fill in]\n\n- [Stack and decisions](./stack.md)\n- [Discovery](./product/discovery.md)\n"
             "- [Roadmap](./coordination/roadmap.md)\n- [Project map](./PROJECT_MAP.md)\n\n## Reports\n\n"
             + "".join(f"- [{name}](./{path})\n" for name, path in AGENTS.items()))
    contents = {
        "README.md": index,
        ROADMAP: ("# Roadmap\n\n## Context and decisions\n\n[Context, observed stack and decisions.]\n\n## Items\n\n"
                  "| ID | Priority | Status | Scope | Dependencies | Acceptance criteria | Evidence |\n|---|---|---|---|---|---|---|\n\n"
                  "## Acceptance table\n\n| Criterion | Status | Evidence |\n|---|---|---|\n"),
        PROJECT_MAP: ("# PROJECT_MAP — Confirmed project index\n\nConfirm paths and contracts before relying on this map.\n\n"
                      "## Screens and components\n\n| Area | Path | States | Verified on |\n|---|---|---|---|\n\n"
                      "## Routes and APIs\n\n| Flow | Method/route | Contract | Authorization | Evidence |\n|---|---|---|---|---|\n\n"
                      "## Data and integrations\n\n| Resource | Source | Consumers | Notes |\n|---|---|---|---|\n\n"
                      "## Tests and operations\n\n| Scope | Command/document | Result |\n|---|---|---|\n"),
    }
    created: list[str] = []
    for rel in ["README.md", *AGENTS.values(), ROADMAP, PROJECT_MAP]:
        target = safe_path(root, docs(rel))
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if rel in contents:
            content = contents[rel]
        elif rel == AGENTS["finalizer"]:
            content = _finalizer_template()
        else:
            content = _agent_template(next(k for k, v in AGENTS.items() if v == rel))
        target.write_text(content, encoding="utf-8", newline="\n")
        created.append(docs(rel))
    ensure_gitignore(root)
    return {"project_root": str(root), "docs_dir": DOCS_DIR, "created": created, "preserved_existing": True}


def update_report(args: dict[str, Any]) -> dict[str, Any]:
    root = project_root(args.get("project_root", ""))
    agent, content = args.get("agent"), args.get("content")
    if agent not in AGENTS:
        raise SquadError(f"agent must be one of: {', '.join(AGENTS)}")
    if not isinstance(content, str) or not content.strip():
        raise SquadError("content must hold the full report")
    target = safe_path(root, docs(AGENTS[agent]))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")
    return {"updated": docs(AGENTS[agent])}


def update_roadmap(args: dict[str, Any]) -> dict[str, Any]:
    root = project_root(args.get("project_root", ""))
    content = args.get("content")
    if not isinstance(content, str) or not content.strip():
        raise SquadError("content must hold the full roadmap")
    target = safe_path(root, docs(ROADMAP))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")
    return {"updated": docs(ROADMAP)}


def _completion_declared(root: Path) -> bool:
    text = _read(root, docs(ROADMAP))
    return bool(re.search(r"(?im)^\s*(?:[-*]|\|).*\b(?:DONE|VALIDATED|CONCLU\w*|VALIDADO)\b", text))


def validate_completion_checklist(args: dict[str, Any]) -> dict[str, Any]:
    """Blocks final acceptance unless the independent finalizer has evidence for every gate."""
    root = project_root(args.get("project_root", ""))
    content = _read(root, docs(AGENTS["finalizer"]))
    rows: dict[str, tuple[str, str]] = {}
    for line in content.splitlines():
        if not line.strip().startswith("|") or re.match(r"\|\s*:?-+", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3:
            rows[cells[0].casefold()] = (cells[1], cells[2])

    inspection = inspect_project({"project_root": str(root)})
    inventory = inspection["project_inventory"]
    dotnet_windows = ".NET" in inspection["stack_markers"] and os.name == "nt"
    results, issues = [], []
    for required in FINALIZER_CHECKS:
        raw_status, evidence = next((v for k, v in rows.items() if required.casefold() in k), ("", ""))
        status = normalize_status(raw_status) if raw_status else "MISSING"
        row_issues: list[str] = []
        if status in ("MISSING", "INVALID"):
            row_issues.append("missing or invalid status (use APPROVED, REJECTED or N/A).")
        if not evidence.strip() or re.search(r"(?i)\[(?:fill in|preencher|evidence|evid[eê]ncia|pending|pendente)\]", evidence):
            row_issues.append("missing or placeholder evidence.")
        if required == CHK_VS and not dotnet_windows and status != "N/A":
            row_issues.append("must be N/A outside .NET on Windows.")
        elif status == "N/A" and not re.search(r"(?i)(reason|because|not applicable|motivo|porque)", evidence):
            row_issues.append("N/A must state the reason.")
        if status == "REJECTED":
            row_issues.append("a REJECTED row blocks final acceptance.")
        if status == "APPROVED":
            if required in (CHK_BUILD, CHK_UNIT, CHK_INTEGRATION, CHK_FLOWS, CHK_AUTHZ) and not (
                    re.search(r"(?i)(command|comando)\s*[:=].+", evidence) and re.search(r"(?i)(result|resultado)\s*[:=].+", evidence)):
                row_issues.append("approval needs an explicit Command: and Result:.")
            if required == CHK_INTEGRATION:
                if not re.search(r"(?i)(integration|integra[cç][aã]o|webapplicationfactory|testcontainer|api test|teste de api)", evidence):
                    row_issues.append("evidence must identify an integration/API test; a unit test is not proof.")
                paths = inventory["integration_test_paths"]
                if not paths or not any(p in evidence for p in paths):
                    row_issues.append("cite a detected integration test path (see project_inventory.integration_test_paths).")
            if required == CHK_BROWSER and not re.search(r"(?i)(browser|navegador).*(request|requis)|request.*(?:HTTP\s*[2-5]\d\d|status\s*[2-5]\d\d)", evidence):
                row_issues.append("needs an actual browser request and its observed HTTP status.")
            if required == CHK_VS and dotnet_windows and not re.search(r"(?i)(localdb|visual studio).*(connection|string)|(connection|string).*(localdb|visual studio)", evidence):
                row_issues.append("needs evidence of the configured connection string and access.")
            if required == CHK_AUTHZ and not re.search(r"(?i)(two|2|dois)\s+(users|usu[aá]rios|identities|identidades)|user\s*a\b.*user\s*b\b|usu[aá]rio\s*a\b.*usu[aá]rio\s*b\b", evidence):
                row_issues.append("needs a test with two users (A cannot access B's data).")
            if required == CHK_INVENTORY:
                listed = [*inventory["solution_files"], *inventory["dotnet_projects"], *inventory["package_manifests"], *inventory["embedded_ui"]]
                missing = [p for p in listed if p not in evidence]
                if missing:
                    row_issues.append(f"evidence omits detected paths: {missing}.")
        issues.extend(f"{required}: {i}" for i in row_issues)
        results.append({"check": required, "status": status, "evidence": evidence, "valid": not row_issues})

    verdict = re.search(r"(?im)^\s*[-*]?\s*\*\*?(?:final verdict|veredito final)\*\*?\s*:\s*`?(\w+)", content)
    if not verdict or normalize_status(verdict.group(1)) != "APPROVED":
        issues.append("The final verdict must be explicitly APPROVED.")
    return {"valid": not issues, "blocks_final_acceptance": bool(issues), "checklist": results, "issues": issues,
            "project_inventory": inventory, "platform_applicability": {"dotnet_windows": dotnet_windows}}


def validate_artifacts(args: dict[str, Any]) -> dict[str, Any]:
    root = project_root(args.get("project_root", ""))
    required = [docs("README.md"), docs(ROADMAP), *[docs(p) for p in AGENTS.values()]]
    link_re = re.compile(r"\[[^]]*\]\(([^)]+)\)")
    issues: list[str] = []
    leaks = find_ui_jargon_leaks(root, list_files(root))
    issues.extend(f"Tech jargon in the UI ({leak['file']}): {leak['matches']}" for leak in leaks)

    results = []
    for rel in required:
        path = safe_path(root, rel)
        content = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        agent = next((k for k, v in AGENTS.items() if docs(v) == rel), None)
        missing_sections = []
        if agent and agent != "design_system":
            wanted = BASE_REQUIRED + ROLE_REQUIRED_HEADINGS.get(agent, [])
            missing_sections = [h for h in wanted if not has_heading(content, h)]
        broken = []
        for target in link_re.findall(content):
            target = target.split("#", 1)[0]
            if not target or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("//"):
                continue
            try:
                if not safe_path(root, (path.parent / target).resolve().relative_to(root).as_posix()).exists():
                    broken.append(target)
            except (ValueError, SquadError):
                broken.append(target)
        if agent == "dba" and re.search(r"status:\s*\**\s*(done|conclu[ií]do)", content, re.IGNORECASE):
            upper = content.upper()
            if any(k in upper for k in ("IN MEMORY", "IN-MEMORY", "EM MEMÓRIA", "LIST<")) and not any(k in upper for k in ("POSTGRES", "SQLITE", "SUPABASE", "MIGRATION")):
                issues.append("Persistence gap in dba.md: DONE is not allowed while data lives only in memory.")
        results.append({"path": rel, "exists": path.is_file(), "non_empty": bool(content.strip()),
                        "missing_sections": missing_sections, "broken_local_links": broken})
        if not content.strip():
            issues.append(f"Missing or empty: {rel}")
        if missing_sections:
            issues.append(f"Missing required headings in {rel}: {', '.join(missing_sections)}")
        if broken:
            issues.append(f"Broken local evidence links in {rel}: {', '.join(broken)}")

    gi = _read(root, ".gitignore")
    if f"{DOCS_DIR}/" not in gi and DOCS_DIR not in gi.splitlines():
        issues.append(f"Git warning: '{DOCS_DIR}/' is not in .gitignore.")

    declared = _completion_declared(root)
    gate = None
    if declared:
        gate = validate_completion_checklist(args)
        issues.extend(f"Completion gate: {i}" for i in gate["issues"])
    return {"valid": not issues, "issues": issues, "artifacts": results, "ui_jargon_leaks_count": len(leaks), "docs_dir": DOCS_DIR,
            "completion_declared": declared, "completion_gate": gate}


# ---------------------------------------------------------------- design and browser

def get_skills_dir() -> Path:
    base = Path(__file__).resolve().parent.parent / "skills"
    if base.is_dir():
        return base
    for candidate in (os.environ.get("SQUAD_SKILLS_DIR"), Path.home() / ".gemini" / "antigravity-cli" / "skills", Path.home() / ".claude" / "skills"):
        if candidate and Path(candidate).is_dir():
            return Path(candidate)
    return base


def get_design_reference(args: dict[str, Any]) -> dict[str, Any]:
    company = (args.get("company") or "").strip().lower()
    query = (args.get("query") or "").strip().lower()
    catalog = get_skills_dir() / "design-reference" / "design-md"
    if not catalog.is_dir():
        return {"error": f"design-md catalog not found at {catalog}"}
    companies = sorted(d.name for d in catalog.iterdir() if d.is_dir())

    def doc_of(name: str) -> Path | None:
        for fname in ("DESIGN.md", "README.md"):
            if (catalog / name / fname).is_file():
                return catalog / name / fname
        return None

    if not company and not query:
        return {"total_companies": len(companies), "companies": companies,
                "message": "Pass 'company' (e.g. 'linear', 'stripe', 'vercel', 'supabase') for the full contract, or 'query' to search patterns."}
    if company:
        for rule in (lambda c: c.lower() == company, lambda c: c.lower().startswith(company), lambda c: company in c.lower()):
            hit = next((c for c in companies if rule(c)), None)
            if hit:
                f = doc_of(hit)
                return {"company": hit, "file": f.name if f else None, "content": f.read_text(encoding="utf-8", errors="replace") if f else ""}
        return {"error": f"Company '{company}' not found in the reference catalog.",
                "suggestions": [c for c in companies if len(company) >= 2 and company[:2] in c.lower()][:8]}
    matches = []
    for c in companies:
        f = doc_of(c)
        if not f:
            continue
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        snippets = ["\n".join(lines[max(0, i - 1):i + 3]) for i, line in enumerate(lines) if query in line.lower()][:2]
        if snippets:
            matches.append({"company": c, "snippets": snippets})
    return {"query": query, "matched_count": len(matches), "results": matches[:15]}


def run_playwright_cli(args: dict[str, Any]) -> dict[str, Any]:
    cmd = (args.get("command") or "snapshot").strip().lower()
    url = (args.get("url") or "").strip()
    viewport = (args.get("viewport") or "desktop").strip().lower()
    output_path = args.get("output_path")
    script = get_skills_dir() / "playwright-cli" / "playwright-cli.js"
    if not script.is_file():
        raise SquadError(f"playwright-cli.js not found at {script} (install with --with-heavy-skills)")
    if cmd not in {"open", "close", "snapshot", "console", "requests", "resize", "screenshot"}:
        raise SquadError(f"Playwright command not allowed: {cmd}")
    cli = ["node", str(script)]
    if cmd == "open":
        if not re.match(r"^https?://", url, re.IGNORECASE):
            raise SquadError("'open' needs a url starting with http:// or https://")
        cli += ["open", url]
    elif cmd == "resize":
        sizes = {"mobile": ["390", "844"], "desktop": ["1440", "900"]}
        cli += ["resize", *(sizes.get(viewport) or (viewport.split("x") if re.fullmatch(r"\d{3,4}x\d{3,4}", viewport) else sizes["desktop"]))]
    elif cmd == "screenshot":
        cli.append("screenshot")
        if not output_path and args.get("project_root"):
            evid = project_root(args["project_root"]) / DOCS_DIR / EVIDENCE_DIR / "frontend"
            evid.mkdir(parents=True, exist_ok=True)
            output_path = str(evid / f"screenshot_{viewport}_{date.today().isoformat()}.png")
        if output_path:
            cli += ["--filename", output_path]
    else:
        cli.append(cmd)
    try:
        proc = subprocess.run(cli, capture_output=True, text=True, timeout=30)
        return {"command": cmd, "exit_code": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip(),
                "output_path": output_path, "success": proc.returncode == 0}
    except subprocess.TimeoutExpired:
        return {"command": cmd, "success": False, "error": "playwright-cli timed out after 30s"}
    except Exception as exc:
        return {"command": cmd, "success": False, "error": str(exc)}


# ---------------------------------------------------------------- run_checks

CHECK_KINDS = ("lint", "typecheck", "build", "test", "db")
DEFAULT_KINDS = ["lint", "typecheck", "build", "test"]


def _detect_checks(root: Path, files: list[str]) -> list[dict[str, Any]]:
    """Known build/test commands per detected stack. Never arbitrary commands."""
    checks: list[dict[str, Any]] = []
    solutions = sorted((f for f in files if f.lower().endswith((".sln", ".slnx"))), key=len)
    projects = sorted((f for f in files if f.lower().endswith(".csproj")), key=len)
    target = solutions[0] if solutions else (projects[0] if projects else None)
    if target:
        checks.append({"kind": "build", "stack": ".NET", "cwd": ".", "cmd": ["dotnet", "build", target, "--nologo"]})
        checks.append({"kind": "test", "stack": ".NET", "cwd": ".", "cmd": ["dotnet", "test", target, "--nologo"]})
    for f in files:
        if Path(f).name != "package.json":
            continue
        folder = Path(f).parent.as_posix()
        pkg_dir = root / folder
        try:
            scripts = json.loads(_read(root, f)).get("scripts") or {}
        except Exception:
            continue
        runner = "pnpm" if (pkg_dir / "pnpm-lock.yaml").exists() else "yarn" if (pkg_dir / "yarn.lock").exists() else "npm"
        run = [runner] if runner == "yarn" else [runner, "run"]
        install = [runner, "ci"] if runner == "npm" and (pkg_dir / "package-lock.json").exists() else [runner, "install"]
        node = {"stack": "Node", "cwd": folder, "install": install, "needs_install": not (pkg_dir / "node_modules").is_dir()}
        if "lint" in scripts:
            checks.append({"kind": "lint", "cmd": [*run, "lint"], **node})
        typecheck = next((s for s in ("typecheck", "type-check", "tsc") if s in scripts), None)
        if typecheck:
            checks.append({"kind": "typecheck", "cmd": [*run, typecheck], **node})
        elif (pkg_dir / "tsconfig.json").is_file():
            checks.append({"kind": "typecheck", "cmd": ["npx", "--no-install", "tsc", "--noEmit"], **node})
        if "build" in scripts:
            checks.append({"kind": "build", "cmd": [*run, "build"], **node})
        test_script = str(scripts.get("test", ""))
        if test_script and "no test specified" not in test_script:
            checks.append({"kind": "test", "cmd": [runner, "test"], **node})
    if any(f.startswith("supabase/tests/") and f.endswith(".sql") for f in files):
        checks.append({"kind": "db", "stack": "Supabase", "cwd": ".", "cmd": ["supabase", "test", "db"]})
    if any(Path(f).name in ("pyproject.toml", "requirements.txt", "pytest.ini") for f in files) and \
            any(re.search(r"(^|/)(tests?/|test_[^/]*\.py$|[^/]*_test\.py$)", f) for f in files):
        checks.append({"kind": "test", "stack": "Python", "cwd": ".", "cmd": ["python", "-m", "pytest", "-q"]})
    if "go.mod" in files:
        checks += [{"kind": "build", "stack": "Go", "cwd": ".", "cmd": ["go", "build", "./..."]},
                   {"kind": "test", "stack": "Go", "cwd": ".", "cmd": ["go", "test", "./..."]}]
    if "Cargo.toml" in files:
        checks += [{"kind": "build", "stack": "Rust", "cwd": ".", "cmd": ["cargo", "build"]},
                   {"kind": "test", "stack": "Rust", "cwd": ".", "cmd": ["cargo", "test"]}]
    return checks


def run_checks(args: dict[str, Any]) -> dict[str, Any]:
    root = project_root(args.get("project_root", ""))
    only = args.get("only") or DEFAULT_KINDS
    if not isinstance(only, list) or not all(k in CHECK_KINDS for k in only):
        raise SquadError(f"'only' must be a list of: {', '.join(CHECK_KINDS)}")
    timeout = max(10, min(int(args.get("timeout_seconds") or 300), 1800))
    install = bool(args.get("install", False))
    planned = [c for c in _detect_checks(root, list_files(root)) if c["kind"] in only]
    if not planned:
        return {"project_root": str(root), "ran": 0, "all_passed": False, "results": [],
                "message": "No build/test command detected. Record the real commands in .squad/stack.md and run them by hand."}

    env = {**os.environ, "CI": "1", "DOTNET_NOLOGO": "1", "DOTNET_CLI_TELEMETRY_OPTOUT": "1"}
    results: list[dict[str, Any]] = []
    for c in planned:
        cwd = root if c["cwd"] == "." else safe_path(root, c["cwd"])
        entry: dict[str, Any] = {"kind": c["kind"], "stack": c["stack"], "cwd": c["cwd"], "command": " ".join(c["cmd"])}
        exe = shutil.which(c["cmd"][0])
        if not exe:
            entry.update(status="missing_tool", message=f"'{c['cmd'][0]}' not found on PATH")
            results.append(entry)
            continue
        if c.get("needs_install"):
            if not install:
                entry.update(status="needs_install", message=f"Dependencies not installed in {c['cwd']}. Run again with install=true ({' '.join(c['install'])}).")
                results.append(entry)
                continue
            try:
                inst = subprocess.run([shutil.which(c["install"][0]) or c["install"][0], *c["install"][1:]], cwd=str(cwd),
                                      capture_output=True, text=True, timeout=timeout, env=env)
                if inst.returncode != 0:
                    entry.update(status="install_failed", exit_code=inst.returncode, output_tail=(inst.stdout + inst.stderr)[-3000:])
                    results.append(entry)
                    continue
                c["needs_install"] = False
            except Exception as exc:
                entry.update(status="install_failed", message=str(exc))
                results.append(entry)
                continue
        try:
            proc = subprocess.run([exe, *c["cmd"][1:]], cwd=str(cwd), capture_output=True, text=True, timeout=timeout, env=env)
            entry.update(status="passed" if proc.returncode == 0 else "failed", exit_code=proc.returncode,
                         output_tail=(proc.stdout + "\n" + proc.stderr).strip()[-3000:])
        except subprocess.TimeoutExpired:
            entry.update(status="timeout", message=f"Exceeded {timeout}s")
        except Exception as exc:
            entry.update(status="error", message=str(exc))
        results.append(entry)

    evid = safe_path(root, docs(f"{EVIDENCE_DIR}/run_checks.md"))
    evid.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"\n## run_checks — {date.today().isoformat()}\n\n", "| Kind | Command | Folder | Status | Exit |\n|---|---|---|---|---|\n"]
    lines += [f"| {r['kind']} | `{r['command']}` | {r['cwd']} | {r['status']} | {r.get('exit_code', '-')} |\n" for r in results]
    with open(evid, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("".join(lines))
    return {"project_root": str(root), "ran": len(results), "all_passed": all(r["status"] == "passed" for r in results),
            "evidence_file": docs(f"{EVIDENCE_DIR}/run_checks.md"), "results": results}


# ---------------------------------------------------------------- MCP plumbing

def _root_schema(extra: dict[str, Any] | None = None, required: list[str] | None = None) -> dict[str, Any]:
    props = {"project_root": {"type": "string", "description": "Absolute path of the target project"}, **(extra or {})}
    return {"type": "object", "properties": props, "required": required if required is not None else ["project_root"]}


TOOLS = [
    {"name": "inspect_project", "description": "Lists files, detects stacks (incl. Next.js, Vite, Vercel, Supabase), persistence, auth, configs, UI jargon and the declared .squad/stack.md.",
     "inputSchema": _root_schema()},
    {"name": "run_checks", "description": "Runs REAL lint, typecheck, build and tests detected for the stack (dotnet, npm/pnpm/yarn, pytest, go, cargo, supabase test db) and returns status, exit code and output tail; appends evidence to .squad/evidence/run_checks.md. Never runs arbitrary commands.",
     "inputSchema": _root_schema({"only": {"type": "array", "items": {"type": "string", "enum": list(CHECK_KINDS)}, "description": "Default: lint, typecheck, build, test. 'db' runs supabase test db (needs supabase start)."},
                                  "install": {"type": "boolean", "description": "Install missing Node dependencies first (npm ci/install). Default: false"},
                                  "timeout_seconds": {"type": "integer", "description": "Per-command timeout (10-1800, default 300)"}})},
    {"name": "audit_code_delivery", "description": "Mechanical scan for shortcuts: simulated latency, Math.random IDs, hardcoded metrics, embedded mocks, swallowed errors (JS/TS/C#/Python/Go) and UI jargon.",
     "inputSchema": _root_schema()},
    {"name": "audit_security_controls", "description": "Security heuristics: mutations without auth (.NET [Authorize], Next.js Route Handlers/Server Actions), Supabase tables without RLS, using(true) policies, security definer without search_path, hardcoded secrets, privileged key in client code, secret-like NEXT_PUBLIC_/VITE_ variables, .env not ignored, missing security tests, unencrypted third-party credentials.",
     "inputSchema": _root_schema()},
    {"name": "audit_frontend_taste", "description": "Scans the UI for generic AI copy, arbitrary hex colors/spacing and missing reduced-motion handling (taste-skill heuristics).",
     "inputSchema": _root_schema()},
    {"name": "initialize_squad_docs", "description": "Creates .squad/ with an index, one report per agent (required headings included), roadmap and project map, and adds .squad/ to .gitignore. Never overwrites existing files.",
     "inputSchema": _root_schema()},
    {"name": "update_agent_report", "description": "Creates or replaces an agent's full report in .squad/.",
     "inputSchema": _root_schema({"agent": {"type": "string", "enum": list(AGENTS)}, "content": {"type": "string"}}, ["project_root", "agent", "content"])},
    {"name": "update_roadmap", "description": "Creates or replaces .squad/coordination/roadmap.md.",
     "inputSchema": _root_schema({"content": {"type": "string"}}, ["project_root", "content"])},
    {"name": "validate_squad_artifacts", "description": "Checks that reports exist with their required headings, local evidence links resolve, DBA persistence is honest, UI has no jargon, and runs the completion gate when the roadmap declares items DONE.",
     "inputSchema": _root_schema()},
    {"name": "validate_completion_checklist", "description": "Validates the independent finalizer's acceptance: every gate needs a status and evidence; blocks gaps, rejections and tests without command/result.",
     "inputSchema": _root_schema()},
    {"name": "get_design_reference", "description": "Queries the bundled catalog of reference DESIGN.md files (Linear, Stripe, Vercel, Supabase, Apple...) by company or free-text query.",
     "inputSchema": {"type": "object", "properties": {"company": {"type": "string", "description": "Reference company (e.g. 'linear', 'stripe', 'vercel')"},
                                                      "query": {"type": "string", "description": "Free-text search (e.g. 'dark mode', 'tokens', 'spacing')"}}}},
    {"name": "run_playwright_cli", "description": "Runs allowed Microsoft Playwright CLI commands (open, snapshot, screenshot, console, requests, resize, close) to capture real browser evidence.",
     "inputSchema": {"type": "object", "properties": {
         "command": {"type": "string", "enum": ["open", "snapshot", "screenshot", "console", "requests", "resize", "close"]},
         "url": {"type": "string", "description": "App URL (e.g. http://localhost:3000)"},
         "viewport": {"type": "string", "description": "desktop (1440x900), mobile (390x844) or WIDTHxHEIGHT"},
         "project_root": {"type": "string", "description": "Project root (screenshots go to .squad/evidence/frontend/)"},
         "output_path": {"type": "string", "description": "Explicit screenshot path"}}, "required": ["command"]}},
]
HANDLERS = {"inspect_project": inspect_project, "run_checks": run_checks, "audit_code_delivery": audit_code_delivery,
            "audit_security_controls": audit_security_controls, "audit_frontend_taste": audit_frontend_taste,
            "initialize_squad_docs": initialize_docs, "update_agent_report": update_report, "update_roadmap": update_roadmap,
            "validate_squad_artifacts": validate_artifacts, "validate_completion_checklist": validate_completion_checklist,
            "get_design_reference": get_design_reference, "run_playwright_cli": run_playwright_cli}


def respond(message: dict[str, Any]) -> dict[str, Any] | None:
    method, ident, params = message.get("method"), message.get("id"), message.get("params") or {}
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": ident, "result": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {"listChanged": False}},
                                                          "serverInfo": {"name": "squad", "version": SERVER_VERSION}}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": ident, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": ident, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        try:
            if name not in HANDLERS:
                raise SquadError(f"Unknown tool: {name}")
            result = HANDLERS[name](params.get("arguments") or {})
            return {"jsonrpc": "2.0", "id": ident, "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}],
                                                              "structuredContent": result}}
        except Exception as exc:
            return {"jsonrpc": "2.0", "id": ident, "result": {"isError": True, "content": [{"type": "text", "text": str(exc)}]}}
    if ident is not None:
        return {"jsonrpc": "2.0", "id": ident, "error": {"code": -32601, "message": f"Unknown method: {method}"}}
    return None


def main() -> None:
    for stream in (sys.stdin, sys.stdout):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    for line in sys.stdin:
        line = line.strip().lstrip("﻿")
        if not line:
            continue
        try:
            result = respond(json.loads(line))
        except json.JSONDecodeError:
            result = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
        if result is not None:
            sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
