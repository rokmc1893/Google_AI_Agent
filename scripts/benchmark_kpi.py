#!/usr/bin/env python3
"""
스크리닝 KPI 벤치마크 — SLA(기본 180초) 충족 여부 출력.
사용: PYTHONPATH=. python scripts/benchmark_kpi.py [--base http://127.0.0.1:8000]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read())


def upload_file(base: str, path: Path) -> dict:
    boundary = "----DeepgleBoundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        f"Content-Type: text/plain\r\n\r\n"
    ).encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{base}/api/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--contract",
        default="fixtures/sample_contract.txt",
    )
    args = parser.parse_args()
    base = args.base.rstrip("/")
    contract = Path(args.contract)
    if not contract.exists():
        print(f"FAIL contract not found: {contract}")
        return 1

    print(f"[KPI] base={base} contract={contract.name}")
    t0 = time.perf_counter()

    try:
        upload = upload_file(base, contract)
        job_id = upload["job_id"]
        print(f"[KPI] upload ok job_id={job_id[:8]}…")

        post_json(f"{base}/api/screen", {"job_id": job_id})
        elapsed_ms = (time.perf_counter() - t0) * 1000

        result = get_json(f"{base}/api/result/{job_id}")
        metrics = get_json(f"{base}/api/metrics")

        sla_s = metrics.get("screen_sla_seconds", 180)
        sla_ms = sla_s * 1000
        ok_sla = elapsed_ms <= sla_ms

        print(f"[KPI] e2e_ms={elapsed_ms:.0f} api_last_screen_ms={metrics.get('last_screen_ms')}")
        print(f"[KPI] verified_issues={len(result.get('verified_issues', []))}")
        print(f"[KPI] SLA {sla_s}s → {'OK' if ok_sla else 'FAIL'}")
        print(f"OK P5-Step4 benchmark sla_met={ok_sla}")

        return 0 if ok_sla else 2
    except urllib.error.URLError as exc:
        print(f"FAIL server not reachable: {exc}")
        print("Hint: PYTHONPATH=. uvicorn backend.main:app --port 8000")
        return 1


if __name__ == "__main__":
    sys.exit(main())
