from __future__ import annotations

import argparse
import json
import time
from statistics import mean, median

import httpx


def _poll_task(client: httpx.Client, base_url: str, task_id: str, poll_interval: float, timeout_s: float) -> dict:
    deadline = time.monotonic() + timeout_s
    while True:
        response = client.get(f"{base_url}/status/{task_id}", timeout=timeout_s)
        response.raise_for_status()
        status = response.json()
        if status.get("status") in {"completed", "failed"}:
            return status
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Task {task_id} did not complete within {timeout_s} seconds")
        time.sleep(poll_interval)


def run_benchmark(base_url: str, user_id: int, clothing_item_id: int, rounds: int, poll_interval: float, timeout_s: float) -> dict:
    create_latencies: list[float] = []
    total_latencies: list[float] = []
    results: list[dict] = []

    with httpx.Client(timeout=timeout_s) as client:
        for index in range(rounds):
            started = time.perf_counter()
            response = client.post(
                f"{base_url}/tasks/generate-texture",
                json={"user_id": user_id, "clothing_item_id": clothing_item_id},
            )
            response.raise_for_status()
            create_elapsed = time.perf_counter() - started

            task = response.json()
            task_id = task["task_id"]
            completed_at = time.perf_counter()
            final_status = _poll_task(client, base_url, task_id, poll_interval, timeout_s)
            total_elapsed = time.perf_counter() - started

            create_latencies.append(create_elapsed)
            total_latencies.append(total_elapsed)
            results.append(
                {
                    "round": index + 1,
                    "task_id": task_id,
                    "create_seconds": round(create_elapsed, 4),
                    "poll_seconds": round(time.perf_counter() - completed_at, 4),
                    "total_seconds": round(total_elapsed, 4),
                    "status": final_status.get("status"),
                }
            )

    return {
        "rounds": rounds,
        "create_mean_seconds": round(mean(create_latencies), 4) if create_latencies else 0.0,
        "create_median_seconds": round(median(create_latencies), 4) if create_latencies else 0.0,
        "total_mean_seconds": round(mean(total_latencies), 4) if total_latencies else 0.0,
        "total_median_seconds": round(median(total_latencies), 4) if total_latencies else 0.0,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark latency cho /tasks/generate-texture")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--user-id", type=int, default=1)
    parser.add_argument("--clothing-item-id", type=int, default=1)
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--poll-interval", type=float, default=0.5)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()

    report = run_benchmark(
        base_url=args.base_url.rstrip("/"),
        user_id=args.user_id,
        clothing_item_id=args.clothing_item_id,
        rounds=max(1, args.rounds),
        poll_interval=max(0.1, args.poll_interval),
        timeout_s=max(1.0, args.timeout),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()