"""Acuracia da extracao de campos do cadastro pelo Telegram.

Mede a funcao `extract_fields` do telegram-integration (a mesma que o servico usa) em:
  1. mensagens de texto simuladas, geradas com semente fixa a partir de formatos variados de
     escrita (valor com e sem "R$", odd com "@", "odd", "cotacao" ou numero solto, casa com
     grafias diferentes, campos em qualquer ordem e mensagens sem algum campo);
  2. as fotos reais de bilhetes disponiveis, lidas com Tesseract (por+eng), como no servico.

Para cada campo (odd, valor apostado, casa), o resultado e classificado em:
  - correto: valor extraido igual ao esperado;
  - ausente: o campo nao foi extraido; o bot pergunta ao usuario (falha segura);
  - errado: valor extraido diferente do esperado; o bot segue sem perguntar (falha silenciosa).
Quando a mensagem nao traz o campo, o esperado e "ausente" e extrair qualquer valor conta como errado.

Uso (no diretorio projeto/):
  services/telegram-integration/.venv/Scripts/python.exe tools/evidence/11-telegram-acuracia.py \
      --bilhetes ../base-prints --saida ../evidencias/20261116-telegram
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "services" / "telegram-integration" / "src"))

from telegram_integration.extraction import extract_fields  # noqa: E402

CAMPOS = ("odd", "stake", "betting_house")

# Casas como o usuario escreveria; o valor canonico e o nome do catalogo do extrator.
CASAS = [
    ("Bet365", ["bet365", "Bet365", "BET365", "bet 365"]),
    ("Betano", ["betano", "Betano", "BETANO"]),
    ("Sportingbet", ["sportingbet", "Sportingbet", "sporting bet"]),
    ("KTO", ["kto", "KTO"]),
    ("Betfair", ["betfair", "Betfair"]),
    ("Pixbet", ["pixbet", "Pixbet"]),
    ("Novibet", ["novibet", "Novibet"]),
    ("Superbet", ["superbet", "Superbet"]),  # casa fora da lista do extrator
]

JOGOS = [
    "Flamengo x Palmeiras", "Corinthians x Santos", "Real Madrid x Barcelona", "Lakers x Celtics",
    "Gremio x Inter", "Sinner x Alcaraz", "Brasil x Argentina", "Liverpool x Chelsea",
]
MERCADOS = ["vitoria do mandante", "ambas marcam", "mais de 2.5 gols", "handicap -1", "empate anula"]


def fmt_decimal(valor: float, virgula: bool) -> str:
    texto = f"{valor:.2f}"
    return texto.replace(".", ",") if virgula else texto


def escreve_valor(valor: float, rng: random.Random) -> str:
    virgula = rng.random() < 0.6
    inteiro = valor.is_integer()
    formas = [
        f"R$ {fmt_decimal(valor, virgula)}",
        f"R${fmt_decimal(valor, virgula)}",
        f"r$ {fmt_decimal(valor, virgula)}",
        f"{int(valor) if inteiro else fmt_decimal(valor, virgula)} reais",
        f"valor {fmt_decimal(valor, virgula)}",
        f"apostei {int(valor) if inteiro else fmt_decimal(valor, virgula)}",
    ]
    return rng.choice(formas)


def escreve_odd(odd: float, rng: random.Random) -> str:
    virgula = rng.random() < 0.5
    texto = fmt_decimal(odd, virgula)
    formas = [f"@{texto}", f"@ {texto}", f"odd {texto}", f"Odd: {texto}", f"cotação {texto}",
              f"cotacao {texto}", f"{texto}", f"na {texto}", f"{texto}x"]
    return rng.choice(formas)


def gera_mensagens(n: int, semente: int) -> list[dict]:
    rng = random.Random(semente)
    mensagens = []
    for i in range(n):
        odd = round(rng.uniform(1.15, 6.0), 2)
        valor = rng.choice([5, 10, 20, 25, 50, 100, 12.5, 32.5, 7.8, 150])
        casa, grafias = rng.choice(CASAS)
        # Em parte das mensagens o usuario omite um campo, como acontece no uso real.
        omite = rng.choices(["nenhum", "odd", "stake", "betting_house"], weights=[6, 1, 1, 2])[0]
        partes = [rng.choice(JOGOS), rng.choice(MERCADOS)]
        esperado = {"odd": None, "stake": None, "betting_house": None}
        if omite != "odd":
            partes.append(escreve_odd(odd, rng))
            esperado["odd"] = f"{odd:.2f}"
        if omite != "stake":
            partes.append(escreve_valor(float(valor), rng))
            esperado["stake"] = f"{float(valor):.2f}"
        if omite != "betting_house":
            partes.append(rng.choice(["na ", "", "casa ", "pela "]) + rng.choice(grafias))
            # Casa fora da lista do extrator: o esperado e que o bot pergunte.
            esperado["betting_house"] = casa if casa != "Superbet" else None
        rng.shuffle(partes)
        separador = rng.choice([", ", " ", " - ", "\n"])
        mensagens.append({"id": f"m{i + 1:02d}", "texto": separador.join(partes), "esperado": esperado,
                          "omitido": omite, "casa_real": casa if omite != "betting_house" else None})
    return mensagens


def normaliza(campo: str, valor: str | None) -> str | None:
    if valor is None:
        return None
    if campo in ("odd", "stake"):
        try:
            return f"{float(valor.replace(',', '.')):.2f}"
        except ValueError:
            return valor
    return valor


def classifica(campo: str, extraido: str | None, esperado: str | None) -> str:
    extraido = normaliza(campo, extraido)
    if extraido is None:
        return "ausente" if esperado is not None else "correto"
    return "correto" if extraido == esperado else "errado"


def avalia(texto: str, esperado: dict) -> dict:
    bet = extract_fields(texto)
    resultado = {}
    for campo in CAMPOS:
        extraido = getattr(bet, campo)
        resultado[campo] = {"extraido": normaliza(campo, extraido), "esperado": esperado[campo],
                            "classe": classifica(campo, extraido, esperado[campo])}
    return resultado


# Gabarito das fotos de base-prints, conferido a olho em cada imagem. A casa nao aparece escrita
# em nenhum dos bilhetes; o esperado e que o bot pergunte (ausente), e nao que adivinhe.
GABARITO_BILHETES = {
    "exemplo_365.png": {"casa": "Bet365", "odd": "3.60", "stake": "5.00"},
    "exemplo_betano.png": {"casa": "Betano", "odd": "8.25", "stake": "5.00"},
    "exemplo_eds.png": {"casa": "Esportes da Sorte", "odd": "5.50", "stake": "2.50"},
    "exemplo_novibet.png": {"casa": "Novibet", "odd": "2.35", "stake": "32.50"},
    "exemplo_vupi.png": {"casa": "Vupi", "odd": "2.70", "stake": "10.00"},
}


def resumo(linhas: list[dict]) -> dict:
    tabela = {}
    for campo in CAMPOS:
        contagem = Counter(l["resultado"][campo]["classe"] for l in linhas)
        tabela[campo] = {k: contagem.get(k, 0) for k in ("correto", "ausente", "errado")}
    completas = sum(all(l["resultado"][c]["classe"] == "correto" for c in CAMPOS) for l in linhas)
    sem_erro = sum(all(l["resultado"][c]["classe"] != "errado" for c in CAMPOS) for l in linhas)
    return {"n": len(linhas), "por_campo": tabela, "mensagens_todas_corretas": completas,
            "mensagens_sem_valor_errado": sem_erro}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=60)
    parser.add_argument("--semente", type=int, default=20261116)
    parser.add_argument("--bilhetes", type=Path)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    args.saida.mkdir(parents=True, exist_ok=True)

    linhas = []
    for m in gera_mensagens(args.n, args.semente):
        m["resultado"] = avalia(m["texto"], m["esperado"])
        linhas.append(m)
    with open(args.saida / "mensagens.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "texto", "omitido"] + [f"{c}_{k}" for c in CAMPOS for k in ("esperado", "extraido", "classe")])
        for l in linhas:
            w.writerow([l["id"], l["texto"].replace("\n", " / "), l["omitido"]]
                       + [l["resultado"][c][k] for c in CAMPOS for k in ("esperado", "extraido", "classe")])

    saida = {"mensagens": resumo(linhas)}

    if args.bilhetes:
        from telegram_integration.ocr import extract_text
        import pytesseract
        saida["tesseract"] = str(pytesseract.get_tesseract_version())
        fotos = []
        for nome, gab in GABARITO_BILHETES.items():
            caminho = args.bilhetes / nome
            texto = extract_text(caminho.read_bytes())
            (args.saida / f"ocr-{caminho.stem}.txt").write_text(texto, encoding="utf-8")
            esperado = {"odd": gab["odd"], "stake": gab["stake"], "betting_house": None}
            fotos.append({"id": nome, "texto": texto, "casa_real": gab["casa"],
                          "resultado": avalia(texto, esperado)})
        saida["bilhetes"] = resumo(fotos)
        saida["bilhetes_detalhe"] = [{"bilhete": f["id"], "casa_real": f["casa_real"],
                                      **{c: f["resultado"][c] for c in CAMPOS}} for f in fotos]

    (args.saida / "resultado.json").write_text(json.dumps(saida, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(saida, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
