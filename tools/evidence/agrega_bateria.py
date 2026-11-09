#!/usr/bin/env python3
"""Agrega as rodadas da bateria (bateria.sh) por configuracao: media e desvio padrao amostral.

Uso: agrega_bateria.py <raiz-da-bateria> [config ...]
Le <raiz>/<cfg>-r<n>/02-resumo.txt, 02-atraso.txt e 02-filas.txt de cada rodada.
"""
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
CONFIGS = sys.argv[2:] or ["c1", "c2", "c3"]


def num(pattern, text, cast=float):
    m = re.search(pattern, text)
    return cast(m.group(1)) if m else None


def max_queue(path):
    best = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split("\t")
        if len(parts) >= 3 and parts[0] == "stats.bet-events":
            try:
                best = max(best, int(parts[1]) + int(parts[2]))
            except ValueError:
                pass
    return best


def run_metrics(d):
    resumo = (d / "02-resumo.txt").read_text(encoding="utf-8", errors="replace")
    atraso = (d / "02-atraso.txt").read_text(encoding="utf-8", errors="replace")
    post = re.search(r"POST /bets: .*?mediana=([\d.]+)ms p95=([\d.]+)ms", resumo)
    patch = re.search(r"PATCH /bets/status: .*?mediana=([\d.]+)ms p95=([\d.]+)ms", resumo)
    def pod(name):
        return _pod(resumo, name)
    return {
        "vazao": num(r"\(([\d.]+) apostas/s\)", resumo),
        "erros": num(r"erros=(\d+)", resumo, int),
        "post_med": float(post.group(1)), "post_p95": float(post.group(2)),
        "patch_med": float(patch.group(1)), "patch_p95": float(patch.group(2)),
        "atraso_med": num(r"mediana=([-\d.]+)s", atraso),
        "atraso_p95": num(r"p95=([-\d.]+)s", atraso),
        "ultimo_apos_fim": num(r"ultimo evento processado ([-\d.]+) s", atraso),
        "no_cpu_pct": num(r"CPU pico: \d+ mCPU \((\d+)%\)", resumo, int),
        "pg_bets": pod("postgres-bets"), "pg_stats": pod("postgres-stats"),
        "fila_max": max_queue(d / "02-filas.txt"),
        "reconc_ok": "FAIL" not in (d / "02-reconciliacao.txt").read_text(encoding="utf-8", errors="replace"),
    }


def _pod(resumo, name):
    m = re.search(rf"^{re.escape(name)}\s+(\d+)\s+(\d+)\s*$", resumo, re.M)
    return int(m.group(1)) if m else None


def fmt(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return "-"
    mean = statistics.mean(vals)
    sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
    return f"{mean:.1f} ± {sd:.1f}"


keys = ["vazao", "erros", "post_med", "post_p95", "patch_med", "patch_p95", "atraso_med",
        "atraso_p95", "ultimo_apos_fim", "no_cpu_pct", "pg_bets", "pg_stats", "fila_max"]
table = {}
for cfg in CONFIGS:
    runs = sorted(p for p in ROOT.glob(f"{cfg}-r*") if p.is_dir() and (p / "02-resumo.txt").exists())
    ms = [run_metrics(r) for r in runs]
    table[cfg] = ms
    print(f"## {cfg}: {len(ms)} rodadas ({', '.join(r.name for r in runs)}); reconciliacao ok em todas: "
          f"{all(m['reconc_ok'] for m in ms)}")
    for r, m in zip(runs, ms):
        print("  " + r.name + ": " + ", ".join(f"{k}={m[k]}" for k in keys))

print()
print("medida".ljust(18) + "".join(c.rjust(22) for c in CONFIGS))
for k in keys:
    print(k.ljust(18) + "".join(fmt([m[k] for m in table[c]]).rjust(22) for c in CONFIGS))
