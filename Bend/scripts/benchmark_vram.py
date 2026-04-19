from __future__ import annotations

import argparse
import json
import threading
import time
from statistics import mean

import httpx

try:
    import pynvml  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional runtime dependency
    pynvml = None


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


def _measure_peak_vram(device_index: int, sample_interval: float, stop_event: threading.Event) -> dict:
    if pynvml is None:
        raise RuntimeError("pynvml is not installed. Install requirements first.")

    pynvml.nvmlInit()
    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(device_index)
        samples: list[int] = []
        total_memory = pynvml.nvmlDeviceGetMemoryInfo(handle).total
        while not stop_event.is_set():
            samples.append(pynvml.nvmlDeviceGetMemoryInfo(handle).used)
            time.sleep(sample_interval)
        samples.append(pynvml.nvmlDeviceGetMemoryInfo(handle).used)
        return {
            "peak_used_bytes": max(samples) if samples else 0,
            "avg_used_bytes": int(mean(samples)) if samples else 0,
            "total_bytes": total_memory,
        }
    finally:
        pynvml.nvmlShutdown()


def run_benchmark(base_url: str, user_id: int, clothing_item_id: int, rounds: int, poll_interval: float, timeout_s: float, device_index: int, sample_interval: float) -> dict:
    if pynvml is None:
        raise RuntimeError("pynvml is not installed. Install Bend/requirements.txt first.")

    stop_event = threading.Event()
    sampler_result: dict[str, int] = {}

    def sampler() -> None:
        nonlocal sampler_result
        sampler_result = _measure_peak_vram(device_index, sample_interval, stop_event)

    thread = threading.Thread(target=sampler, daemon=True)
    thread.start()

    request_timings: list[float] = []
    with httpx.Client(timeout=timeout_s) as client:
        for _ in range(rounds):
            started = time.perf_counter()
            response = client.post(
                f"{base_url}/tasks/generate-texture",
                json={"user_id": user_id, "clothing_item_id": clothing_item_id},
            )
            response.raise_for_status()
            task_id = response.json()["task_id"]
            _poll_task(client, base_url, task_id, poll_interval, timeout_s)
            request_timings.append(time.perf_counter() - started)

    stop_event.set()
    thread.join(timeout=5.0)

    report = {
        "rounds": rounds,
        "mean_total_seconds": round(mean(request_timings), 4) if request_timings else 0.0,
        "vram": {
            "device_index": device_index,
            "sample_interval_seconds": sample_interval,
            **sampler_result,
        },
    }
    if sampler_result.get("total_bytes"):
        report["vram"]["peak_used_mb"] = round(sampler_result["peak_used_bytes"] / 1024 / 1024, 2)
        report["vram"]["avg_used_mb"] = round(sampler_result["avg_used_bytes"] / 1024 / 1024, 2)
        report["vram"]["total_mb"] = round(sampler_result["total_bytes"] / 1024 / 1024, 2)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark VRAM cho /tasks/generate-texture")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--user-id", type=int, default=1)
    parser.add_argument("--clothing-item-id", type=int, default=1)
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--poll-interval", type=float, default=0.5)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--device-index", type=int, default=0)
    parser.add_argument("--sample-interval", type=float, default=0.25)
    args = parser.parse_args()

    report = run_benchmark(
        base_url=args.base_url.rstrip("/"),
        user_id=args.user_id,
        clothing_item_id=args.clothing_item_id,
        rounds=max(1, args.rounds),
        poll_interval=max(0.1, args.poll_interval),
        timeout_s=max(1.0, args.timeout),
        device_index=max(0, args.device_index),
        sample_interval=max(0.05, args.sample_interval),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()