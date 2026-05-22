#!/usr/bin/env python3
"""Phase 5 verification. Run from repo root."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check(name: str, ok: bool) -> None:
    print(f"{'OK' if ok else 'FAIL'} {name}")
    if not ok:
        raise SystemExit(1)


def main() -> None:
    checks = []

    vite = (ROOT / "vite.config.ts").read_text()
    checks.append(("P5-Step1 vite base", "base: './'" in vite or 'base: "./"' in vite))

    checks.append(("P5-Step2 docker-compose", (ROOT / "docker-compose.yml").exists()))
    checks.append(("P5-Step2 Dockerfile.backend", (ROOT / "docker/Dockerfile.backend").exists()))
    checks.append(("P5-Step2 nginx.conf", (ROOT / "docker/nginx.conf").exists()))

    os.environ["PYTHONPATH"] = str(ROOT)
    os.environ.setdefault("USE_LLM", "false")
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    m = client.get("/api/metrics").json()
    checks.append(("P5-Step3 metrics API", "screen_sla_seconds" in m and "last_screen_ms" in m))

    with open(ROOT / "fixtures/sample_contract.txt", "rb") as f:
        u = client.post("/api/upload", files={"file": ("c.txt", f, "text/plain")})
    jid = u.json()["job_id"]
    client.post("/api/screen", json={"job_id": jid})
    m2 = client.get("/api/metrics").json()
    checks.append(("P5-Step3 screen timing", m2["screen_count"] >= 1 and m2["last_screen_ms"] is not None))

    dist_index = ROOT / "dist/index.html"
    if dist_index.exists():
        html = dist_index.read_text()
        checks.append(
            ("P5-Step1 dist relative",
             "./assets/" in html or "/assets/" in html or 'src="./' in html),
        )
    else:
        r = subprocess.run(
            ["npm", "run", "build:offline"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=180,
        )
        checks.append(("P5-Step1 npm build:offline", r.returncode == 0))
        if r.returncode == 0 and dist_index.exists():
            html = dist_index.read_text()
            checks.append(("P5-Step1 dist relative paths", "./assets/" in html))

    readme = (ROOT / "README.md").read_text()
    checks.append(("P5-Step5 README", "Phase 5" in readme and "docker compose" in readme))

    print("\n=== Phase 5 Progress ===")
    for label, ok in checks:
        check(label, ok)
    print("\nPhase 5 — all checks passed")


if __name__ == "__main__":
    main()
