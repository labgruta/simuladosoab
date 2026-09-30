# Simulados OAB

Simulador online da 1ª fase do Exame de Ordem, com 3.665 questões oficiais de 46 provas (Exame 2010.2 ao 47º) separadas por matéria.

- Escolha até 3 matérias, ou use os botões de grupo (Estatuto da OAB e Código de Ética, mais recorrentes, recorrência média, menos recorrentes).
- Modo prova (gabarito no final) ou modo estudo (resposta a cada questão), cronômetro opcional no ritmo da OAB.
- Correção com desempenho por matéria, histórico e opção de refazer as questões erradas.

## Estrutura

- `index.html`, `style.css`, `app.js`: o app (HTML/CSS/JS puro, sem build).
- `q-<materia>.json`: questões de cada matéria (`q` enunciado, `a` alternativas, `r` índice da correta, `e` exame, `n` número da questão no caderno tipo 1).
- `meta.json`: total de questões por matéria.
- `wrangler.jsonc`: configuração do Cloudflare Workers (arquivos estáticos). O deploy roda `npx wrangler deploy`.
- `ferramentas/`: scripts que geram o banco de questões a partir dos PDFs da OAB (não são publicados). Veja `ferramentas/README.md`.

## Origem dos dados

Cadernos de prova tipo 1 e gabaritos publicados em examedeordem.oab.org.br. Questões anuladas (pelos gabaritos definitivos e comunicados de anulação) foram removidas. A matéria de cada questão foi identificada automaticamente pela ordem dos blocos de matérias em cada prova, então pode haver pequenos desvios nas fronteiras entre matérias.
