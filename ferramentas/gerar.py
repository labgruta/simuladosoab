"""Gera o banco de questões do app.

    python3 ferramentas/gerar.py              # usa dados/ e lê só os PDFs de exames novos
    python3 ferramentas/gerar.py --reextrair  # relê todos os PDFs presentes na pasta
    python3 ferramentas/gerar.py --reextrair 2010.2 38   # relê só esses exames

As questões extraídas e os gabaritos já processados ficam versionados em ferramentas/dados/
(brutas.json e gabaritos.json), então nenhum PDF antigo é necessário. Um PDF só é lido quando
o exame ainda não está nesses arquivos (ex.: o 48º) ou com --reextrair. O resultado é gravado
em q-<matéria>.json e meta.json, na raiz do repositório.
"""
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import fontes  # noqa: E402
from classificar import classificar, resumo  # noqa: E402
from montar import montar  # noqa: E402

RAIZ = os.path.dirname(AQUI)
BRUTAS = os.path.join(fontes.DADOS, "brutas.json")
GABARITOS = os.path.join(fontes.DADOS, "gabaritos.json")


def _ler(caminho):
    if not os.path.exists(caminho):
        return {}
    with open(caminho) as f:
        return json.load(f)


def _gravar(caminho, dados):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w") as f:
        json.dump(dados, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main():
    reextrair = "--reextrair" in sys.argv
    so = {a for a in sys.argv[1:] if not a.startswith("--")}  # exames específicos para reextrair
    brutas, gabaritos = _ler(BRUTAS), _ler(GABARITOS)
    print(f"Dados versionados: {len(brutas)} provas. PDFs procurados em {fontes.PASTA_PDFS}")

    cadernos = {ex: a for ex, a in fontes.cadernos().items() if (reextrair and (not so or ex in so)) or ex not in brutas}
    if cadernos:
        from extrair import extrair_caderno  # só precisa do PyMuPDF quando há PDF para ler
        for exame, arquivo in sorted(cadernos.items()):
            qs = extrair_caderno(fontes.caminho(arquivo), palavras=exame in fontes.EXTRAIR_POR_PALAVRAS)
            problemas = [q["n"] for q in qs if len(q["alts"]) != 4 or not q["stem"]]
            print(f"  caderno {exame}: {len(qs)} questões" + (f"  problemas: {problemas}" if problemas else ""))
            brutas[exame] = qs
        _gravar(BRUTAS, brutas)

    arquivos_gab = {ex: a for ex, a in fontes.gabaritos().items() if (reextrair and (not so or ex in so)) or ex not in gabaritos}
    if arquivos_gab:
        from gabaritos import gabarito_do_pdf
        for exame in sorted(arquivos_gab):
            g = gabarito_do_pdf(exame)
            print(f"  gabarito {exame}: {len(g)} respostas")
            gabaritos[exame] = {str(n): letra for n, letra in g.items()}
        _gravar(GABARITOS, gabaritos)

    sem_gabarito = sorted(set(brutas) - set(gabaritos))
    if sem_gabarito:
        sys.exit(f"Falta o gabarito de: {', '.join(sem_gabarito)}. Salve o PDF como 'OAB NN - Gabarito Definitivo.pdf'.")
    gabaritos = {ex: {int(n): l for n, l in g.items()} for ex, g in gabaritos.items()}

    print("Classificando por matéria (blocos por prova):")
    materias = {}
    for exame in sorted(brutas, key=fontes.ordem_cronologica):
        materias[exame] = classificar(exame, brutas[exame])
        print(f"  {exame:7s} {resumo(materias[exame])}")

    meta, descartes = montar(brutas, materias, gabaritos, RAIZ)
    print(f"\n{meta['total']} questões sorteáveis de {meta['exams']} provas gravadas em {RAIZ}")
    print(f"Descartadas: {descartes}. Desatualizadas pela lei (ficam no banco com aviso, fora dos sorteios): {meta['desatualizadas']}")
    print("\nTemas mais recorrentes por matéria:")
    for materia, temas in meta["temas"].items():
        rec = [f"{t['nome']} ({t['n']})" for t in temas if t["rec"]]
        print(f"  {materia:15s} {'; '.join(rec)}")


if __name__ == "__main__":
    main()
