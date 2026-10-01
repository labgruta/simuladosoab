"""Baixa do site da OAB os PDFs usados pelo banco de questões.

    python3 ferramentas/baixar.py [pasta]          # todos os exames
    python3 ferramentas/baixar.py [pasta] 48 47    # só alguns exames

Para cada exame grava, na pasta (padrão: ~/Downloads/Provas OAB):
    Cadernos/OAB NN - Caderno de Prova - Tipo 1.pdf     caderno tipo 1 da aplicação principal
    Gabaritos/OAB NN - Gabarito Definitivo.pdf           (ou "Gabarito Preliminar", se for o único)
    Anulações/OAB NN - Anulação (AAAA-MM-DD).pdf         comunicados que anulam questões da 1ª fase
    Anulações/OAB NN - Sem anulação (AAAA-MM-DD).pdf     comunicados de que não houve anulação
    Anulações/OAB NN - Gabarito retificado (AAAA-MM-DD).pdf  gabarito republicado com correção
Os comunicados com título genérico ("COMUNICADO") são lidos para saber se tratam de anulação.
Requer PyMuPDF (ferramentas/requirements.txt).
"""
import html
import json
import os
import re
import sys
import tempfile
import urllib.request

import pymupdf

SITE = "https://examedeordem.oab.org.br/EditaisProvas?NumeroExame="
UA = {"User-Agent": "Mozilla/5.0 (simuladosoab)"}
FORA_DA_1A_FASE = re.compile(r"Reaplica|Salvador|Porto Alegre|Ipatinga|Direito|2ª fase|Prático|Padrão", re.I)


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def _codigo(nome):
    """'XXV EXAME...' -> '25'; '47º EXAME...' -> '47'; '... 2010.2' -> '2010.2'"""
    m = re.search(r"(2010\.\d)", nome)
    if m:
        return m.group(1)
    m = re.match(r"(\d+)º", nome)
    if m:
        return m.group(1).zfill(2)
    val = {"I": 1, "V": 5, "X": 10, "L": 50}
    r = re.match(r"([IVXL]+)\s", nome.upper()).group(1)
    n = sum(-val[c] if val[c] < val.get(r[i + 1:i + 2], 0) else val[c] for i, c in enumerate(r))
    return str(n).zfill(2)


def exames():
    s = _get(SITE + "0").decode("utf-8", "ignore")
    return [(v, " ".join(html.unescape(t).split())) for v, t in re.findall(r'<option value="(\d+)"[^>]*>([^<]+)</option>', s) if v != "0"]


def links(id_exame):
    s = _get(SITE + id_exame).decode("utf-8", "ignore")
    saida = []
    for href, txt in re.findall(r'<a[^>]+href="([^"]+\.pdf)"[^>]*>(.*?)</a>', s, re.S | re.I):
        t = " ".join(html.unescape(re.sub("<[^>]+>", "", txt)).split())
        m = re.match(r"(\d\d)/(\d\d)/(\d{4})", t)
        data = f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""
        saida.append({"url": href.replace("http://", "https://"), "titulo": t, "data": data})
    return saida


def _caderno(ls):
    for l in ls:
        t = l["titulo"]
        if re.search(r"caderno", t, re.I) and re.search(r"tipo\s*0?1\b|prova\s*0?1\s*$", t, re.I) and not FORA_DA_1A_FASE.search(t) \
                and not re.search(r"comunicado|anula|gabarito", t, re.I):
            return l
    return None


def _gabarito(ls):
    cands = [l for l in ls if re.search(r"gabarito", l["titulo"], re.I) and not FORA_DA_1A_FASE.search(l["titulo"])
             and not re.search(r"comunicado|manuten", l["titulo"], re.I)
             and not re.search(r"caderno de prova 0?[2-4]\b", l["titulo"], re.I)]
    for l in cands:
        if re.search(r"definitiv", l["titulo"], re.I):
            return l, "Definitivo"
    for l in cands:  # preliminar corrigido ("retificado em", "atualizado") antes do original
        if re.search(r"retifica|atualiza|republica", l["titulo"], re.I):
            return l, "Preliminar retificado"
    for l in cands:
        return l, "Preliminar" if re.search(r"prelimin", l["titulo"], re.I) else ""
    return None, ""


