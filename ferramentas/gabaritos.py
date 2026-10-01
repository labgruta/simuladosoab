"""Lê o gabarito (tipo 1) de um exame a partir do PDF. Só é usado para exames novos;
os gabaritos já lidos ficam em dados/gabaritos.json.

Uso avulso para conferir:  python3 gabaritos.py
"""
import re

import pymupdf

import fontes


def texto_do_pdf(nome):
    return " ".join(p.get_text() for p in pymupdf.open(fontes.caminho(nome)))


def _gabarito_em_tabela(texto, total):
    """Formato mais comum: linhas de números (1 2 3 ...) seguidas das letras. Usa o primeiro bloco (tipo 1)."""
    toks = re.findall(r"\d+|[A-D]\b|\*|[Xx]\b|ANULADA|Anulada|NULA", texto)
    gab, i = {}, 0
    while i < len(toks) and len(gab) < total:
        if toks[i].isdigit() and int(toks[i]) == len(gab) + 1:
            j, nums = i, []
            while j < len(toks) and toks[j].isdigit() and int(toks[j]) == len(gab) + 1 + len(nums):
                nums.append(int(toks[j]))
                j += 1
            letras = []
            while j < len(toks) and not toks[j].isdigit() and len(letras) < len(nums):
                letras.append(toks[j])
                j += 1
            if len(nums) >= 5 and len(letras) == len(nums):
                gab.update(zip(nums, letras))
                i = j
                continue
        i += 1
    return gab


def _gabarito_correspondencia(texto):
    """XII Exame: tabela 'tipo 1, tipo 2, tipo 3, tipo 4, gabarito' por linha."""
    toks = re.findall(r"\d+|[A-D\*]\b", texto)
    gab = {}
    for i in range(len(toks) - 4):
        w = toks[i:i + 5]
        if all(x.isdigit() for x in w[:4]) and not w[4].isdigit() and 1 <= int(w[0]) <= 80 and int(w[0]) not in gab:
            gab[int(w[0])] = w[4]
    return gab


def gabarito_do_pdf(exame):
    """{número da questão: 'A'..'D' ou '*' (anulada)}"""
    texto = texto_do_pdf(fontes.gabaritos()[exame])
    if exame == "2010.2":  # "001 – C; 002 – A; ..."
        return {int(a): b for a, b in re.findall(r"(\d{3})\s*[–-]\s*([A-D\*])", texto)}
    if exame == "12":
        return _gabarito_correspondencia(texto)
    return _gabarito_em_tabela(texto, fontes.total_questoes(exame))


if __name__ == "__main__":
    for exame in sorted(fontes.gabaritos(), key=fontes.ordem_cronologica):
        total = fontes.total_questoes(exame)
        g = gabarito_do_pdf(exame)
        print(f"{exame:7s} {len(g):3d} " + "".join(g.get(i, "?") for i in range(1, total + 1)))
