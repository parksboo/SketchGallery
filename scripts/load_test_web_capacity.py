#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any


def _http_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 10.0,
) -> tuple[int, dict[str, Any]]:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url=url, method=method, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {"error": raw or str(exc)}
        return exc.code, parsed


def _pct(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    idx = int(round((len(values) - 1) * q))
    return sorted(values)[idx]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capacity/load test for SketchGallery webserver create-job path."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:5050")
    parser.add_argument("--sketch-key", required=True)
    parser.add_argument("--mode", default="test")
    parser.add_argument("--title", default="Load Test")
    parser.add_argument("--prompt", default="Load test request")
    parser.add_argument("--style", default="Cinematic")
    parser.add_argument("--total", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--submit-timeout-sec", type=float, default=10.0)
    parser.add_argument("--poll-interval-sec", type=float, default=1.0)
    parser.add_argument("--job-timeout-sec", type=float, default=300.0)
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    create_url = f"{base}/api/v1/jobs"

    def submit_one(i: int) -> dict[str, Any]:
        payload = {
            "sketch_key": args.sketch_key,
            "title": f"{args.title} #{i}",
            "prompt": args.prompt,
            "style": args.style,
            "mode": args.mode,
            "sketch_name": "loadtest.png",
        }
        started = time.perf_counter()
        code, data = _http_json(
            "POST", create_url, payload=payload, timeout=args.submit_timeout_sec
        )
        latency = time.perf_counter() - started
        return {
            "index": i,
            "http_code": code,
            "latency_sec": latency,
            "job_id": str(data.get("job_id", "")).strip(),
            "status": str(data.get("status", "")).strip(),
            "error": data.get("error"),
        }

    started_all = time.perf_counter()
    submit_results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as ex:
        futures = [ex.submit(submit_one, i) for i in range(args.total)]
        for fut in as_completed(futures):
            submit_results.append(fut.result())

    accepted = [
        r for r in submit_results if r["http_code"] == 202 and r["job_id"] and r["status"]
    ]
    submit_latencies = [r["latency_sec"] for r in submit_results]
    accepted_latencies = [r["latency_sec"] for r in accepted]

    print("=== Submit Summary ===")
    print(f"total={args.total} concurrency={args.concurrency}")
    print(f"accepted={len(accepted)} rejected={args.total - len(accepted)}")
    print(
        "submit_latency_sec: "
        f"avg={statistics.mean(submit_latencies):.3f} "
        f"p50={_pct(submit_latencies, 0.50):.3f} "
        f"p95={_pct(submit_latencies, 0.95):.3f}"
    )
    if accepted_latencies:
        print(
            "accepted_submit_latency_sec: "
            f"avg={statistics.mean(accepted_latencies):.3f} "
            f"p50={_pct(accepted_latencies, 0.50):.3f} "
            f"p95={_pct(accepted_latencies, 0.95):.3f}"
        )

    job_started_at = {r["job_id"]: time.perf_counter() for r in accepted}
    final_status: dict[str, str] = {}
    completion_latency_sec: dict[str, float] = {}
    timed_out_jobs: set[str] = set()

    while len(final_status) + len(timed_out_jobs) < len(job_started_at):
        for job_id in job_started_at:
            if job_id in final_status or job_id in timed_out_jobs:
                continue
            elapsed = time.perf_counter() - job_started_at[job_id]
            if elapsed > args.job_timeout_sec:
                timed_out_jobs.add(job_id)
                continue

            code, data = _http_json("GET", f"{base}/api/v1/jobs/{job_id}", timeout=10.0)
            if code != 200:
                continue
            status = str(data.get("status", "")).strip().lower()
            if status in {"completed", "failed"}:
                final_status[job_id] = status
                completion_latency_sec[job_id] = elapsed

        if len(final_status) + len(timed_out_jobs) >= len(job_started_at):
            break
        time.sleep(max(0.1, args.poll_interval_sec))

    completed = [j for j, s in final_status.items() if s == "completed"]
    failed = [j for j, s in final_status.items() if s == "failed"]
    completion_values = [completion_latency_sec[j] for j in completed]
    wallclock = time.perf_counter() - started_all
    throughput = len(completed) / wallclock if wallclock > 0 else 0.0

    print("=== Completion Summary ===")
    print(
        f"completed={len(completed)} failed={len(failed)} timed_out={len(timed_out_jobs)}"
    )
    if completion_values:
        print(
            "completed_latency_sec: "
            f"avg={statistics.mean(completion_values):.3f} "
            f"p50={_pct(completion_values, 0.50):.3f} "
            f"p95={_pct(completion_values, 0.95):.3f}"
        )
    print(f"wallclock_sec={wallclock:.3f}")
    print(f"throughput_completed_jobs_per_sec={throughput:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

