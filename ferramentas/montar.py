"""Junta questões, matérias, temas e gabaritos e grava os arquivos que o app lê (q-<matéria>.json e meta.json)."""
import collections
import json
import os
import re

import fontes
from temas import atribuir_temas, resumo_de_temas

ILEGIVEIS = re.compile(r"[\x00-\x08\x0b-\x1fϢ-Ͽ]")  # restos de fonte sem mapa de caracteres
FIM_DA_PROVA = re.compile(r"\s*(QUESTIONÁRIO DE PERCEPÇÃO|Questionário de percepção|CRONOGRAMA OPERACIONAL|CRONOGRAMA\b).*$", re.S)
# Rodapés que grudam no fim da última alternativa da coluna (VII, VIII, 2010.2; "XV E"/"XVI E" no XV e XVI,
# onde o rodapé vem partido em pedaços)
RODAPE = re.compile(r"\s*(?:[IVXL]+ EXAME DE ORDEM UNIFICADO\s*[–-]\s*TIPO 0?1\s*[–-]\s*BRANC[AO]"
                    r"|Caderno de Prova 0?1(?:\s*[–-]\s*\d{1,3}\s*[–-])?|[–-]\s*\d{1,3}\s*[–-]|[IVXL]{2,5} E)\s*$")
# número de página solto depois do ponto final da última alternativa da página (XXXV, XXXVIII)
PAGINA_SOLTA = re.compile(r"([.;:)!?”\"])\s+\d{1,3}$")


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
    if exame == "2010.2":  # lido por palavras; a ligadura "ti" deixa um espaço depois: "Consti tuição", "ti po"
        texto = re.sub(r"ti (?=[a-zà-úç])", "ti", texto)
        texto = re.sub(r"(?<=[tf])í (?=[a-zà-úç])", "í", texto)  # "ofí cio", "tí tulo"
    texto = FIM_DA_PROVA.sub("", texto)  # questionário de percepção grudado na última questão
    # palavra composta partida na quebra de linha: "sexta- feira" -> "sexta-feira" (preserva "pré- e pós-")
    texto = re.sub(r"(\w)- (?!(?:e|ou|a|ao) )(?=[a-zà-ú])", r"\1-", texto)
    texto = RODAPE.sub("", texto)
    texto = ILEGIVEIS.sub("", texto)
    texto = PAGINA_SOLTA.sub(r"\1", texto.rstrip())  # depois do ILEGIVEIS: no XXXV o número vem com lixo ("1ϲ")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r" *\n *", "\n", texto)
    return texto.strip()


def _correcoes_pontuais(exame, n, enunciado, alts):
    alts = dict(alts)
    if exame == "35" and n == 77 and "D" not in alts:
        # a letra D saiu ilegível e grudou na C
        alts["C"], alts["D"] = re.split(r"\s*\x18\)\x03\s*", alts["C"], maxsplit=1)
    # páginas do XXXV sem texto no PDF (lidas por OCR), conferidas com a imagem da página
    if exame == "35" and n == 58 and enunciado.find("qualquer natureza\n") > 0:
        enunciado = enunciado.replace("qualquer natureza\n", "qualquer natureza para tipificação do delito.\n")
    if exame == "35" and n == 74:
        alts["D"] = re.sub(r"\s*L' FGV\s*$", "", alts["D"])  # logotipo do rodapé
    if exame == "2010.2" and n == 1:
        # instruções da capa misturadas à primeira questão
        enunciado = re.sub(r"^.*?\b01 A\d{5}\s*", "", enunciado, flags=re.S)
        i = enunciado.find("O Congresso Nacional")
        if i > 0:
            enunciado = enunciado[i:]
    if exame == "2010.2" and n == 2:
        # quadro de siglas da página seguinte ("... da seguinte forma: CP = Código Penal; ...")
        alts["D"] = re.sub(r"\s*forma: CP = .*$", "", alts["D"], flags=re.S)
    if exame == "2010.2" and n == 46:
        alts = {k: v.replace("variandi i ", "variandi ") for k, v in alts.items()}  # glifo repetido no PDF
    return enunciado, alts


def _notas():
    """dados/notas.json: avisos de mudança na lei por questão. 'desatualizada' sai dos sorteios no app;
    'conferir' só mostra o aviso depois da resposta."""
    caminho = os.path.join(fontes.DADOS, "notas.json")
    if not os.path.exists(caminho):
        return {}
    with open(caminho) as f:
        return {k: v for k, v in json.load(f).items() if not k.startswith("_")}


def montar(brutas, materias, gabaritos, destino):
    """gabaritos: {exame: {número: 'A'..'D' ou '*'}}"""
    banco = collections.defaultdict(list)
    por_materia = collections.Counter()
    descartes = collections.Counter()
    notas = _notas()
    fora_dos_sorteios = 0
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
            q = {"id": f"{exame}-{n}", "e": nome_do_exame(exame), "n": n,
                 "q": enunciado, "a": [alts[k] for k in "ABCD"], "r": "ABCD".index(resposta)}
            nota = notas.pop(q["id"], None)
            if nota:
                q["nota"] = nota
            banco[materia].append(q)
            if not nota or nota["tipo"] != "desatualizada":  # contagem = questões sorteáveis
                por_materia[materia] += 1
            else:
                fora_dos_sorteios += 1
    if notas:
        raise SystemExit(f"Notas para questões que não estão no banco: {sorted(notas)}")

    for materia, lista in banco.items():
        atribuir_temas(materia, lista)
    temas = resumo_de_temas(banco)

    os.makedirs(destino, exist_ok=True)
    for materia, lista in banco.items():
        with open(os.path.join(destino, f"q-{materia}.json"), "w") as f:
            json.dump(lista, f, ensure_ascii=False, separators=(",", ":"))
    exames = {q["id"].rsplit("-", 1)[0] for lista in banco.values() for q in lista}
    meta = {"counts": dict(por_materia), "total": sum(por_materia.values()),
            "exams": len(exames), "anuladas": descartes["anulada"],
            "desatualizadas": fora_dos_sorteios, "temas": temas}
    with open(os.path.join(destino, "meta.json"), "w") as f:
        json.dump(meta, f, ensure_ascii=False)
    return meta, dict(descartes)
