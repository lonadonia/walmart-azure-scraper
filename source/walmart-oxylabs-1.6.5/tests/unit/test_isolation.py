"""The project stands alone: its code imports only the standard library, its own package and the
dependencies it declares; it reads no file outside its folder; it has no web interface and no second
provider."""

from __future__ import annotations

import ast
import sys
import tomllib
from pathlib import Path

from tests.conftest import ROOT

SRC = ROOT / "src" / "walmart_headless"
# Import names of the declared dependencies (pyproject.toml [project] dependencies).
DECLARED = {
    "pydantic",
    "yaml",
    "sqlalchemy",
    "alembic",
    "psycopg",
    "selectolax",
    "ulid",
    "httpx",
    "azure",
}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


def test_the_code_imports_only_the_standard_library_its_package_and_declared_dependencies() -> None:
    allowed = set(sys.stdlib_module_names) | DECLARED | {"walmart_headless", "__future__"}
    for path in SRC.rglob("*.py"):
        extra = _imports(path) - allowed
        assert not extra, (path.relative_to(ROOT), extra)


def test_the_declared_dependencies_have_no_web_framework_browser_or_other_provider() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    deps = " ".join(project["dependencies"]).lower()
    for name in ("fastapi", "uvicorn", "flask", "playwright", "scrapfly", "oxylabs", "cryptography"):
        assert name not in deps
    assert project["scripts"] == {"walmart-collector": "walmart_headless.cli:entrypoint"}


def test_no_code_refers_to_the_original_application_or_files_outside_the_project() -> None:
    for path in SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for needle in (
            "import mscraper",
            "from mscraper",
            "src/mscraper",
            "deploy_validation",
            "deliverables/",
        ):
            assert needle not in text, (path.relative_to(ROOT), needle)
        assert "scrapfly" not in text.lower(), path.relative_to(ROOT)


def test_the_project_has_no_web_interface_files() -> None:
    web = [
        p.relative_to(ROOT)
        for p in ROOT.rglob("*")
        if p.suffix in (".js", ".ts", ".tsx", ".css", ".jsx")
        and not any(part in (".venv", "node_modules") for part in p.parts)
    ]
    assert web == []
