# Ferramentas: geração do banco de questões

Scripts que leem os PDFs oficiais da OAB (cadernos de prova tipo 1 e gabaritos) e geram os arquivos `q-<matéria>.json` e `meta.json` usados pelo app. Esta pasta não é publicada pelo Cloudflare (está no `.assetsignore`).

As questões já extraídas e os gabaritos dos 46 exames processados (2010.2 ao 47º) ficam em `dados/` (`brutas.json` e `gabaritos.json`). Por isso os PDFs antigos não são mais necessários: o banco pode ser regerado a qualquer momento só com esses arquivos, e PDFs só entram para incluir um exame novo.

## Como rodar

```bash
python3 ferramentas/gerar.py
```

Sem PDFs, isso regera o banco a partir de `dados/` (não precisa instalar nada). Para ler PDFs, instale as dependências antes:

```bash
python3 -m venv ferramentas/.venv
ferramentas/.venv/bin/pip install -r ferramentas/requirements.txt
```

Os PDFs são procurados em `~/Downloads/Provas OAB` (inclusive subpastas). Para usar outra pasta: `OAB_PDFS=/caminho/da/pasta`. Só são lidos os PDFs de exames que ainda não estão em `dados/`; `--reextrair` relê todos os PDFs presentes na pasta (`--reextrair 2010.2 38` relê só esses exames).

## Baixar os PDFs oficiais e revisar o banco

```bash
ferramentas/.venv/bin/python ferramentas/baixar.py          # todos os exames; ou: baixar.py 48 47
ferramentas/.venv/bin/python ferramentas/revisar.py revisao.md
```

`baixar.py` baixa do site da OAB, para `~/Downloads/Provas OAB`, o caderno tipo 1 (`Cadernos/`), o gabarito da 1ª fase (`Gabaritos/`, o definitivo ou, na falta dele, o preliminar retificado) e os comunicados sobre a prova objetiva (`Anulações/`: anulações, avisos de que não houve anulação e gabaritos republicados com correção). Reaplicações (Salvador, Porto Alegre, Ipatinga) ficam de fora.

`revisar.py` confere o banco publicado contra esses PDFs: resposta de cada questão x gabarito oficial; questões fora do banco x anulações oficiais; texto de cada enunciado e alternativa x uma leitura independente do caderno; e alternativas repetidas. Páginas sem texto no PDF (parte do XXXV) foram conferidas pela imagem e estão listadas em `CONFERIDAS_NA_IMAGEM`.

## Incluir um exame novo (ex.: 48º)

1. Rode `ferramentas/.venv/bin/python ferramentas/baixar.py 48`. Ou baixe à mão o caderno tipo 1 e o gabarito definitivo da 1ª fase.
2. Os arquivos ficam como `OAB 48 - Caderno de Prova - Tipo 1.pdf` e `OAB 48 - Gabarito Definitivo.pdf` na pasta dos PDFs.
3. Se houver comunicado de anulação, acrescente as questões em `ANULADAS` (`fontes.py`). Anuladas marcadas com `*` no gabarito definitivo já são descartadas sozinhas.
4. Rode `ferramentas/.venv/bin/python ferramentas/gerar.py`. Ele lê só os dois PDFs novos, acrescenta o exame em `dados/` e confere a linha do exame no resumo (ex.: `48  ET8 FI2 CO6 ...`). Se a distribuição do edital mudar, ajuste `MODELOS` em `classificar.py`.
5. Faça commit de `dados/`, dos `q-*.json` e do `meta.json`. O Cloudflare publica sozinho. Depois disso os PDFs podem ser apagados.

## Como funciona

| Arquivo | O que faz |
|---|---|
| `dados/` | Questões extraídas (`brutas.json`) e gabaritos (`gabaritos.json`, `*` = anulada) de cada exame já processado. |
| `fontes.py` | Pasta dos PDFs, padrão de nome dos arquivos e questões anuladas por exame. |
| `extrair.py` | Lê o caderno em duas colunas, remove cabeçalhos e rodapés, separa enunciado e alternativas. Corrige PDFs que quebram cada linha em dois pedaços. |
| `ocr.py` | OCR (Vision, macOS) para páginas com fonte sem mapa de caracteres, hoje parte do XXXV Exame. |
| `gabaritos.py` | Lê o gabarito tipo 1 (três formatos diferentes ao longo dos anos). |
| `lexico.py` | Palavras-chave e leis citadas que indicam cada matéria. |
| `classificar.py` | Divide cada prova em blocos de matérias, seguindo a ordem e a quantidade do edital de cada época. |
| `temas.py` | Classifica cada questão num tema da matéria (ex.: Honorários, em Ética) e marca os temas mais recorrentes, os que somados cobrem 60% das questões da matéria. |
| `montar.py` | Junta tudo, limpa o texto, descarta anuladas e grava os JSON. |
| `gerar.py` | Roda as etapas acima a partir de `dados/`, lendo só os PDFs de exames novos. |
| `baixar.py` | Baixa cadernos, gabaritos e comunicados de anulação do site da OAB. |
| `revisar.py` | Confere o banco publicado contra os PDFs oficiais e grava um relatório. |

Os cadernos não dizem a matéria nem o tema de cada questão. A matéria é deduzida pela posição na prova e o tema, por palavras-chave com peso maior para termos específicos. As fronteiras entre matérias vizinhas (ex.: Trabalho e Processo do Trabalho) podem ter pequenos desvios.
