"""Revisa o banco publicado (q-*.json) contra os PDFs oficiais baixados com baixar.py.

    python3 ferramentas/revisar.py [relatorio.md]

Confere: (1) a resposta de cada questão contra o gabarito oficial; (2) as questões fora do banco
contra as anulações oficiais (comunicados + "*" nos gabaritos); (3) a extração atual dos cadernos
contra dados/brutas.json; (4) o texto de cada questão contra uma leitura independente do PDF
(colunas recortadas direto no PyMuPDF); (5) alternativas iguais ou quase iguais na mesma questão.
"""
import difflib
import glob
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import pymupdf  # noqa: E402

import fontes  # noqa: E402
from extrair import extrair_caderno  # noqa: E402
from gabaritos import gabarito_do_pdf  # noqa: E402

RAIZ = os.path.dirname(AQUI)
# sensível a maiúsculas: "Exame de Ordem Unificado" aparece em enunciados; o cabeçalho é em caixa alta
CABECALHO = re.compile(r"EXAME (DE|DO) ORDEM UNI|Exame de Ordem Uniﬁ ?cado 2010|PROVA APLICADA|P[áa]gina \d|Tipo\s+Branc|TIPO 0?1\s*[–-]|Qualquer semelhan|Caderno de Prova 0?1|^[–-]\s*\d+\s*[–-]$|^\d{1,3}$")
# questões em páginas sem camada de texto (o banco veio de OCR): não há leitura independente possível;
# conferidas uma a uma contra a imagem da página em 2026-10-01
CONFERIDAS_NA_IMAGEM = {"35": {57, 58, 69, 70, 71, 72, 73, 74}}
LIG = str.maketrans({"ﬁ": "fi", "ﬂ": "fl", "“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "—": "-", "‐": "-", "−": "-", "": " "})


def norm(s):
    """Compara só a sequência de caracteres: sem espaços, hífens, aspas tipográficas ou ligaduras."""
    s = s.translate(LIG)
    s = re.sub(r"[\s\-­]", "", s)
    # alguns cadernos (XV, XVI) desenham letras duas vezes na emenda das linhas: colapsa repetições
    # nos dois lados da comparação ("julgameento" e "julgamento" viram o mesmo texto)
    return re.sub(r"(.)\1+", r"\1", s)


def texto_independente(caminho):
    doc = pymupdf.open(caminho)
    partes = []
    for pg in doc:
        w, h = pg.rect.width, pg.rect.height
        for x0, x1 in ((0, w / 2), (w / 2, w)):
            # palavras soltas, reagrupadas em linhas pela altura e ordenadas pela posição: aguenta PDFs
            # que partem cada linha em pedaços (XV, XVI), que o get_text("text") devolve fora de ordem
            linhas = {}
            for p in pg.get_text("words", clip=pymupdf.Rect(x0, h * 0.04, x1, h * 0.96)):
                chave = next((k for k in linhas if abs(k - p[3]) <= 2.5), round(p[3], 1))
                linhas.setdefault(chave, []).append(p)
            for _, ws in sorted(linhas.items()):
                l = " ".join(p[4] for p in sorted(ws, key=lambda p: p[0])).strip()
                if l and not CABECALHO.search(l):
                    partes.append(l)
    return norm(" ".join(partes))


def numeros_anulados(texto):
    t = " ".join(texto.split())
    nums = set()
    for m in re.finditer(r"anula\w*[^.]{0,120}?quest\w*\s+(?:de\s+)?(?:n(?:\.|º|°)?\s*[º°.]?\s*|números?\s+)?((?:\d{1,3}(?:\s*,\s*|\s+e\s+)?)+)", t, re.I):
        nums |= {int(x) for x in re.findall(r"\d{1,3}", m.group(1))}
    return nums


def main():
    saida = sys.argv[1] if len(sys.argv) > 1 else os.path.join(fontes.PASTA_PDFS, "revisao.md")
    publicadas = {}
    for f in glob.glob(os.path.join(RAIZ, "q-*.json")):
        for q in json.load(open(f)):
            ex, n = q["id"].rsplit("-", 1)
            publicadas[(ex, int(n))] = q
    brutas = json.load(open(os.path.join(fontes.DADOS, "brutas.json")))
    cadernos, gabs = fontes.cadernos(), fontes.gabaritos()
    rel = ["# Revisão do banco de questões contra os PDFs oficiais", ""]
    tot = {"gabarito": 0, "anul": 0, "extracao": 0, "texto": 0, "iguais": 0, "quase": 0}

    # 1 e 2: gabaritos e anulações
    anul_oficial = {}
    for arq in glob.glob(os.path.join(fontes.PASTA_PDFS, "**", "OAB * - Anulação*.pdf"), recursive=True):
        if "reaplicação" in arq:
            continue
        ex = re.match(r"OAB (\S+) -", os.path.basename(arq)).group(1)
        anul_oficial.setdefault(ex, set()).update(numeros_anulados(" ".join(p.get_text() for p in pymupdf.open(arq))))
    rel += ["## 1. Respostas contra o gabarito oficial e 2. anulações", ""]
    for ex in sorted(brutas, key=fontes.ordem_cronologica):
        g = gabarito_do_pdf(ex)
        estrelas = {n for n, l in g.items() if l == "*"}
        oficiais = anul_oficial.get(ex, set()) | estrelas
        fora = {n for n in range(1, fontes.total_questoes(ex) + 1) if (ex, n) not in publicadas}
        for n in sorted(range(1, fontes.total_questoes(ex) + 1)):
            q = publicadas.get((ex, n))
            oficial = g.get(n)
            if q and oficial not in ("A", "B", "C", "D", "*"):
                rel.append(f"- **{ex} q{n}**: gabarito oficial sem resposta legível ({oficial!r})"); tot["gabarito"] += 1
            elif q and oficial != "*" and "ABCD"[q["r"]] != oficial:
                rel.append(f"- **{ex} q{n}**: app responde {'ABCD'[q['r']]}, gabarito oficial {oficial}"); tot["gabarito"] += 1
            if q and n in oficiais:
                rel.append(f"- **{ex} q{n}**: anulada oficialmente, mas está no banco"); tot["anul"] += 1
        for n in sorted(fora - oficiais):
            rel.append(f"- **{ex} q{n}**: fora do banco sem anulação oficial encontrada"); tot["anul"] += 1
        if set(fontes.ANULADAS.get(ex, [])) != anul_oficial.get(ex, set()) and anul_oficial.get(ex):
            rel.append(f"- {ex}: lista ANULADAS {sorted(fontes.ANULADAS.get(ex, []))} x comunicados {sorted(anul_oficial[ex])} (+ '*' no gabarito: {sorted(estrelas)})")
    if not tot["gabarito"] and not tot["anul"]:
        rel.append("Nenhuma divergência.")

    # 3, 4 e 5: texto
    rel += ["", "## 3. Extração atual x dados versionados, 4. texto x leitura independente, 5. alternativas", ""]
    for ex in sorted(brutas, key=fontes.ordem_cronologica):
        caminho = fontes.caminho(cadernos[ex])
        try:
            nova = {q["n"]: q for q in extrair_caderno(caminho, palavras=ex in fontes.EXTRAIR_POR_PALAVRAS)}
        except Exception as e:  # ex.: OCR do macOS indisponível (páginas ilegíveis do XXXV)
            rel.append(f"- {ex}: não foi possível reextrair o caderno ({type(e).__name__}); extração não comparada")
            nova = None
        for q in (brutas[ex] if nova is not None else []):
            o = nova.get(q["n"])
            if not o or norm(o["stem"]) != norm(q["stem"]) or {k: norm(v) for k, v in o["alts"].items()} != {k: norm(v) for k, v in q["alts"].items()}:
                rel.append(f"- **{ex} q{q['n']}**: extração de hoje difere de dados/brutas.json"); tot["extracao"] += 1
        indep = texto_independente(caminho)
        for n in range(1, fontes.total_questoes(ex) + 1):
            q = publicadas.get((ex, n))
            if not q:
                continue
            if n in CONFERIDAS_NA_IMAGEM.get(ex, ()):
                rel.append(f"- {ex} q{n}: página sem texto no PDF; conferida pela imagem"); continue
            for rotulo, txt in [("enunciado", q["q"])] + [(f"alternativa {'ABCD'[i]}", a) for i, a in enumerate(q["a"])]:
                partes = [p for p in txt.split("\n") if p.strip()]
                for p in partes:
                    if norm(p) not in indep:
                        alvo = norm(p)
                        sm = difflib.SequenceMatcher(None, alvo, indep, autojunk=False)
                        m = sm.find_longest_match(0, len(alvo), 0, len(indep))
                        trecho = indep[max(0, m.b - m.a):max(0, m.b - m.a) + len(alvo)]
                        razao = difflib.SequenceMatcher(None, alvo, trecho).ratio()
                        rel.append(f"- **{ex} q{n}** {rotulo}: não confere com o PDF (semelhança {razao:.0%}). App: `{p[:110]}`")
                        tot["texto"] += 1
                        break
            alts = [norm(a).lower() for a in q["a"]]
            for i in range(4):
                for j in range(i + 1, 4):
                    if alts[i] == alts[j]:
                        rel.append(f"- **{ex} q{n}**: alternativas {'ABCD'[i]} e {'ABCD'[j]} idênticas"); tot["iguais"] += 1
                    else:
                        a, b = q["a"][i].split(), q["a"][j].split()
                        dif = sum(1 for op in difflib.SequenceMatcher(None, a, b).get_opcodes() if op[0] != "equal")
                        if dif == 1 and len(a) > 8:
                            tot["quase"] += 1
        print(f"  {ex} revisado", flush=True)
    rel += ["", "## Resumo", "",
            f"- respostas divergentes do gabarito oficial: {tot['gabarito']}",
            f"- divergências de anulação: {tot['anul']}",
            f"- questões cuja extração mudou: {tot['extracao']}",
            f"- trechos que não conferem com a leitura independente do PDF: {tot['texto']}",
            f"- pares de alternativas idênticas: {tot['iguais']}",
            f"- pares que diferem num único trecho (pegadinhas como 'com'/'sem'; informativo): {tot['quase']}"]
    open(saida, "w").write("\n".join(rel) + "\n")
    print("\n".join(rel[-7:]))
    print("relatório:", saida)


if __name__ == "__main__":
    main()
