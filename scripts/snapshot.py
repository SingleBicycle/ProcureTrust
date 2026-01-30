#!/usr/bin/env python3
"""Generate and update STATUS.md SNAPSHOT block.

This script is designed to be resilient in sparse repos or when optional
Python dependencies are missing. It fills missing data with "(missing)".
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


BEGIN_MARKER = "<!-- SNAPSHOT:BEGIN -->"
END_MARKER = "<!-- SNAPSHOT:END -->"

IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".idea",
    ".vscode",
}

TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".sql",
    ".ini",
    ".cfg",
    ".sh",
    ".txt",
}

VECTOR_KEYWORDS = [
    "pgvector",
    "chroma",
    "weaviate",
    "milvus",
    "faiss",
    "vectorstore",
    "vector_store",
    "embedding",
]

KG_RULE_EXTS = {".yaml", ".yml", ".json"}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def run_cmd(cmd: Sequence[str], cwd: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            list(cmd),
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def iter_files(root: Path) -> Iterable[Path]:
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for name in files:
            yield Path(base) / name


def iter_text_files(root: Path) -> Iterable[Path]:
    for path in iter_files(root):
        if path.suffix.lower() in TEXT_EXTENSIONS:
            yield path


def git_info(root: Path) -> Tuple[str, str, str]:
    inside = run_cmd(["git", "rev-parse", "--is-inside-work-tree"], root)
    if inside != "true":
        return "(missing)", "(missing)", "(missing)"

    branch = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], root)
    last_commit = run_cmd(["git", "log", "-1", "--oneline"], root)
    dirty_output = run_cmd(["git", "status", "--porcelain"], root)
    if dirty_output is None:
        dirty = "(missing)"
    else:
        dirty = "yes" if dirty_output.strip() else "no"
    return branch or "(missing)", last_commit or "(missing)", dirty


def render_tree(root: Path, max_depth: int = 2, max_entries: int = 200) -> List[str]:
    lines: List[str] = []
    if not root.exists():
        return [f"- {root.name}/ (missing)"]

    lines.append(f"- {root.name}/")
    count = 0
    for base, dirs, files in os.walk(root):
        rel_base = Path(base).relative_to(root)
        depth = len(rel_base.parts)
        if depth >= max_depth:
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        indent = "  " * (depth + 1)
        for name in sorted(dirs):
            lines.append(f"{indent}- {name}/")
            count += 1
            if count >= max_entries:
                lines.append(f"{indent}- ... (truncated)")
                return lines
        for name in sorted(files):
            lines.append(f"{indent}- {name}")
            count += 1
            if count >= max_entries:
                lines.append(f"{indent}- ... (truncated)")
                return lines
    return lines


def can_import_as_package(module_path: Path, root: Path) -> bool:
    try:
        rel_path = module_path.relative_to(root)
    except ValueError:
        return False
    parts = rel_path.parts[:-1]
    for i in range(1, len(parts) + 1):
        init_path = root.joinpath(*parts[:i], "__init__.py")
        if not init_path.exists():
            return False
    return True


def import_module_from_path(module_path: Path, root: Path):
    try:
        rel_path = module_path.relative_to(root).with_suffix("")
        module_name = "_snapshot_" + "_".join(rel_path.parts)
    except ValueError:
        module_name = "_snapshot_module"
    if can_import_as_package(module_path, root):
        rel_path = module_path.relative_to(root).with_suffix("")
        dotted = ".".join(rel_path.parts)
        return __import__(dotted, fromlist=["*"])

    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location(module_name, str(module_path))
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


def find_fastapi_app(root: Path) -> Tuple[Optional[object], Optional[Path], str]:
    api_dir = root / "apps" / "api"
    if not api_dir.exists():
        return None, None, "apps/api missing"

    try:
        from fastapi import FastAPI  # type: ignore
    except Exception as exc:
        return None, None, f"fastapi import failed: {exc}"

    candidates: List[Path] = []
    for path in iter_files(api_dir):
        if path.suffix != ".py":
            continue
        try:
            text = read_text(path)
        except Exception:
            continue
        if "FastAPI" in text:
            candidates.append(path)

    # Prioritize common entrypoints
    priority = [
        api_dir / "main.py",
        api_dir / "app.py",
        api_dir / "__init__.py",
    ]
    ordered = []
    for p in priority:
        if p in candidates:
            ordered.append(p)
    for p in candidates:
        if p not in ordered:
            ordered.append(p)

    for path in ordered:
        module = import_module_from_path(path, root)
        if module is None:
            continue
        for value in module.__dict__.values():
            try:
                if isinstance(value, FastAPI):
                    return value, path, ""
            except Exception:
                continue

    return None, None, "FastAPI app not found"


def openapi_from_app(app: object) -> Optional[Dict[str, object]]:
    try:
        return app.openapi()  # type: ignore[attr-defined]
    except Exception:
        return None


def list_router_files(api_dir: Path) -> List[str]:
    files: List[str] = []
    for path in iter_files(api_dir):
        if path.suffix != ".py":
            continue
        try:
            text = read_text(path)
        except Exception:
            continue
        if "APIRouter" in text:
            files.append(str(path))
    return sorted(files)


def extract_endpoints(openapi: Dict[str, object]) -> List[str]:
    endpoints: List[str] = []
    paths = openapi.get("paths") if isinstance(openapi, dict) else None
    if not isinstance(paths, dict):
        return endpoints
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, spec in methods.items():
            if method.startswith("x-"):
                continue
            summary = ""
            if isinstance(spec, dict):
                summary = str(spec.get("summary") or spec.get("operationId") or "")
            entry = f"{method.upper()} {path}"
            if summary:
                entry += f" - {summary}"
            endpoints.append(entry)
    return sorted(endpoints)


def detect_openapi_base_url(openapi: Dict[str, object]) -> str:
    servers = openapi.get("servers") if isinstance(openapi, dict) else None
    if isinstance(servers, list) and servers:
        first = servers[0]
        if isinstance(first, dict) and "url" in first:
            return str(first["url"])
    return "(missing)"


def find_openapi_files(root: Path) -> List[str]:
    candidates = []
    for path in iter_files(root):
        if path.name.lower() in {"openapi.json", "openapi.yaml", "openapi.yml"}:
            candidates.append(str(path))
    return sorted(candidates)


def find_graph_module(root: Path) -> Optional[Path]:
    candidates = [
        root / "apps" / "api" / "services" / "orchestrator" / "graph.py",
        root / "apps" / "api" / "orchestrator" / "graph.py",
        root / "apps" / "api" / "services" / "graph.py",
        root / "apps" / "api" / "graph.py",
    ]
    for path in candidates:
        if path.exists():
            return path
    api_dir = root / "apps" / "api"
    if not api_dir.exists():
        return None
    for path in iter_files(api_dir):
        if path.name == "graph.py":
            return path
    return None


def parse_graph_static(text: str) -> Tuple[List[str], List[str]]:
    nodes = set()
    edges = set()

    for match in re.findall(r"add_node\(\s*['\"]([^'\"]+)['\"]", text):
        nodes.add(match)

    for match in re.findall(
        r"add_edge\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]",
        text,
    ):
        if len(match) == 2:
            edges.add(f"{match[0]} -> {match[1]}")

    return sorted(nodes), sorted(edges)


def parse_stage_values(text: str) -> List[str]:
    stages = set()
    for match in re.findall(r"Stage\s*([A-D])", text, flags=re.IGNORECASE):
        stages.add(f"Stage {match.upper()}")
    for match in re.findall(r"stage[_\s-]?([a-d])", text, flags=re.IGNORECASE):
        stages.add(f"Stage {match.upper()}")
    return sorted(stages)


def detect_ready_gate(text: str) -> str:
    if re.search(r"ready\s*gate", text, flags=re.IGNORECASE):
        return "yes"
    if re.search(r"ready_gate", text, flags=re.IGNORECASE):
        return "yes"
    if re.search(r"readyGate", text, flags=re.IGNORECASE):
        return "yes"
    return "no"


def schema_info(schema_path: Path) -> Tuple[str, List[str], List[str]]:
    data = json.loads(read_text(schema_path))
    version = "(missing)"
    if isinstance(data, dict):
        if "version" in data:
            version = str(data["version"])
        elif "$id" in data:
            version = str(data["$id"])
        elif "title" in data:
            version = str(data["title"])

    properties = []
    if isinstance(data, dict) and isinstance(data.get("properties"), dict):
        properties = list(data["properties"].keys())

    required = []
    if isinstance(data, dict) and isinstance(data.get("required"), list):
        required = [str(x) for x in data["required"]]

    return version, properties, required


def extract_tables_from_text(text: str) -> List[str]:
    tables = set()
    for match in re.findall(r"create_table\(\s*['\"]([^'\"]+)['\"]", text):
        tables.add(match)
    for match in re.findall(r"__tablename__\s*=\s*['\"]([^'\"]+)['\"]", text):
        tables.add(match)
    return sorted(tables)


def list_recent_migrations(versions_dir: Path, limit: int = 5) -> List[str]:
    if not versions_dir.exists():
        return []
    files = [p for p in versions_dir.iterdir() if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [p.name for p in files[:limit]]


def find_vector_store_locations(root: Path) -> List[str]:
    hits = []
    for path in iter_files(root):
        name_lower = path.name.lower()
        if any(keyword in name_lower for keyword in VECTOR_KEYWORDS):
            hits.append(rel(path, root))
            if len(hits) >= 10:
                break
    for base, dirs, _files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for name in dirs:
            name_lower = name.lower()
            if any(keyword in name_lower for keyword in VECTOR_KEYWORDS):
                hits.append(rel(Path(base) / name, root))
                if len(hits) >= 10:
                    return sorted(set(hits))
    return sorted(set(hits))


def list_knowledge_packs(root: Path) -> List[str]:
    candidates = [root / "docs" / "knowledge", root / "data" / "knowledge"]
    packs = []
    for base in candidates:
        if base.exists() and base.is_dir():
            for item in sorted(base.iterdir()):
                packs.append(rel(item, root))
    return packs


def find_kglite_rules(root: Path) -> List[str]:
    hits = []
    for path in iter_files(root):
        if path.suffix.lower() not in KG_RULE_EXTS:
            continue
        lower = str(path).lower()
        if "kg" in lower or "rule" in lower or "knowledge" in lower:
            hits.append(rel(path, root))
            if len(hits) >= 10:
                break
    return sorted(set(hits))


def list_web_routes(root: Path) -> List[str]:
    routes = []
    for rel_dir in ["apps/web/pages", "apps/web/routes", "apps/web/app"]:
        base = root / rel_dir
        if base.exists() and base.is_dir():
            for path in iter_files(base):
                if path.is_file():
                    routes.append(rel(path, root))
    return sorted(routes)


def find_component_paths(root: Path, component_name: str) -> List[str]:
    matches = []
    comp_lower = component_name.lower()
    web_dir = root / "apps" / "web"
    if not web_dir.exists():
        return matches
    for path in iter_files(web_dir):
        if comp_lower in path.name.lower():
            matches.append(rel(path, root))
    return sorted(matches)


def parse_make_targets(makefile_path: Path) -> Dict[str, bool]:
    targets = {}
    if not makefile_path.exists():
        return targets
    text = read_text(makefile_path)
    for line in text.splitlines():
        if not line or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+)\s*:", line)
        if match:
            targets[match.group(1)] = True
    return targets


def detect_pytest_config(root: Path) -> str:
    candidates = [root / "pytest.ini", root / "setup.cfg", root / "pyproject.toml"]
    for path in candidates:
        if not path.exists():
            continue
        if path.name == "pytest.ini":
            return rel(path, root)
        if path.name == "setup.cfg":
            text = read_text(path)
            if "[tool:pytest]" in text:
                return rel(path, root)
        if path.name == "pyproject.toml":
            text = read_text(path)
            if "[tool.pytest" in text:
                return rel(path, root)
    return "(missing)"


def detect_package_json_test(root: Path) -> str:
    candidates = [root / "package.json", root / "apps" / "web" / "package.json"]
    for path in candidates:
        if not path.exists():
            continue
        try:
            data = json.loads(read_text(path))
        except Exception:
            return f"(missing)"
        scripts = data.get("scripts") if isinstance(data, dict) else None
        if isinstance(scripts, dict) and "test" in scripts:
            return f"yes ({rel(path, root)})"
        return f"no ({rel(path, root)})"
    return "(missing)"


def list_ci_workflows(root: Path) -> List[str]:
    workflows_dir = root / ".github" / "workflows"
    if not workflows_dir.exists():
        return []
    return sorted(rel(path, root) for path in workflows_dir.glob("*.y*ml"))


def scan_todos(root: Path, limit: int = 20) -> List[str]:
    results = []
    pattern = re.compile(r"\b(TODO|FIXME)\b\s*[:\-]?\s*(.*)", re.IGNORECASE)
    for path in iter_text_files(root):
        if rel(path, root) in {"STATUS.md", "scripts/snapshot.py"}:
            continue
        try:
            text = read_text(path)
        except Exception:
            continue
        for idx, line in enumerate(text.splitlines(), start=1):
            match = pattern.search(line)
            if match:
                content = match.group(0).strip()
                results.append(f"{rel(path, root)}:{idx}: {content}")
                if len(results) >= limit:
                    return results
    return results


def build_snapshot(root: Path) -> str:
    lines: List[str] = []
    lines.append("## SNAPSHOT (auto)")
    lines.append("")

    # A) Git
    lines.append("### A) Git")
    try:
        branch, last_commit, dirty = git_info(root)
    except Exception:
        branch, last_commit, dirty = "(missing)", "(missing)", "(missing)"
    lines.append(f"- Branch: {branch}")
    lines.append(f"- Last commit: {last_commit}")
    lines.append(f"- Dirty files: {dirty}")
    lines.append("")

    # B) Repo Tree
    lines.append("### B) Repo Tree (key paths)")
    for name in ["apps", "packages", "infra", "scripts"]:
        path = root / name
        try:
            lines.extend(render_tree(path))
        except Exception:
            lines.append(f"- {name}/ (missing)")
    lines.append("")

    # C) API Surface
    lines.append("### C) API Surface (FastAPI)")
    api_dir = root / "apps" / "api"
    base_url = "(missing)"
    endpoints: List[str] = []
    router_files: List[str] = []
    openapi_file = "(missing)"

    if api_dir.exists():
        try:
            app, app_path, _err = find_fastapi_app(root)
            if app is not None:
                openapi = openapi_from_app(app)
                if openapi:
                    endpoints = extract_endpoints(openapi)
                    base_url = detect_openapi_base_url(openapi)
            router_files = [rel(Path(p), root) for p in list_router_files(api_dir)]
        except Exception:
            router_files = [rel(Path(p), root) for p in list_router_files(api_dir)]
    else:
        router_files = []

    openapi_files = find_openapi_files(root)
    if openapi_files:
        openapi_file = openapi_files[0]

    lines.append(f"- Base URL: {base_url}")
    lines.append("- Endpoints summary:")
    if endpoints:
        for entry in endpoints:
            lines.append(f"  - {entry}")
    else:
        lines.append("  - (missing)")
    lines.append("- Router files (fallback):")
    if router_files:
        for path in router_files:
            lines.append(f"  - {path}")
    else:
        lines.append("  - (missing)")
    lines.append(f"- OpenAPI file path (if exported): {openapi_file}")
    lines.append("")

    # D) Orchestrator Graph
    lines.append("### D) Orchestrator Graph (LangGraph)")
    graph_path = find_graph_module(root)
    if graph_path is None:
        lines.append("- Graph module: (missing)")
        lines.append("- Nodes:")
        lines.append("  - (missing)")
        lines.append("- Edges:")
        lines.append("  - (missing)")
        lines.append("- Stage machine support:")
        lines.append("  - stage values found:")
        lines.append("    - (missing)")
        lines.append("  - ready gate: (missing)")
    else:
        lines.append(f"- Graph module: {rel(graph_path, root)}")
        nodes: List[str] = []
        edges: List[str] = []
        stages: List[str] = []
        ready_gate = "(missing)"

        try:
            module = import_module_from_path(graph_path, root)
            if module is not None and hasattr(module, "describe_graph"):
                describe_fn = getattr(module, "describe_graph")
                if callable(describe_fn):
                    info = describe_fn()
                    if isinstance(info, dict):
                        nodes = [str(x) for x in info.get("nodes", [])]
                        edges_raw = info.get("edges", [])
                        edges = []
                        for item in edges_raw:
                            if isinstance(item, (list, tuple)) and len(item) == 2:
                                edges.append(f"{item[0]} -> {item[1]}")
                            else:
                                edges.append(str(item))
                        stages = [str(x) for x in info.get("stages", [])]
        except Exception:
            pass

        if not nodes or not edges or not stages or ready_gate == "(missing)":
            try:
                text = read_text(graph_path)
            except Exception:
                text = ""
            if not nodes or not edges:
                parsed_nodes, parsed_edges = parse_graph_static(text)
                if not nodes:
                    nodes = parsed_nodes
                if not edges:
                    edges = parsed_edges
            if not stages:
                stages = parse_stage_values(text)
            ready_gate = detect_ready_gate(text) if text else "(missing)"

        lines.append("- Nodes:")
        if nodes:
            for node in nodes:
                lines.append(f"  - {node}")
        else:
            lines.append("  - (missing)")
        lines.append("- Edges:")
        if edges:
            for edge in edges:
                lines.append(f"  - {edge}")
        else:
            lines.append("  - (missing)")
        lines.append("- Stage machine support:")
        lines.append("  - stage values found:")
        if stages:
            for stage in stages:
                lines.append(f"    - {stage}")
        else:
            lines.append("    - (missing)")
        lines.append(f"  - ready gate: {ready_gate}")
    lines.append("")

    # E) Schemas
    lines.append("### E) Schemas")
    schema_path = root / "packages" / "schemas" / "schema.json"
    if schema_path.exists():
        try:
            version, properties, required = schema_info(schema_path)
        except Exception:
            version, properties, required = "(missing)", [], []
        lines.append(f"- RequirementObject version: {version}")
        lines.append(f"- schema.json path: {rel(schema_path, root)}")
        lines.append("- Top-level fields (first 30):")
        if properties:
            for name in properties[:30]:
                lines.append(f"  - {name}")
        else:
            lines.append("  - (missing)")
        lines.append("- Required fields:")
        if required:
            for name in required:
                lines.append(f"  - {name}")
        else:
            lines.append("  - (missing)")
    else:
        lines.append("- RequirementObject version: (missing)")
        lines.append("- schema.json path: (missing)")
        lines.append("- Top-level fields (first 30):")
        lines.append("  - (missing)")
        lines.append("- Required fields:")
        lines.append("  - (missing)")
    lines.append("")

    # F) DB / Migrations
    lines.append("### F) DB / Migrations")
    versions_dir = root / "apps" / "api" / "alembic" / "versions"
    if versions_dir.exists():
        recent = list_recent_migrations(versions_dir)
    else:
        recent = []

    tables: List[str] = []
    for path in [versions_dir, root / "apps" / "api"]:
        if not path.exists():
            continue
        for file_path in iter_files(path):
            if file_path.suffix != ".py":
                continue
            try:
                text = read_text(file_path)
            except Exception:
                continue
            for table in extract_tables_from_text(text):
                if table not in tables:
                    tables.append(table)
            if len(tables) >= 30:
                break
        if len(tables) >= 30:
            break

    lines.append("- DB tables (best-effort):")
    if tables:
        for name in tables[:30]:
            lines.append(f"  - {name}")
    else:
        lines.append("  - (missing)")

    lines.append("- Latest migrations:")
    if recent:
        for name in recent:
            lines.append(f"  - {name}")
    else:
        lines.append("  - (missing)")
    lines.append("")

    # G) RAG / KG-lite
    lines.append("### G) RAG / KG-lite")
    vector_hits = find_vector_store_locations(root)
    knowledge_packs = list_knowledge_packs(root)
    kg_rules = find_kglite_rules(root)

    lines.append("- Vector store locations:")
    if vector_hits:
        for item in vector_hits:
            lines.append(f"  - {item}")
    else:
        lines.append("  - (missing)")

    lines.append("- Knowledge packs:")
    if knowledge_packs:
        for item in knowledge_packs:
            lines.append(f"  - {item}")
    else:
        lines.append("  - (missing)")

    lines.append("- KG-lite rules:")
    if kg_rules:
        for item in kg_rules:
            lines.append(f"  - {item}")
    else:
        lines.append("  - (missing)")
    lines.append("")

    # H) Frontend Modules
    lines.append("### H) Frontend Modules")
    routes = list_web_routes(root)
    lines.append("- Pages/routes:")
    if routes:
        for item in routes:
            lines.append(f"  - {item}")
    else:
        lines.append("  - (missing)")

    lines.append("- Key UI components present:")
    for component in ["Chat", "CompletenessBar", "MissingList", "RFQPreview", "AssetTimeline"]:
        matches = find_component_paths(root, component)
        if matches:
            lines.append(f"  - {component}: {matches[0]}")
        else:
            lines.append(f"  - {component}: (missing)")
    lines.append("")

    # I) Tests & Commands
    lines.append("### I) Tests & Commands")
    makefile_path = root / "Makefile"
    targets = parse_make_targets(makefile_path)

    def target_status(name: str) -> str:
        if not makefile_path.exists():
            return "(missing)"
        return "yes" if targets.get(name) else "no"

    lines.append(f"- make dev: {target_status('dev')}")
    lines.append(f"- make test: {target_status('test')}")
    lines.append(f"- make snapshot: {target_status('snapshot')}")

    pytest_config = detect_pytest_config(root)
    lines.append(f"- pytest config: {pytest_config}")

    package_json_test = detect_package_json_test(root)
    lines.append(f"- package.json test script: {package_json_test}")

    workflows = list_ci_workflows(root)
    lines.append("- CI workflows:")
    if workflows:
        for workflow in workflows:
            lines.append(f"  - {workflow}")
    else:
        lines.append("  - (missing)")

    suggested = ["make snapshot"]
    if targets.get("dev"):
        suggested.append("make dev")
    if targets.get("test"):
        suggested.append("make test")
    if pytest_config != "(missing)":
        suggested.append("pytest")
    lines.append("- Suggested commands:")
    for cmd in suggested:
        lines.append(f"  - {cmd}")
    lines.append("")

    # J) Known Issues
    lines.append("### J) Known Issues (auto-collected TODO markers)")
    todos = scan_todos(root)
    lines.append("- TODO/FIXME list (top 20):")
    if todos:
        for item in todos:
            lines.append(f"  - {item}")
    else:
        lines.append("  - (missing)")

    return "\n".join(lines).rstrip() + "\n"


def replace_snapshot_block(text: str, snapshot: str) -> str:
    begin_idx = text.find(BEGIN_MARKER)
    end_idx = text.find(END_MARKER)
    if begin_idx == -1 or end_idx == -1 or end_idx < begin_idx:
        raise ValueError("SNAPSHOT markers not found or invalid order")

    before = text[: begin_idx + len(BEGIN_MARKER)]
    after = text[end_idx:]
    return f"{before}\n{snapshot}{after}"


def main() -> int:
    root = repo_root()
    status_path = root / "STATUS.md"
    if not status_path.exists():
        print("STATUS.md not found", file=sys.stderr)
        return 1

    try:
        snapshot = build_snapshot(root)
    except Exception as exc:
        print(f"Failed to build snapshot: {exc}", file=sys.stderr)
        return 1

    try:
        status_text = read_text(status_path)
        updated = replace_snapshot_block(status_text, snapshot)
        status_path.write_text(updated, encoding="utf-8")
    except Exception as exc:
        print(f"Failed to update STATUS.md: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
