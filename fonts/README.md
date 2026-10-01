# Fontes embarcadas no app

Todas sob a SIL Open Font License 1.1 (textos de licença nesta pasta). A Calibri, usada nos cadernos da OAB, é da Microsoft e não pode ser redistribuída; por isso a Fonte OAB usa a Carlito, que tem as mesmas medidas.

| Fonte | Arquivos | Origem | Observação |
|---|---|---|---|
| Fonte OAB | `FonteOAB-*.woff2` / `.woff` (regular, negrito, itálico, negrito itálico) | [google/fonts: Carlito](https://github.com/google/fonts/tree/main/ofl/carlito) | Substituta livre da Calibri, a fonte dos cadernos de prova (mesmas medidas). Subconjunto latino, renomeado para "Fonte OAB" porque "Carlito" é nome reservado. No CSS, a Calibri original é usada quando já existe no aparelho (`local()`). `FonteOAB-Regular.ttf` e `FonteOAB-Bold.ttf` são as mesmas fontes em TTF, embutidas no PDF da prova (o jsPDF só aceita TTF). Licença em `OFL-Carlito.txt`. |
| iA Writer Duo S | `iAWriterDuoS-*.woff2` / `.woff` (regular, negrito, itálico, negrito itálico) | [iaolo/iA-Fonts](https://github.com/iaolo/iA-Fonts/tree/master/iA%20Writer%20Duo/Webfonts) | Webfonts oficiais, sem alteração (nomes reservados "iA Writer" e "Plex"). |
| Atkinson Hyperlegible | `AtkinsonHyperlegible-*.woff2` / `.woff` | [google/fonts](https://github.com/google/fonts/tree/main/ofl/atkinsonhyperlegible) | Convertida de TTF para woff2/woff. |
| Lexend | `Lexend-wght.ttf` (variável, pesos 100–900) | [google/fonts](https://github.com/google/fonts/tree/main/ofl/lexend) | Arquivo original, sem alteração (nome reservado "RevReading Lexend"). |
| Literata | `Literata-*.woff2` / `.woff` | [google/fonts](https://github.com/google/fonts/tree/main/ofl/literata) | Instâncias estáticas (tamanho óptico 12, pesos 400 e 700), só alfabeto latino. |
| Lora | `Lora-wght.ttf` (variável, pesos 400–700) | [google/fonts](https://github.com/google/fonts/tree/main/ofl/lora) | Arquivo original, sem alteração (nome reservado "Lora"). |

O navegador só baixa a fonte escolhida (e as amostras, quando o painel "Aparência" é aberto).
