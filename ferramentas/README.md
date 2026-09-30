# Ferramentas: geração do banco de questões

Scripts que leem os PDFs oficiais da OAB (cadernos de prova tipo 1 e gabaritos) e geram os arquivos `q-<matéria>.json` e `meta.json` usados pelo app. Esta pasta não é publicada pelo Cloudflare (está no `.assetsignore`).

## Como rodar

```bash
python3 -m venv ferramentas/.venv
ferramentas/.venv/bin/pip install -r ferramentas/requirements.txt
ferramentas/.venv/bin/python ferramentas/gerar.py --reextrair
```

Os PDFs são procurados em `~/Downloads`. Para usar outra pasta: `OAB_PDFS=/caminho/da/pasta`.

## Incluir um exame novo (ex.: 48º)

1. Baixe do site da OAB o caderno tipo 1 e o gabarito definitivo da 1ª fase.
2. Salve como `OAB 48 - Caderno de Prova - Tipo 1.pdf` e `OAB 48 - Gabarito Definitivo.pdf` na pasta dos PDFs.
3. Se houver comunicado de anulação, acrescente as questões em `ANULADAS` (`fontes.py`). Anuladas marcadas com `*` no gabarito definitivo já são descartadas sozinhas.
4. Rode `gerar.py --reextrair` e confira a linha do exame no resumo (ex.: `48  ET8 FI2 CO6 ...`). Se a distribuição do edital mudar, ajuste `MODELOS` em `classificar.py`.
5. Faça commit dos `q-*.json` e do `meta.json`. O Cloudflare publica sozinho.

## Como funciona

| Arquivo | O que faz |
|---|---|
| `fontes.py` | Pasta dos PDFs, nomes dos arquivos e questões anuladas por exame. |
| `extrair.py` | Lê o caderno em duas colunas, remove cabeçalhos e rodapés, separa enunciado e alternativas. Corrige PDFs que quebram cada linha em dois pedaços. |
| `ocr.py` | OCR (Vision, macOS) para páginas com fonte sem mapa de caracteres, hoje parte do XXXV Exame. |
| `gabaritos.py` | Lê o gabarito tipo 1 (três formatos diferentes ao longo dos anos). |
| `lexico.py` | Palavras-chave e leis citadas que indicam cada matéria. |
| `classificar.py` | Divide cada prova em blocos de matérias, seguindo a ordem e a quantidade do edital de cada época. |
| `montar.py` | Junta tudo, limpa o texto, descarta anuladas e grava os JSON. |
| `gerar.py` | Roda as etapas acima. A extração fica em cache em `saida/`. |

Os cadernos não dizem a matéria de cada questão, então ela é deduzida pela posição na prova. As fronteiras entre matérias vizinhas (ex.: Trabalho e Processo do Trabalho) podem ter pequenos desvios.
