"""Extrai enunciado e alternativas das questões de um caderno de prova (PDF, duas colunas).

Uso avulso para conferir um caderno:  python3 extrair.py "caminho/do/caderno.pdf"
"""
import os
import re
import sys
from collections import defaultdict

import pymupdf

import fontes

# Cabeçalhos e rodapés que se repetem em todas as páginas.
# Estrito de propósito: "Exame de Ordem" sozinho aparece em enunciados de Ética.
CABECALHO = re.compile(r"EXAME (DE|DO) ORDEM UNI|PROVA APLICADA|^P[áa]gina \d+$|Tipo\s+Branc|TIPO 0?1\s*[–-]|Qualquer semelhan", re.I)
# "(A) texto" ou "A) texto"
ALTERNATIVA = re.compile(r"^\(?([A-D])\)\s*(.*)$")
# Rótulo da questão: "12", "Questão 12", "Questão 22*", "06 A00420" (código usado em 2010.2)
ROTULO = re.compile(r"^(?:QUEST[ÃA]O\s*)?(\d{1,3})\s*\*?\.?(?:\s+[A-Z]\d{5})?$", re.I)


def ilegivel(pg):
    """Páginas com fonte sem mapa de caracteres saem como caracteres de controle."""
    t = pg.get_text()
    return len(t) > 200 and sum(1 for c in t if ord(c) < 32 and c not in "\n\t ") > 3


def _linhas_ocr(pg, meio, altura):
    from ocr import ocr_pagina  # só no macOS, e só quando necessário
    linhas = defaultdict(list)
    for x0, y0, x1, t in ocr_pagina(pg):
        if CABECALHO.search(t) and (y0 < altura * 0.1 or y0 > altura * 0.9):
            continue
        if re.fullmatch(r"\d{1,3}", t.strip()) and y0 > altura * 0.9:
            continue
        col = 0 if x0 < meio - 5 else 1
        chave = next((k for k in linhas if k[0] == col and abs(k[1] - y0) <= 3.5), (col, round(y0)))
        linhas[chave].append((x0, t))
    return sorted((c, y, min(x for x, _ in v), " ".join(t for _, t in sorted(v))) for (c, y), v in linhas.items())


def linhas_da_pagina(pg, pno):
    """Linhas (coluna, y, x, texto) na ordem de leitura: coluna esquerda e depois a direita."""
    largura, altura = pg.rect.width, pg.rect.height
    meio = largura / 2
    if pno > 0 and ilegivel(pg):
        return _linhas_ocr(pg, meio, altura)
    linhas = defaultdict(list)
    for b in pg.get_text("rawdict")["blocks"]:
        for l in b.get("lines", []):
            chars = [c for s in l["spans"] for c in s["chars"]]
            if not chars:
                continue
            x0, y0, x1, y1 = l["bbox"]
            bruto = "".join(c["c"] for c in chars).strip()
            if CABECALHO.search(bruto) and (y0 < altura * 0.1 or y0 > altura * 0.9):
                continue
            # número de página centralizado no rodapé
            if re.fullmatch(r"\d{1,3}", bruto) and y0 > altura * 0.9 and abs((x0 + x1) / 2 - meio) < 30:
                continue
            col = 0 if x0 < meio - 5 else 1
            base = round(chars[0]["origin"][1])
            # junta pedaços da mesma linha visual (alguns PDFs quebram cada linha em dois)
            chave = next((k for k in linhas if k[0] == col and abs(k[1] - base) <= 2.5), (col, base))
            linhas[chave] += chars
    saida = []
    for (col, base), chars in linhas.items():
        chars.sort(key=lambda c: c["bbox"][0])
        txt, ultimo = [], None
        for c in chars:
            # caractere desenhado duas vezes na emenda dos pedaços
            if ultimo and c["c"] == ultimo["c"] and abs(c["bbox"][0] - ultimo["bbox"][0]) < 2.0:
                continue
            if ultimo and c["bbox"][0] - ultimo["bbox"][2] > 2.5 and c["c"] != " " and ultimo["c"] != " ":
                txt.append(" ")
            txt.append(c["c"])
            ultimo = c
        t = re.sub(r"\s+", " ", "".join(txt)).strip()
        if t:
            saida.append((col, base, min(c["bbox"][0] for c in chars), t))
    return sorted(saida)


def linhas_do_pdf(caminho):
    doc = pymupdf.open(caminho)
    return [(pno,) + l for pno, pg in enumerate(doc) for l in linhas_da_pagina(pg, pno)]


def _juntar(linhas):
    """[(texto, novo_paragrafo)] -> texto com quebras de parágrafo."""
    out = ""
    for t, paragrafo in linhas:
        if not out:
            out = t
        elif paragrafo:
            out += "\n" + t
        elif out.endswith("-") and t[:1].islower():
            out += t
        else:
            out += " " + t
    return out.strip()


def extrair_caderno(caminho):
    """Lista de questões {n, stem, alts{A..D}, star} na ordem do caderno."""
    questoes, atual, esperado, anterior = {}, None, 1, None
    for pno, col, y, x, t in linhas_do_pdf(caminho):
        m = ROTULO.match(t)
        if m and int(m.group(1)) == esperado:
            atual = {"n": esperado, "stem": [], "alts": {}, "last": None, "star": "*" in t}
            questoes[esperado] = atual
            esperado += 1
            anterior = None
            continue
        if atual is None:
            continue
        paragrafo = anterior is not None and anterior[0] == (pno, col) and (y - anterior[1]) > 17
        anterior = ((pno, col), y)
        a = ALTERNATIVA.match(t)
        ult = atual["last"]
        if a and ((ult is None and a.group(1) == "A") or (ult and ord(a.group(1)) == ord(ult) + 1)):
            atual["last"] = a.group(1)
            atual["alts"][a.group(1)] = [(a.group(2), False)]
            continue
        if ult:
            atual["alts"][ult].append((t, False))
        else:
            atual["stem"].append((t, paragrafo))
    return [
        {"n": n, "stem": _juntar(q["stem"]), "alts": {k: _juntar(v) for k, v in q["alts"].items()}, "star": q["star"]}
        for n, q in sorted(questoes.items())
    ]


def extrair_todos():
    """{exame: [questões]} para todos os cadernos encontrados."""
    brutas = {}
    for exame, arquivo in sorted(fontes.cadernos().items()):
        qs = extrair_caderno(fontes.caminho(arquivo))
        problemas = [q["n"] for q in qs if len(q["alts"]) != 4 or not q["stem"]]
        aviso = f"  problemas: {problemas}" if problemas else ""
        print(f"  {exame:7s} {len(qs)} questões{aviso}")
        brutas[exame] = qs
    return brutas


if __name__ == "__main__":
    for f in sys.argv[1:]:
        qs = extrair_caderno(f)
        ruins = [q["n"] for q in qs if len(q["alts"]) != 4 or not q["stem"]]
        print(os.path.basename(f), len(qs), "questões; problemas:", ruins)
