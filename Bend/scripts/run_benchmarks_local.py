from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import httpx


def _wait_for_health(base_url: str, timeout_s: float = 60.0) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            response = httpx.get(f"{base_url}/health", timeout=2.0)
            if response.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(1.0)
    raise TimeoutError("Local backend did not become healthy in time")


def _run_python_script(repo_root: Path, script_relative: str, args: list[str]) -> dict:
    command = [sys.executable, script_relative, *args]
    completed = subprocess.run(
        command,
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    stdout = completed.stdout.strip()
    return json.loads(stdout) if stdout else {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Start local backend and run latency/VRAM benchmarks")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--user-id", type=int, default=1)
    parser.add_argument("--clothing-item-id", type=int, default=1)
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--skip-vram", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]

    server = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        _wait_for_health(args.base_url, timeout_s=60.0)

        latency = _run_python_script(
            repo_root,
            "Bend/scripts/benchmark_latency.py",
            [
                "--base-url",
                args.base_url,
                "--user-id",
                str(args.user_id),
                "--clothing-item-id",
                str(args.clothing_item_id),
                "--rounds",
                str(args.rounds),
                "--timeout",
                str(args.timeout),
            ],
        )

        result = {
            "latency": latency,
        }

        if not args.skip_vram:
            vram = _run_python_script(
                repo_root,
                "Bend/scripts/benchmark_vram.py",
                [
                    "--base-url",
                    args.base_url,
                    "--user-id",
                    str(args.user_id),
                    "--clothing-item-id",
                    str(args.clothing_item_id),
                    "--rounds",
                    str(args.rounds),
                    "--timeout",
                    str(args.timeout),
                ],
            )
            result["vram"] = vram

        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
