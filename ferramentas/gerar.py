"""Gera o banco de questões do app a partir dos PDFs da OAB.

    python3 ferramentas/gerar.py              # usa a extração em cache, se houver
    python3 ferramentas/gerar.py --reextrair  # lê todos os PDFs de novo

Grava q-<matéria>.json e meta.json na raiz do repositório. A extração dos PDFs (a parte
lenta) fica em cache em ferramentas/saida/brutas.json.
"""
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import fontes  # noqa: E402
from classificar import classificar, resumo  # noqa: E402
from extrair import extrair_todos  # noqa: E402
from montar import montar  # noqa: E402

RAIZ = os.path.dirname(AQUI)
CACHE = os.path.join(AQUI, "saida", "brutas.json")


def main():
    if "--reextrair" in sys.argv or not os.path.exists(CACHE):
        print(f"Extraindo cadernos de {fontes.PASTA_PDFS} …")
        brutas = extrair_todos()
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with open(CACHE, "w") as f:
            json.dump(brutas, f, ensure_ascii=False)
    else:
        with open(CACHE) as f:
            brutas = json.load(f)
        print(f"Usando extração em cache ({len(brutas)} cadernos). Use --reextrair para ler os PDFs de novo.")

    print("Classificando por matéria (blocos por prova):")
    materias = {}
    for exame in sorted(brutas, key=fontes.ordem_cronologica):
        materias[exame] = classificar(exame, brutas[exame])
        print(f"  {exame:7s} {resumo(materias[exame])}")

    meta, descartes = montar(brutas, materias, RAIZ)
    print(f"\n{meta['total']} questões de {meta['exams']} provas gravadas em {RAIZ}")
    print(f"Descartadas: {descartes}")


if __name__ == "__main__":
    main()
