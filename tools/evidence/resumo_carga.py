#!/usr/bin/env python3
import re
import sys
from datetime import datetime
from pathlib import Path

out = Path(sys.argv[1])


def read_blocks(path):
    blocks = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## "):
            blocks.append((datetime.fromisoformat(line[3:].strip()), []))
        elif blocks and line.strip():
            blocks[-1][1].append(line)
    return blocks


def parse_cpu(value):
    return int(value[:-1]) if value.endswith("m") else int(float(value) * 1000)


result = []

hpa_file = out / "02-hpa.txt"
if hpa_file.exists():
    blocks = read_blocks(hpa_file)
    start = blocks[0][0] if blocks else None
    series = {}
    for stamp, lines in blocks:
        for line in lines:
            match = re.match(r"^(\S+)\s+\S+\s+(?:cpu:\s+)?(\S+?)/\d+%\s+\d+\s+\d+\s+(\d+)\s", line)
            if not match or match.group(1) == "NAME":
                continue
            current = re.match(r"(\d+)%", match.group(2))
            cpu = int(current.group(1)) if current else None
            series.setdefault(match.group(1), []).append((stamp, cpu, int(match.group(3))))
    result.append("## HPA (amostras a cada 10 s)")
    result.append(f"{'servico':<16}{'replicas max':>14}{'CPU pico (% do request)':>26}{'1o escalonamento':>20}")
    for name, rows in sorted(series.items()):
        cpus = [c for _, c, _ in rows if c is not None]
        first_up = next((s for s, _, r in rows if r > rows[0][2]), None)
        delay = f"+{int((first_up - start).total_seconds())} s" if first_up else "nao escalou"
        peak = f"{max(cpus)}%" if cpus else "n/d"
        result.append(f"{name:<16}{max(r for _, _, r in rows):>14}{peak:>26}{delay:>20}")

top_file = out / "02-top.txt"
if top_file.exists():
    peaks = {}
    for _, lines in read_blocks(top_file):
        for line in lines:
            parts = line.split()
            if len(parts) != 3 or parts[0] == "NAME" or not parts[1][0].isdigit():
                continue
            service = re.sub(r"-[a-z0-9]{8,10}-[a-z0-9]{5}$", "", parts[0])
            cpu = parse_cpu(parts[1])
            memory = int(re.sub(r"\D", "", parts[2]) or 0)
            best = peaks.get(service, (0, 0))
            peaks[service] = (max(best[0], cpu), max(best[1], memory))
    result.append("")
    result.append("## Pico por pod (kubectl top, maior valor observado)")
    result.append(f"{'servico':<22}{'CPU (millicores)':>18}{'memoria (Mi)':>16}")
    for service, (cpu, memory) in sorted(peaks.items()):
        result.append(f"{service:<22}{cpu:>18}{memory:>16}")

load_file = out / "02-carga.txt"
if load_file.exists():
    lines = load_file.read_text(encoding="utf-8", errors="replace").splitlines()
    result.append("")
    result.append("## Carga (saida do load_test_bets.py)")
    result.extend(line.strip() for line in lines if any(k in line for k in ("apostas criadas", "tempo total", "won=")))

print("\n".join(result))
