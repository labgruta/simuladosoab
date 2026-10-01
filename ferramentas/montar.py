"""Junta questões, matérias, temas e gabaritos e grava os arquivos que o app lê (q-<matéria>.json e meta.json)."""
import collections
import json
import os
import re

import fontes
from temas import atribuir_temas, resumo_de_temas

ILEGIVEIS = re.compile(r"[\x00-\x08\x0b-\x1fϢ-Ͽ]")  # restos de fonte sem mapa de caracteres
FIM_DA_PROVA = re.compile(r"\s*(QUESTIONÁRIO DE PERCEPÇÃO|Questionário de percepção|CRONOGRAMA OPERACIONAL).*$", re.S)
# Rodapés que grudam no fim da última alternativa da coluna (VII, VIII e 2010.2)
RODAPE = re.compile(r"\s*(?:[IVXL]+ EXAME DE ORDEM UNIFICADO\s*[–-]\s*TIPO 0?1\s*[–-]\s*BRANC[AO]"
                    r"|Caderno de Prova 0?1(?:\s*[–-]\s*\d{1,3}\s*[–-])?|[–-]\s*\d{1,3}\s*[–-])\s*$")


def _romano(n):
    s = ""
    for valor, letra in [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]:
        while n >= valor:
            s += letra
            n -= valor
    return s


def nome_do_exame(exame):
    if exame.startswith("2010"):
        return f"Exame {exame}"
    n = int(exame)
    return f"{_romano(n)} Exame" if n <= 37 else f"{n}º Exame"


def limpar(texto, exame):
    texto = (texto.replace("", " ").replace("‐", "-")
             .replace("ﬁ ", "fi").replace("ﬁ", "fi").replace("ﬂ ", "fl").replace("ﬂ", "fl"))
    if exame == "2010.2":  # o "ti" desse caderno vem separado: "Const ituição"
        texto = re.sub(r"(\w)t i(\w)", r"\1ti\2", texto)
        # também "compat ível", "t ipo", "benef ício": o espaço vem da ligadura com i/í
        texto = re.sub(r"\b(\w*[tf]) ([iíìî])(?=\w)", r"\1\2", texto)
        texto = re.sub(r"(\w)t ni (\w)", r"\1tin\2", texto)
    texto = FIM_DA_PROVA.sub("", texto)  # questionário de percepção grudado na última questão
    # palavra composta partida na quebra de linha: "sexta- feira" -> "sexta-feira" (preserva "pré- e pós-")
    texto = re.sub(r"(\w)- (?!(?:e|ou|a|ao) )(?=[a-zà-ú])", r"\1-", texto)
    texto = RODAPE.sub("", texto)
    texto = ILEGIVEIS.sub("", texto)
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r" *\n *", "\n", texto)
    return texto.strip()


def _correcoes_pontuais(exame, n, enunciado, alts):
    alts = dict(alts)
    if exame == "35" and n == 77 and "D" not in alts:
        # a letra D saiu ilegível e grudou na C
        alts["C"], alts["D"] = re.split(r"\s*\x18\)\x03\s*", alts["C"], maxsplit=1)
    if exame == "2010.2" and n == 1:
        # instruções da capa antes da primeira questão
        enunciado = re.sub(r"^.*?\b01 A\d{5}\s*", "", enunciado, flags=re.S)
    return enunciado, alts


def montar(brutas, materias, gabaritos, destino):
    """gabaritos: {exame: {número: 'A'..'D' ou '*'}}"""
    banco = collections.defaultdict(list)
    por_materia = collections.Counter()
    descartes = collections.Counter()
    for exame in sorted(brutas):
        questoes, gab = brutas[exame], gabaritos[exame]
        anuladas = set(fontes.ANULADAS.get(exame, []))
        for q, materia in zip(questoes, materias[exame]):
            n = q["n"]
            enunciado, alts = _correcoes_pontuais(exame, n, q["stem"], q["alts"])
            enunciado = limpar(enunciado, exame)
            alts = {k: limpar(v, exame) for k, v in alts.items()}
            resposta = gab.get(n)
            if n in anuladas or resposta == "*":
                descartes["anulada"] += 1
                continue
            if resposta not in ("A", "B", "C", "D"):
                descartes["sem gabarito"] += 1
                continue
            if sorted(alts) != ["A", "B", "C", "D"] or not enunciado or not all(alts.values()):
                descartes["texto incompleto"] += 1
                continue
            banco[materia].append({
                "id": f"{exame}-{n}", "e": nome_do_exame(exame), "n": n,
                "q": enunciado, "a": [alts[k] for k in "ABCD"], "r": "ABCD".index(resposta),
            })
            por_materia[materia] += 1

    for materia, lista in banco.items():
        atribuir_temas(materia, lista)
    temas = resumo_de_temas(banco)

    os.makedirs(destino, exist_ok=True)
    for materia, lista in banco.items():
        with open(os.path.join(destino, f"q-{materia}.json"), "w") as f:
            json.dump(lista, f, ensure_ascii=False, separators=(",", ":"))
    exames = {q["id"].rsplit("-", 1)[0] for lista in banco.values() for q in lista}
    meta = {"counts": dict(por_materia), "total": sum(por_materia.values()),
            "exams": len(exames), "anuladas": descartes["anulada"], "temas": temas}
    with open(os.path.join(destino, "meta.json"), "w") as f:
        json.dump(meta, f, ensure_ascii=False)
    return meta, dict(descartes)
