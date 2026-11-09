#!/usr/bin/env python3
"""Gera uma figura de terminal legivel a partir de um arquivo de evidencia (devolutiva do TCC 2,
2026-11-08: o texto das capturas de terminal estava pequeno). O conteudo e a saida real do
comando, gravada pelos scripts deste diretorio; so a apresentacao muda: fonte monoespacada
grande e no maximo --cols colunas, para que a figura ocupe a largura da pagina com o texto em
tamanho de leitura (90 colunas em 16 cm dao cerca de 8,5 pt).

Uso: render_terminal.py <saida.png> <arquivo> [<arquivo> ...] [--title "comando"] [--cols 90]
     [--grep REGEX] [--max-lines N]
Cada arquivo vira um bloco; --title aparece como a linha do comando ($ ...).
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (30, 30, 30)
FG = (230, 230, 230)
PROMPT = (120, 200, 120)
FONT_CANDIDATES = ["C:/Windows/Fonts/consola.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("output")
    p.add_argument("files", nargs="+")
    p.add_argument("--title", action="append", default=[])
    p.add_argument("--cols", type=int, default=90)
    p.add_argument("--grep")
    p.add_argument("--max-lines", type=int, default=60)
    p.add_argument("--size", type=int, default=28)
    a = p.parse_args()

    lines: list[tuple[str, tuple[int, int, int]]] = []
    for i, name in enumerate(a.files):
        if i < len(a.title):
            lines.append(("$ " + a.title[i], PROMPT))
        text = Path(name).read_text(encoding="utf-8", errors="replace").splitlines()
        if a.grep:
            text = [t for t in text if re.search(a.grep, t)]
        for t in text[: a.max_lines]:
            t = t.replace("\t", "    ").rstrip()
            lines.append((t if len(t) <= a.cols else t[: a.cols - 1] + "…", FG))
        if i < len(a.files) - 1:
            lines.append(("", FG))

    font = load_font(a.size)
    char_w = font.getbbox("M")[2]
    line_h = int(a.size * 1.35)
    pad = a.size
    # largura fixa em --cols colunas: todas as figuras ficam com a mesma escala na pagina
    width = pad * 2 + char_w * a.cols
    height = pad * 2 + line_h * len(lines)
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    for n, (t, color) in enumerate(lines):
        draw.text((pad, pad + n * line_h), t, font=font, fill=color)
    img.save(a.output)
    print(f"{a.output}: {width}x{height}, {len(lines)} linhas")


if __name__ == "__main__":
    main()
