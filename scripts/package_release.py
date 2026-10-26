"""Create a source-only release; never traverse runtime directories or include credentials."""

from pathlib import Path
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = [
    "backend",
    "docs",
    "evaluation",
    "migrations",
    "phase-00",
    "scripts",
    "tests",
    ".github",
    "frontend/app",
    "frontend/e2e",
    "frontend/public",
]
ROOT_FILES = [
    "README.md",
    "AGENTS.md",
    "pyproject.toml",
    "alembic.ini",
    "compose.yaml",
    ".env.example",
    ".gitignore",
    ".dockerignore",
    "requirements-local.lock",
    "frontend/AGENTS.md",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/tsconfig.json",
    "frontend/next-env.d.ts",
    "frontend/next.config.ts",
    "frontend/playwright.config.ts",
    "frontend/Dockerfile",
    "frontend/.dockerignore",
]
ARTIFACTS = [
    "sample-audit.json",
    "evaluation-development.json",
    "evaluation-held_out.json",
    "research-checks.json",
    "verification-summary.json",
    "lexical-cli.json",
    "browser-tests.json",
    "typography-checks.json",
    "welcome-desktop.png",
    "audit-desktop.png",
    "audit-mobile.png",
    "source-desktop.png",
    "experiments-desktop.png",
]


def check_links():
    for path in [
        ROOT / "README.md",
        *sorted((ROOT / "docs").glob("*.md")),
        *sorted((ROOT / "phase-00").rglob("*.md")),
    ]:
        content = path.read_text(encoding="utf-8")
        assert "\ufffd" not in content, path
        for target in re.findall(r"\]\(([^)]+)\)", content):
            if "://" in target or target.startswith("#"):
                continue
            relative = target.split("#")[0]
            assert (path.parent / relative).is_file(), (path, target)


def main():
    check_links()
    selected = set()
    for name in FOLDERS:
        for path in (ROOT / name).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}:
                selected.add(path)
    selected.update(ROOT / name for name in ROOT_FILES)
    selected.update(ROOT / "artifacts" / name for name in ARTIFACTS if (ROOT / "artifacts" / name).exists())
    assert all(path.is_file() for path in selected)
    manifest = {}
    output = ROOT / "AI-Auditor-v1.0.zip"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(selected):
            relative = path.relative_to(ROOT).as_posix()
            assert not relative.startswith((".venv", ".data"))
            assert path.name != ".env"
            assert "node_modules" not in path.parts and "test-results" not in path.parts
            data = path.read_bytes()
            manifest[relative] = hashlib.sha256(data).hexdigest()
            archive.writestr("AI-Auditor/" + relative, data)
        archive.writestr("AI-Auditor/release-manifest.json", json.dumps(manifest, indent=2))
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert "AI-Auditor/backend/api.py" in archive.namelist()
        assert "AI-Auditor/frontend/app/page.tsx" in archive.namelist()
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    (ROOT / "AI-Auditor-v1.0.sha256").write_text(checksum + "  " + output.name + "\n", encoding="utf-8")
    print("Archive:", output.name)
    print("Source/artifact files:", len(selected))
    print("Archive bytes:", output.stat().st_size)
    print("SHA256:", checksum)
    print("PASS: local links, ZIP integrity and source-only allowlist.")


if __name__ == "__main__":
    main()
