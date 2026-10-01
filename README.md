# Simulados OAB

Simulador online da 1ª fase do Exame de Ordem, com 3.665 questões oficiais de 46 provas (Exame 2010.2 ao 47º) separadas por matéria.

- Escolha até 3 matérias, ou use os botões de grupo: todas as matérias (prova completa na proporção da OAB), Estatuto da OAB e Código de Ética, mais recorrentes, recorrência média, menos recorrentes.
- Opção "só temas mais recorrentes": usa apenas questões dos assuntos que mais caíram em cada matéria.
- Cada clique em "Sortear simulado" monta uma prova nova, evitando repetir questões de sorteios recentes.
- "Baixar prova em PDF": sorteia uma prova e baixa o PDF com o gabarito na última página, sempre em preto no branco, na Fonte OAB e com a entrelinha da prova. Diagramação "igual à prova da OAB" (2 colunas, corpo 9, fios e justificação do caderno) ou "personalizado" (1 a 3 colunas, corpo 9 a 12). Usa jsPDF, carregado do cdnjs só nessa hora.
- Modo prova (gabarito no final) ou modo estudo (resposta a cada questão), cronômetro opcional no ritmo da OAB.
- Aparência ajustável na tela inicial e, a qualquer momento (inclusive durante o simulado), pelo ícone de formatação no alto da tela: 6 fontes (Fonte OAB, a padrão, com as medidas da Calibri dos cadernos; iA Writer Duo, Atkinson Hyperlegible, Lexend, Literata, Lora), embarcadas em `fonts/`, e 8 combinações de cor de fundo e texto.
- Correção com desempenho por matéria, histórico, "sortear outro simulado" com a mesma configuração e opção de refazer as questões erradas.
- "Correção em PDF" em cada simulado do histórico: todas as questões, com a resposta certa em verde (e sinal de certo) e a resposta errada em vermelho (e X), uma linha por questão dizendo o que foi marcado e, no fim, o gabarito ao lado das suas respostas. Usa a mesma diagramação escolhida para o PDF da prova. O histórico guarda só os códigos das questões e as respostas; os textos vêm do banco na hora.

## Estrutura

- `index.html`, `style.css`, `app.js`: o app (HTML/CSS/JS puro, sem build).
- `tema.js`: aplica a fonte e as cores salvas antes de desenhar a página (usado por todas as páginas).
- `pdf.js`: geração da prova em PDF.
- `privacidade.html`, `privacidade.js`: política de privacidade, com o botão que apaga os dados do navegador. O link fica no rodapé da tela inicial.
- `404.html`: página de endereço inexistente.
- `_headers`: cabeçalhos de segurança (CSP e outros). O Cloudflare lê e não publica. Veja os comentários no arquivo.
- `fonts/`: fontes embarcadas e suas licenças (SIL OFL 1.1). Veja `fonts/README.md`.
- `q-<materia>.json`: questões de cada matéria (`q` enunciado, `a` alternativas, `r` índice da correta, `e` exame, `n` número da questão no caderno tipo 1, `t` tema).
- `meta.json`: total de questões por matéria e temas de cada matéria (com os mais recorrentes marcados).
- `wrangler.jsonc`: configuração do Cloudflare Workers (arquivos estáticos). O deploy roda `npx wrangler deploy`.
- `.assetsignore`: lista do que é publicado. Tudo fica de fora, menos os arquivos liberados nela com `!`.
- `ferramentas/`: scripts que geram o banco de questões a partir dos PDFs da OAB (não são publicados). Veja `ferramentas/README.md`.

## Privacidade e segurança

- Sem cookies, sem analytics e sem rastreadores. Tudo o que o app guarda (preferências, simulado em andamento, histórico, questões vistas) fica no `localStorage` do navegador, nas chaves `oab.*`, e nunca é enviado ao servidor.
- Única dependência externa: o jsPDF, carregado do cdnjs só ao baixar o PDF, com verificação de integridade (SRI).
- Arquivo novo do site só vai ao ar se for liberado no `.assetsignore`. Não use scripts inline nas páginas: a CSP só aceita scripts em arquivo.

## Origem dos dados

Cadernos de prova tipo 1 e gabaritos publicados em examedeordem.oab.org.br. Questões anuladas (pelos gabaritos definitivos e comunicados de anulação) foram removidas. A matéria de cada questão foi identificada automaticamente pela ordem dos blocos de matérias em cada prova, então pode haver pequenos desvios nas fronteiras entre matérias.
