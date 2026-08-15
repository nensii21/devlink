"""
Generate TypeScript and Python SDKs from the exported OpenAPI schema.

Used by the ``sdk-generation`` GitHub Actions workflow. Requires:
  - openapi-typescript (npx) for the TypeScript SDK
  - openapi-python-client (pip) for the Python SDK

Outputs:
  - ``clients/typescript/`` — generated TS client + package.json
  - ``clients/python/``     — generated Python client package

Run from the repository root:
    python backend/scripts/generate_sdks.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CLIENTS_DIR = REPO_ROOT / "clients"
OPENAPI_FILE = CLIENTS_DIR / "openapi.json"
TYPESCRIPT_DIR = CLIENTS_DIR / "typescript"
PYTHON_DIR = CLIENTS_DIR / "python"


def _run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)


def generate_typescript() -> None:
    if not shutil.which("npx"):
        raise SystemExit(
            "npx not found; install Node.js to generate the TypeScript SDK"
        )
    _run(
        [
            "npx",
            "--yes",
            "openapi-typescript",
            str(OPENAPI_FILE),
            "-o",
            str(TYPESCRIPT_DIR / "src" / "api" / "generated.ts"),
        ]
    )


def generate_python() -> None:
    if not shutil.which("openapi-python-client"):
        _run([sys.executable, "-m", "pip", "install", "openapi-python-client"])
    _run(
        [
            "openapi-python-client",
            "generate",
            "--path",
            str(OPENAPI_FILE),
            "--output-path",
            str(PYTHON_DIR),
            "--meta",
            "setup",
            "--overwrite",
        ]
    )


def write_typescript_package() -> None:
    package_json = TYPESCRIPT_DIR / "package.json"
    package_json.parent.mkdir(parents=True, exist_ok=True)
    if package_json.exists():
        return
    package_json.write_text(
        json_pretty(
            {
                "name": "@devlink/api-client",
                "version": "1.0.0",
                "description": "Generated TypeScript client for the DevLink API.",
                "main": "dist/index.js",
                "types": "dist/index.d.ts",
                "scripts": {
                    "build": "tsc",
                    "typecheck": "tsc --noEmit",
                },
                "devDependencies": {
                    "typescript": "^5.5.0",
                },
            }
        ),
        encoding="utf-8",
    )


def json_pretty(data: object) -> str:
    import json

    return json.dumps(data, indent=2)


def main() -> None:
    if not OPENAPI_FILE.exists():
        raise SystemExit(
            f"{OPENAPI_FILE} not found. Run backend/scripts/export_openapi.py first."
        )
    (TYPESCRIPT_DIR / "src" / "api").mkdir(parents=True, exist_ok=True)
    generate_typescript()
    write_typescript_package()
    generate_python()
    print("SDK generation complete.")


if __name__ == "__main__":
    main()
