"""Onde estão os dados de origem e o que já se sabe sobre cada exame.

As questões extraídas e os gabaritos de todos os exames já processados ficam versionados
em ferramentas/dados/ (brutas.json e gabaritos.json), então os PDFs antigos não são mais
necessários. PDFs só entram para incluir um exame novo (ou reprocessar um exame).

Para incluir um exame novo: baixe o caderno tipo 1 e o gabarito do site da OAB, salve como
"OAB 48 - Caderno de Prova - Tipo 1.pdf" e "OAB 48 - Gabarito Definitivo.pdf" na pasta dos
PDFs e, se houver questões anuladas, acrescente-as em ANULADAS.
"""
import glob
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(AQUI, "dados")

# Pasta com os PDFs. Pode ser trocada com a variável de ambiente OAB_PDFS.
PASTA_PDFS = os.path.expanduser(os.environ.get("OAB_PDFS", "~/Downloads"))

# Questões anuladas (numeração do caderno tipo 1), tiradas dos comunicados de anulação.
# Anulações que valeram só para reaplicações locais (Ipatinga/IX, Salvador/XX) não entram.
# Os gabaritos definitivos mais novos também marcam anuladas com "*"; essas são descartadas
# automaticamente.
ANULADAS = {
    "2010.2": [13], "2010.3": [94], "04": [34, 64, 79], "05": [27], "06": [35, 51],
    "07": [27, 29, 53, 65], "09": [3, 26, 27], "11": [31], "15": [33, 78], "17": [20, 76],
    "21": [7, 67], "24": [71], "27": [41], "28": [37], "29": [20, 34], "30": [20, 30, 57],
    "32": [3, 45, 55, 61, 74], "33": [59], "34": [63], "35": [50, 59], "36": [50, 51],
    "37": [7, 69], "38": [45, 60, 62], "39": [18, 49, 63], "40": [5, 46], "42": [43],
    "43": [1], "47": [47],
}


def _com_nome_padrao(padrao):
    achados = {}
    for f in glob.glob(os.path.join(PASTA_PDFS, padrao)):
        achados[re.match(r"OAB (\S+) -", os.path.basename(f)).group(1)] = os.path.basename(f)
    return achados


def cadernos():
    """{exame: arquivo do caderno tipo 1} dos PDFs presentes na pasta"""
    return _com_nome_padrao("OAB * - Caderno de Prova - Tipo 1.pdf")


def gabaritos():
    """{exame: arquivo do gabarito da 1ª fase} dos PDFs presentes na pasta"""
    return _com_nome_padrao("OAB * - Gabarito*.pdf")


def caminho(nome):
    return os.path.join(PASTA_PDFS, nome)


def total_questoes(exame):
    return 100 if exame.startswith("2010") else 80


def ordem_cronologica(exame):
    return float(exame) if "." in exame else float(exame) + 2010
