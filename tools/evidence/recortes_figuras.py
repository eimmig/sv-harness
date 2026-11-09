#!/usr/bin/env python3
"""Recorta, dos arquivos de uma rodada do 02-carga.sh, os trechos usados nas figuras do TCC.

Uso: recortes_figuras.py <pasta-da-rodada> <pasta-de-saida>
Gera antes.txt (HPA, consumo e filas em repouso), escalonamento.txt (primeira amostra do HPA com
mais de uma replica), fila-max.txt (amostra das filas com a maior fila de eventos),
reconciliacao.txt (reconciliacao e atraso) e resumo.txt (resumo, com as linhas de latencia
quebradas para caber em 90 colunas). O conteudo e copiado sem alteracao, exceto essa quebra.
"""
import re
import sys
from pathlib import Path

run, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)


def read(name):
    return (run / name).read_text(encoding="utf-8", errors="replace")


def blocks(text):
    """Divide um arquivo de amostras em [(cabecalho '## data', linhas)]."""
    res, cur = [], None
    for line in text.splitlines():
        if line.startswith("## "):
            cur = (line, [])
            res.append(cur)
        elif cur is not None:
            cur[1].append(line)
    return res


# repouso: do primeiro cabecalho do HPA ate o fim (sem a listagem larga de pods)
antes = read("02-antes.txt").splitlines()
start = next(i for i, l in enumerate(antes) if l.startswith("NAME") and "REFERENCE" in l)
keep = [l for l in antes[start:] if not l.startswith(("Timeout:", "Listing queues"))]
(out / "antes.txt").write_text("\n".join([antes[0]] + keep) + "\n", encoding="utf-8")

# primeira amostra do HPA com alguma replica > 1
for head, lines in blocks(read("02-hpa.txt")):
    reps = [int(l.split()[-2]) for l in lines if l and not l.startswith("NAME")]
    if any(r > 1 for r in reps):
        (out / "escalonamento.txt").write_text("\n".join([head] + lines) + "\n", encoding="utf-8")
        break

# amostra das filas com a maior fila de eventos
best, best_n = None, -1
for head, lines in blocks(read("02-filas.txt")):
    for l in lines:
        p = l.split("\t")
        if p[0] == "stats.bet-events" and len(p) >= 3:
            n = int(p[1]) + int(p[2])
            if n > best_n:
                best, best_n = (head, lines), n
head, lines = best
lines = [l for l in lines if not l.startswith(("Timeout:", "Listing queues"))]
(out / "fila-max.txt").write_text("\n".join([head] + lines) + "\n", encoding="utf-8")

(out / "reconciliacao.txt").write_text(read("02-reconciliacao.txt").rstrip() + "\n\n"
                                       + read("02-atraso.txt").rstrip() + "\n", encoding="utf-8")

resumo = []
for l in read("02-resumo.txt").splitlines():
    if l.startswith("latencias por requisicao"):
        continue
    m = re.match(r"^(latencia\s+: )?(POST /bets|PATCH /bets/status): (.*)$", l)
    if m:
        resumo.append(f"{m.group(2)}:")
        resumo.append("    " + m.group(3))
    else:
        resumo.append(l)
(out / "resumo.txt").write_text("\n".join(resumo) + "\n", encoding="utf-8")
print("recortes em", out)
