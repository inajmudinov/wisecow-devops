#!/usr/bin/env python3
"""Check Linux system health; exit 1 for alerts, 2 for errors."""
import argparse
import datetime
import logging
import shutil
import time
from pathlib import Path


def percent(value):
    value = float(value)
    if not 0 <= value <= 100:
        raise argparse.ArgumentTypeError("Must be between 0 and 100")
    return value


def cpu_sample():
    fields = Path("/proc/stat").read_text().splitlines()[0].split()
    # Exclude guest counters, which are already included in user/nice.
    values = list(map(int, fields[1:9]))
    return sum(values), values[3] + values[4]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu", type=percent, default=80)
    parser.add_argument("--memory", type=percent, default=80)
    parser.add_argument("--disk", type=percent, default=85)
    parser.add_argument("--max-processes", type=int, default=500)
    parser.add_argument("--path", default="/")
    parser.add_argument("--log", help="Also append results to this file")
    args = parser.parse_args()
    if args.max_processes < 1:
        parser.error("--max-processes must be positive")

    logger = logging.getLogger("health")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    try:
        if args.log:
            handler = logging.FileHandler(args.log)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        total1, idle1 = cpu_sample()
        time.sleep(1)
        total2, idle2 = cpu_sample()
        delta = total2 - total1
        if delta <= 0:
            raise RuntimeError("CPU counters did not advance")
        cpu = 100 * (1 - (idle2 - idle1) / delta)

        memory = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, value = line.split(":", 1)
            memory[key] = int(value.split()[0])
        mem_used = 100 * (
            1 - memory["MemAvailable"] / memory["MemTotal"]
        )

        disk = shutil.disk_usage(args.path)
        disk_used = 100 * disk.used / disk.total

        processes = 0
        running = 0
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit():
                continue
            try:
                status = (entry / "status").read_text()
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                continue
            processes += 1
            if any(line.startswith("State:\tR")
                   for line in status.splitlines()):
                running += 1

        logger.info(
            "CPU=%.1f%% Memory=%.1f%% Disk=%.1f%% "
            "Processes=%d Running=%d Path=%s",
            cpu, mem_used, disk_used, processes, running, args.path
        )

        alerts = []
        for name, actual, threshold in [
            ("CPU", cpu, args.cpu),
            ("Memory", mem_used, args.memory),
            ("Disk", disk_used, args.disk),
        ]:
            if actual > threshold:
                alerts.append(
                    f"{name} {actual:.1f}% exceeds {threshold:.1f}%"
                )
        if processes > args.max_processes:
            alerts.append(
                f"Process count {processes} exceeds {args.max_processes}"
            )

        for alert in alerts:
            logger.warning("ALERT: %s", alert)
        if not alerts:
            logger.info("OK: All metrics are within thresholds")
        return 1 if alerts else 0
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        logger.error("Monitoring failed: %s", error)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