def _tipo_comunicado(texto):
    """"Anulação" se anula questões numeradas da prova objetiva; "Sem anulação" se informa que não houve;
    "Gabarito retificado" se o gabarito da prova objetiva foi republicado com correção."""
    t = " ".join(texto.split())
    if re.search(r"republicad\w* o gabarito|gabarito retificado|retifica\w* (d[oe] )?gabarito", t, re.I) and re.search(r"prova objetiva|1ª fase", t, re.I):
        return "Gabarito retificado"
    objetiva = re.search(r"prova objetiva|quest\w* objetivas?|primeira fase|1ª fase|caderno de prova (do )?tipo 0?1|tipo 1", t, re.I)
    pratica = re.search(r"prático-profissional|quesito|espelho|padrão de resposta", t, re.I)
    if not objetiva or (pratica and not re.search(r"prova objetiva", t, re.I)):
        return None
    # "anulação da Questão n. 47", "questão de nº. 13", "questão n.º 94", "questões de número 50 e 59"
    if re.search(r"anula\w*[^.]{0,120}?quest\w*\s+(?:de\s+)?(?:n(?:\.|º|°)?\s*[º°.]?\s*|números?\s+)?\d", t, re.I):
        return "Anulação"
    if re.search(r"(não houve|não foram realizadas|não existem novas) anula", t, re.I):
        return "Sem anulação"
    return None


def baixar(pasta, so=None):
    for sub in ("Cadernos", "Gabaritos", "Anulações"):
        os.makedirs(os.path.join(pasta, sub), exist_ok=True)
    arq_resumo = os.path.join(pasta, "resumo.json")
    resumo = json.load(open(arq_resumo)) if os.path.exists(arq_resumo) else {}
    tmp = tempfile.mkdtemp(prefix="oab_comunicados_")
    for id_exame, nome in exames():
        cod = _codigo(nome)
        if so and cod not in so:
            continue
        ls = links(id_exame)
        r = resumo[cod] = {"caderno": None, "gabarito": None, "anulacao": [], "sem_anulacao": []}
        cad = _caderno(ls)
        if cad:
            open(os.path.join(pasta, "Cadernos", f"OAB {cod} - Caderno de Prova - Tipo 1.pdf"), "wb").write(_get(cad["url"]))
            r["caderno"] = cad["titulo"]
        gab, tipo = _gabarito(ls)
        if gab:
            nomearq = f"OAB {cod} - Gabarito {tipo}".strip() + ".pdf"
            open(os.path.join(pasta, "Gabaritos", nomearq), "wb").write(_get(gab["url"]))
            r["gabarito"] = gab["titulo"]
        for l in ls:
            if not re.search(r"comunicado|anula|nota|aviso", l["titulo"], re.I) or FORA_DA_1A_FASE.search(l["titulo"]) and not re.search(r"anula", l["titulo"], re.I):
                continue
            try:
                dados = _get(l["url"])
                texto = " ".join(p.get_text() for p in pymupdf.open(stream=dados, filetype="pdf"))
            except Exception:
                continue
            tipo = _tipo_comunicado(texto)
            if not tipo:
                continue
            extra = " (reaplicação)" if re.search(r"Reaplica|Salvador|Ipatinga|Porto Alegre", l["titulo"] + texto[:400], re.I) else ""
            arq = f"OAB {cod} - {tipo} ({l['data']}){extra}.pdf"
            k = 2
            while arq in r["anulacao"] + r["sem_anulacao"] + r.get("retificacao", []):  # dois comunicados no mesmo dia
                arq = f"OAB {cod} - {tipo} ({l['data']}) ({k}){extra}.pdf"
                k += 1
            open(os.path.join(pasta, "Anulações", arq), "wb").write(dados)
            r.setdefault({"Anulação": "anulacao", "Sem anulação": "sem_anulacao"}.get(tipo, "retificacao"), []).append(arq)
        print(f"  {cod:7s} caderno: {'ok' if r['caderno'] else '—'}  gabarito: {'ok' if r['gabarito'] else '—'}  "
              f"anulação: {len(r['anulacao'])}  sem anulação: {len(r['sem_anulacao'])}  gabarito retificado: {len(r.get('retificacao', []))}", flush=True)
    with open(arq_resumo, "w") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=1)
    return resumo


if __name__ == "__main__":
    args = sys.argv[1:]
    pasta = os.path.expanduser(args.pop(0)) if args and not re.fullmatch(r"[\d.]+", args[0]) else os.path.expanduser("~/Downloads/Provas OAB")
    baixar(pasta, set(a.zfill(2) if "." not in a else a for a in args) or None)
