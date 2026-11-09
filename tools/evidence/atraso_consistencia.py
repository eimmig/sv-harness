#!/usr/bin/env python3
"""Atraso de consistencia de uma rodada do 02-carga.sh: tempo entre a resposta da
API ao registro (ou liquidacao) de uma aposta e o processamento do evento
correspondente no stats-service, momento em que o consumidor invalida o cache e a
estatistica passa a refletir a aposta.

O bets-service apaga a linha do outbox depois de publicar, entao nao ha um
instante de producao por evento no banco. O script usa, em vez disso, as duas
curvas acumuladas:
  - produzidos: fim de cada POST /bets e PATCH /bets/status com resposta 2xx,
    tirado de 02-latencias.csv (relogio de quem rodou o gerador);
  - consumidos: processed_event.processed_at do tenant da carga, tirado de
    02-processados.txt (relogio do servidor).
A fila e consumida em ordem de chegada, entao o n-esimo evento consumido e
comparado com o n-esimo produzido. Com varios consumidores a ordem nao e
estrita, e o resultado e uma aproximacao por evento; os agregados (mediana,
p95, maximo) sao robustos a essa troca local de ordem.

O deslocamento entre os dois relogios vem de 02-relogio.txt (servidor - local,
em segundos) e e somado aos instantes do gerador. Com o gerador no proprio
servidor, o deslocamento e zero.

Uso: atraso_consistencia.py <pasta-da-rodada>
"""
from __future__ import annotations

import math
import re
import sys
from datetime import datetime
from pathlib import Path


def pct(values: list[float], p: float) -> float:
    k = max(0, min(len(values) - 1, math.ceil(p / 100.0 * len(values)) - 1))
    return values[k]


def main() -> None:
    out = Path(sys.argv[1])
    carga = (out / "02-carga.txt").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"inicio da carga \(UTC\): (\S+)", carga)
    if not m:
        sys.exit("02-carga.txt sem a linha 'inicio da carga (UTC)'")
    t0 = datetime.fromisoformat(m.group(1)).timestamp()
    m_fim = re.search(r"fim da carga \(UTC\): (\S+)", carga)
    t_fim = datetime.fromisoformat(m_fim.group(1)).timestamp() if m_fim else None

    offset = 0.0
    relogio = out / "02-relogio.txt"
    if relogio.exists():
        offsets = [float(v) for v in re.findall(r"offset_s=(-?[\d.]+)", relogio.read_text(encoding="utf-8"))]
        if offsets:
            offset = sum(offsets) / len(offsets)

    produced: list[float] = []
    for line in (out / "02-latencias.csv").read_text(encoding="utf-8").splitlines()[1:]:
        start_s, _op, status, ms = line.split(",")
        if 200 <= int(status) < 300:
            produced.append(t0 + float(start_s) + float(ms) / 1000.0 + offset)
    produced.sort()

    consumed = sorted(float(v) for v in (out / "02-processados.txt").read_text(encoding="utf-8").split() if v)

    n = min(len(produced), len(consumed))
    if n == 0:
        sys.exit("sem eventos para comparar")
    lags = sorted(consumed[i] - produced[i] for i in range(n))

    print(f"eventos produzidos (respostas 2xx)  : {len(produced)}")
    print(f"eventos consumidos (processed_event): {len(consumed)}")
    print(f"deslocamento de relogio aplicado    : {offset:+.3f} s")
    print(f"atraso por evento: mediana={pct(lags, 50):.1f}s p95={pct(lags, 95):.1f}s "
          f"max={lags[-1]:.1f}s min={lags[0]:.1f}s")
    if t_fim is not None:
        drain = consumed[-1] - (t_fim + offset)
        print(f"ultimo evento processado {drain:.1f} s apos o fim do registro")


if __name__ == "__main__":
    main()
