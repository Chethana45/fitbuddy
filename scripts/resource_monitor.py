"""Run the Locust load test against a demo-mode server and record its CPU and memory use.

Starts uvicorn in demo mode, samples the server process tree every second while Locust runs,
and writes reports/resource_usage.csv plus the usual Locust reports/perf* files.

Run from the project root with the venv active:  python scripts/resource_monitor.py
"""
import csv
import os
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
HOST = "http://127.0.0.1:8000"
PY = sys.executable


def wait_for_server(server: subprocess.Popen) -> None:
    """Poll /api/health until the server answers (about 30 s), or kill it and exit."""
    for _ in range(60):
        try:
            print(urllib.request.urlopen(f"{HOST}/api/health").read().decode())
            return
        except Exception:
            time.sleep(0.5)
    server.kill()
    sys.exit("server did not start")


class Sampler:
    """Samples CPU and RSS of a process and its children once per second in a background thread."""

    def __init__(self, pid: int) -> None:
        self.root = psutil.Process(pid)
        self.ncpu = psutil.cpu_count()
        self.total_mb = psutil.virtual_memory().total / 2**20
        self.samples: list[dict] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run)
        # Reuse Process objects: cpu_percent() is measured since the previous call on the same object.
        self._cache: dict[int, psutil.Process] = {}

    def _procs(self) -> list[psutil.Process]:
        try:
            live = [self.root] + self.root.children(recursive=True)
        except psutil.NoSuchProcess:
            return []
        for p in live:
            self._cache.setdefault(p.pid, p)
        return [self._cache[p.pid] for p in live]

    def _run(self) -> None:
        for p in self._procs():
            p.cpu_percent(None)  # prime the counters
        t0 = time.time()
        while not self._stop.wait(1.0):
            cpu = 0.0
            rss = 0.0
            for p in self._procs():
                try:
                    cpu += p.cpu_percent(None)
                    rss += p.memory_info().rss
                except psutil.NoSuchProcess:
                    pass
            mb = rss / 2**20
            if not self.samples:
                print("tree:", [(p.pid, p.name()) for p in self._procs()])
            self.samples.append({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "elapsed_s": round(time.time() - t0, 1),
                "cpu_percent": round(cpu, 1),  # 100 = one full core
                "cpu_percent_of_system": round(cpu / self.ncpu, 2),
                "rss_mb": round(mb, 1),
                "mem_percent_of_system": round(mb / self.total_mb * 100, 3),
            })

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join()


def main() -> None:
    env = dict(os.environ, DEMO_MODE="true")
    REPORTS.mkdir(exist_ok=True)

    with open(REPORTS / "server-perf.log", "w") as log:
        server = subprocess.Popen(
            [PY, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
        )
        wait_for_server(server)

        sampler = Sampler(server.pid)
        sampler.start()
        cmd = [
            PY, "-m", "locust", "-f", "tests/locustfile.py", "--headless",
            "-u", "50", "-r", "10", "-t", "60s", "--host", HOST,
            "--csv", "reports/perf", "--html", "reports/perf.html",
        ]
        rc = subprocess.run(cmd, cwd=ROOT, env=env).returncode
        sampler.stop()
        server.terminate()
        server.wait(10)

    samples = sampler.samples
    if not samples:
        sys.exit(f"no samples collected (locust rc={rc})")

    with open(REPORTS / "resource_usage.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(samples[0]))
        writer.writeheader()
        writer.writerows(samples)

    print(f"\nlocust rc={rc} samples={len(samples)} cores={sampler.ncpu} "
          f"ram_total_mb={sampler.total_mb:.0f}")
    for key in ("cpu_percent", "cpu_percent_of_system", "rss_mb", "mem_percent_of_system"):
        values = [s[key] for s in samples]
        print(f"{key}: avg={sum(values) / len(values):.2f} peak={max(values):.2f}")


if __name__ == "__main__":
    main()
