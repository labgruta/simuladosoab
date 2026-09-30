"""Onde estão os PDFs e o que já se sabe sobre cada exame.

Para incluir um exame novo: baixe o caderno tipo 1 e o gabarito do site da OAB,
salve como "OAB 48 - Caderno de Prova - Tipo 1.pdf" e "OAB 48 - Gabarito Definitivo.pdf"
na pasta dos PDFs e, se houver questões anuladas, acrescente-as em ANULADAS.
"""
import glob
import os
import re

# Pasta com os PDFs. Pode ser trocada com a variável de ambiente OAB_PDFS.
PASTA_PDFS = os.path.expanduser(os.environ.get("OAB_PDFS", "~/Downloads"))

# Arquivos baixados com o nome original (UUID) do site da OAB.
CADERNOS_UUID = {
    "43": "145104f9-1301-453d-9079-3d5af4f8e60a.pdf",
    "44": "fda2cc49-fbbd-4893-9b75-0f61c177cd5d.pdf",
    "46": "b5f2a4bd-8885-4f42-909f-a2ecac329dab.pdf",
}
GABARITOS_UUID = {
    "32": "1750075e-7f13-4caa-aebe-4de0f9b96e8f.pdf",
    "33": "0f6c7896-6e63-4791-b96e-9861acd22b66.pdf",
    "34": "3e2cb64d-1537-4750-9b86-38455cd68bca.pdf",
    "38": "899aa8b1-ad89-4f8a-8eae-6fa62154c0da.pdf",
    "40": "17139d3a-6991-4ff5-baaf-d9b69dc16fc8.pdf",
    "41": "84fbe13b-0efb-4b50-b729-aaba9edd95e5.pdf",
    "42": "f7a7e51f-5468-402d-b594-c09a0e499b9f.pdf",
    "43": "2d003602-840e-4ef2-9a4a-004144a35268.pdf",
    "44": "b6fb7503-e2cf-4e9b-8b0a-9b822df591fe.pdf",
    "45": "038bd1b7-d255-4323-ac1f-c59351757484.pdf",
    "46": "0662d6ed-01a3-4ee5-905f-a6704d72992b.pdf",
    "47": "572dc8e2-78a0-4e37-b6de-20709e2c59ab.pdf",
}

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


def _com_nome_padrao(padrao, base):
    achados = dict(base)
    for f in glob.glob(os.path.join(PASTA_PDFS, padrao)):
        achados[re.match(r"OAB (\S+) -", os.path.basename(f)).group(1)] = os.path.basename(f)
    return achados


def cadernos():
    """{exame: arquivo do caderno tipo 1}"""
    return _com_nome_padrao("OAB * - Caderno de Prova - Tipo 1.pdf", CADERNOS_UUID)


def gabaritos():
    """{exame: arquivo do gabarito da 1ª fase}"""
    return _com_nome_padrao("OAB * - Gabarito*.pdf", GABARITOS_UUID)


def caminho(nome):
    return os.path.join(PASTA_PDFS, nome)


def total_questoes(exame):
    return 100 if exame.startswith("2010") else 80


def ordem_cronologica(exame):
    return float(exame) if "." in exame else float(exame) + 2010
