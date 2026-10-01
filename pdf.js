"use strict";
// Gera a prova em PDF (questões + gabarito no final) com jsPDF.
// Sempre em preto no branco, na Fonte OAB (medidas da Calibri dos cadernos) e com o espaçamento
// entre linhas da prova. Duas diagramações:
//   "prova"         igual ao caderno da OAB: A4, 2 colunas, corpo 9, número da questão sobre um fio,
//                   fio entre as colunas, texto justificado, sem matéria/origem no corpo;
//   "personalizado" 1, 2 ou 3 colunas, corpo 9 a 12, com matéria e origem de cada questão.
// Com info.respostas, gera a correção de um simulado feito, na mesma diagramação, mas colorida: a
// alternativa certa em verde (com sinal de certo) e a marcada errada em vermelho (com X), além de
// uma linha escrita por questão ("Errada: você marcou B; a certa é C"), para quem não distingue cores
// ou imprime em preto e branco.
// Funciona no navegador (window.SimuladoPdf) e no Node (module.exports), para testes.
(function (root) {
  const JSPDF_URL = "https://cdnjs.cloudflare.com/ajax/libs/jspdf/4.2.1/jspdf.umd.min.js";
  const JSPDF_SRI = "sha384-qovJwSBbRDPP5cEjCp8S0UP66wrvnjaa60XMOGzTNanrThcrGfXfnZkvgY8N1KT3";
  const FONTE_OAB = { normal: "fonts/FonteOAB-Regular.ttf", bold: "fonts/FonteOAB-Bold.ttf" };

  // Medidas do caderno da OAB (em pt, para corpo 9). Em outros corpos, tudo é proporcional.
  const PROVA = {
    entrelinha: 11.03,  // entre linhas do mesmo parágrafo (1,2256 x corpo)
    paragrafo: 13.03,   // entre parágrafos do enunciado e antes da alternativa (A)
    alternativa: 11.9,  // entre uma alternativa e a seguinte
    numeroTexto: 17.1,  // da linha do número da questão à primeira linha do texto
    textoNumero: 20.7,  // da última linha de uma questão ao número da seguinte
    numero: 11,         // corpo do número da questão (negrito)
    fio: 4.0,           // distância do número ao fio abaixo dele
    recuo: 14.2,        // recuo do texto das alternativas
    topoNumero: 10.4,   // do topo da coluna à linha do número
  };
  const A4 = { w: 595.28, h: 841.89 };
  const LETTERS = "ABCD";
  // Cores da correção (texto sobre fundo com contraste acima de 6:1)
  const COR = {
    certa: { texto: [22, 101, 62], fundo: [226, 243, 233] },
    errada: { texto: [166, 32, 26], fundo: [251, 231, 229] },
    branco: [90, 90, 90],
  };

  // Helvetica (reserva) só cobre Latin-1: troca aspas curvas, travessões etc.
  function latin1Helvetica(s) {
    return s
      .replace(/[“”„]/g, '"').replace(/[‘’‚]/g, "'")
      .replace(/[–—−]/g, "-").replace(/…/g, "...").replace(/•/g, "-")
      .replace(/[^\u0000-ÿ]/g, "");
  }
  // A Fonte OAB cobre Latin-1 e a pontuação geral (aspas curvas, travessões, reticências).
  function oab(s) {
    return s.replace(/[^\u0000-ÿıŒœ‐-‧‰-⁞€™−]/g, "");
  }

  function geometria(layout) {
    if (!layout || layout.modo !== "personalizado") {
      // caderno da OAB: margens 42,6 / 40,6 pt, colunas de 243 pt e 26 pt de intervalo
      return { corpo: 9, colunas: 2, esq: 42.6, dir: 40.6, intervalo: 26.1, topo: 67.5, base: 780, origem: false };
    }
    const colunas = [1, 2, 3].includes(+layout.colunas) ? +layout.colunas : 2;
    const corpo = [9, 10, 11, 12].includes(+layout.tamanho) ? +layout.tamanho : 10;
    return { corpo, colunas, esq: 45, dir: 45, intervalo: colunas > 1 ? 22 : 0, topo: 67.5, base: 780, origem: true };
  }

  // fonte: { normal, bold } em base64 (TTF). Sem ela, o PDF sai em Helvetica.
  // layout: { modo: "prova" | "personalizado", colunas, tamanho }
  // info: { label, date } na prova; na correção também respostas (índice ou null, uma por
  // questão) e resumo (linha com acertos, modo e tempo).
  function montar(jsPDF, items, info, fonte, layout) {
    const correcao = Array.isArray(info.respostas);
    const doc = new jsPDF({ unit: "pt", format: "a4", compress: true });
    if (typeof doc.setLanguage === "function") doc.setLanguage("pt-BR");
    let familia = "helvetica", txt = latin1Helvetica;
    if (fonte && fonte.normal && fonte.bold) {
      doc.addFileToVFS("FonteOAB-Regular.ttf", fonte.normal);
      doc.addFont("FonteOAB-Regular.ttf", "FonteOAB", "normal");
      doc.addFileToVFS("FonteOAB-Bold.ttf", fonte.bold);
      doc.addFont("FonteOAB-Bold.ttf", "FonteOAB", "bold");
      familia = "FonteOAB"; txt = oab;
    }
    const titulo = txt(correcao ? "Correção do simulado OAB – 1ª fase" : "Simulado OAB – 1ª fase");
    doc.setProperties({ title: titulo, subject: info.label, creator: "Simulados OAB" });
    doc.setTextColor(0, 0, 0); doc.setDrawColor(0, 0, 0);

    const g = geometria(layout);
    if (correcao) g.origem = true; // na correção, matéria e origem sempre aparecem
    const m = (v) => v * g.corpo / 9; // medida da prova na escala do corpo escolhido
    const largura = A4.w - g.esq - g.dir;
    const colW = (largura - g.intervalo * (g.colunas - 1)) / g.colunas;
    const colX = (c) => g.esq + c * (colW + g.intervalo);
    const font = (style, size) => { doc.setFont(familia, style); doc.setFontSize(size); };

    // trechos de texto em sequência na mesma linha: [texto, cor ou null, negrito?]
    const trechos = (partes, x, y, size) => {
      for (const [t, cor, negrito] of partes) {
        font(negrito ? "bold" : "normal", size);
        doc.setTextColor(...(cor || [0, 0, 0]));
        doc.text(txt(t), x, y);
        x += doc.getTextWidth(txt(t));
      }
      doc.setTextColor(0, 0, 0);
    };
    // sinais de certo e X desenhados (a Fonte OAB não tem ✓ e ✗), à esquerda do texto
    const sinal = (tipo, x, y) => {
      doc.setLineWidth(1.1); doc.setLineCap("round");
      if (tipo === "certa") {
        doc.setDrawColor(...COR.certa.texto);
        doc.line(x, y - 3, x + 1.8, y - 1); doc.line(x + 1.8, y - 1, x + 5.2, y - 6);
      } else {
        doc.setDrawColor(...COR.errada.texto);
        doc.line(x, y - 6, x + 4.6, y - 1.2); doc.line(x + 4.6, y - 6, x, y - 1.2);
      }
      doc.setDrawColor(0, 0, 0); doc.setLineCap("butt");
    };

    // --- título da primeira página (largura total) ---
    font("bold", 14);
    doc.text(titulo, g.esq, 56);
    font("normal", 8.5);
    doc.text(doc.splitTextToSize(txt(`${items.length} questões · ${info.label}`), largura)[0], g.esq, 70);
    let regua = 88;
    if (correcao) {
      doc.text(doc.splitTextToSize(txt(info.resumo), largura)[0], g.esq, 81);
      trechos([
        ["Em ", null], ["verde", COR.certa.texto, true], [" (com sinal de certo), a resposta certa; em ", null],
        ["vermelho", COR.errada.texto, true], [" (com X), a sua resposta quando errada.", null],
      ], g.esq, 92, 8.5);
      regua = 99;
    } else {
      doc.text(doc.splitTextToSize(txt(`Gerado em ${info.date} · questões oficiais do Exame de Ordem Unificado (OAB/FGV), sem as anuladas. Gabarito na última página.`), largura)[0], g.esq, 81);
    }
    doc.setLineWidth(0.5); doc.line(g.esq, regua, A4.w - g.dir, regua);
    const topoPagina1 = regua + 8;

    // --- fluxo em colunas: "base" é a linha de base do último elemento da coluna atual ---
    let pagina = 1, col = 0, base = null;
    const usoColuna = {}; // pagina -> { coluna: última linha de base }
    const topoAtual = () => (pagina === 1 ? topoPagina1 : g.topo);
    const proximaColuna = () => {
      if (col < g.colunas - 1) col++;
      else { doc.addPage(); pagina++; col = 0; }
      base = null;
    };
    // gap: distância entre linhas de base; primeira: do topo da coluna; reserva: espaço que precisa caber junto
    const posicionar = (gap, primeira, reserva) => {
      let b = base === null ? topoAtual() + primeira : base + gap;
      if (b + (reserva || 0) > g.base) { proximaColuna(); b = topoAtual() + primeira; }
      base = b;
      usoColuna[pagina] = usoColuna[pagina] || {};
      usoColuna[pagina][col] = b;
      return b;
    };

    // justificação feita à mão (o justify do jsPDF não funciona com fontes embutidas); como no Word da
    // prova, todas as linhas são justificadas, menos a última de cada parágrafo
    const linhaJustificada = (linha, x, y, w, ultima) => {
      const palavras = linha.split(" ").filter(Boolean);
      if (ultima || palavras.length < 2) { doc.text(linha, x, y); return; }
      const total = palavras.reduce((a, p) => a + doc.getTextWidth(p), 0);
      const espaco = (w - total) / (palavras.length - 1);
      let cx = x;
      for (const p of palavras) { doc.text(p, cx, y); cx += doc.getTextWidth(p) + espaco; }
    };
    const paragrafo = (texto, dx, gapPrimeira) => {
      font("normal", g.corpo);
      const w = colW - dx;
      const linhas = doc.splitTextToSize(txt(texto), w);
      linhas.forEach((linha, i) => {
        const y = posicionar(i === 0 ? gapPrimeira : m(PROVA.entrelinha), m(9));
        linhaJustificada(linha, colX(col) + dx, y, w, i === linhas.length - 1);
      });
    };

    let materia = null, aposMateria = false;
    items.forEach((q, i) => {
      if (g.origem && q.subjectName !== materia) { // matéria: só no personalizado
        materia = q.subjectName; aposMateria = true;
        font("bold", g.corpo * 0.9);
        // em colunas estreitas o nome da matéria quebra em mais de uma linha
        const linhas = doc.splitTextToSize(txt(materia.toUpperCase()), colW);
        linhas.forEach((linha, k) => {
          const y = k === 0
            ? posicionar(m(PROVA.textoNumero), m(9), m(PROVA.textoNumero + PROVA.numeroTexto + PROVA.entrelinha * (linhas.length + 1)))
            : posicionar(m(PROVA.entrelinha), m(9));
          doc.text(linha, colX(col), y);
        });
      }
      // número da questão e fio, com ao menos 3 linhas de texto na mesma coluna
      const gapNumero = aposMateria ? m(PROVA.entrelinha * 1.6) : m(PROVA.textoNumero);
      aposMateria = false;
      const yNum = posicionar(gapNumero, m(PROVA.topoNumero), m(PROVA.numeroTexto + PROVA.entrelinha * 2));
      font("bold", m(PROVA.numero));
      doc.text(String(i + 1), colX(col), yNum);
      if (g.origem) {
        const w = doc.getTextWidth(`${i + 1}  `);
        font("normal", g.corpo * 0.8);
        const origem = txt(`${q.e}, questão ${q.n}${q.topicName ? " · " + q.topicName : ""}`);
        doc.text(doc.splitTextToSize(origem, colW - w)[0], colX(col) + w, yNum);
      }
      doc.setLineWidth(0.5);
      doc.line(colX(col) - 1.5, yNum + m(PROVA.fio), colX(col) + colW, yNum + m(PROVA.fio));

      // correção: situação da questão por escrito, logo abaixo do número
      const resp = correcao ? info.respostas[i] : null;
      if (correcao) {
        const [cor, msg] = resp == null ? [COR.branco, `Em branco. A resposta certa é ${LETTERS[q.r]}.`]
          : resp === q.r ? [COR.certa.texto, `Certa: você marcou ${LETTERS[resp]}.`]
          : [COR.errada.texto, `Errada: você marcou ${LETTERS[resp]}; a certa é ${LETTERS[q.r]}.`];
        font("bold", g.corpo);
        doc.setTextColor(...cor);
        doc.text(txt(msg), colX(col), posicionar(m(PROVA.numeroTexto), m(9)));
        doc.setTextColor(0, 0, 0);
      }
      q.q.split("\n").forEach((para, j) => paragrafo(para, 0, j === 0 && !correcao ? m(PROVA.numeroTexto) : m(PROVA.paragrafo)));
      q.a.forEach((alt, j) => {
        const destaque = !correcao ? null : j === q.r ? "certa" : j === resp ? "errada" : null;
        font(destaque ? "bold" : "normal", g.corpo);
        const w = colW - m(PROVA.recuo);
        const linhas = doc.splitTextToSize(txt(alt), w);
        linhas.forEach((linha, l) => {
          const gap = l > 0 ? m(PROVA.entrelinha) : (j === 0 ? m(PROVA.paragrafo) : m(PROVA.alternativa));
          const y = posicionar(gap, m(9));
          if (destaque) {
            // faixa de fundo linha a linha (a alternativa pode mudar de coluna no meio)
            const ultima = l === linhas.length - 1;
            doc.setFillColor(...COR[destaque].fundo);
            doc.rect(colX(col) - 1.5, y - m(8.6), colW + 3, ultima ? m(12) : m(PROVA.entrelinha), "F");
            doc.setTextColor(...COR[destaque].texto);
            if (l === 0) sinal(destaque, colX(col) - 8.5, y);
          }
          if (l === 0) doc.text(`(${LETTERS[j]})`, colX(col), y);
          linhaJustificada(linha, colX(col) + m(PROVA.recuo), y, w, l === linhas.length - 1);
        });
        doc.setTextColor(0, 0, 0);
      });
    });

    // fio entre as colunas, do topo até o fim do conteúdo de cada página
    if (g.colunas > 1) {
      doc.setLineWidth(0.7);
      for (const [p, cols] of Object.entries(usoColuna)) {
        doc.setPage(+p);
        const topo = +p === 1 ? topoPagina1 : g.topo;
        for (let c = 1; c < g.colunas; c++) {
          if (!cols[c]) continue;
          const x = colX(c) - g.intervalo / 2;
          doc.line(x, topo, x, Math.max(cols[c - 1] || 0, cols[c]) + m(3.3));
        }
      }
    }

    // --- gabarito (página própria, largura total); na correção, com a sua resposta ao lado ---
    doc.addPage();
    font("bold", 14);
    doc.text(correcao ? txt("Gabarito e suas respostas") : "Gabarito", g.esq, 56);
    doc.setLineWidth(0.5); doc.line(g.esq, 64, A4.w - g.dir, 64);
    let inicio = 84;
    if (correcao) {
      trechos([
        ["Em cada linha: número, resposta certa, a sua resposta (", null], ["verde", COR.certa.texto, true],
        [" se acertou, ", null], ["vermelho", COR.errada.texto, true], [" se errou, – em branco) e a origem.", null],
      ], g.esq, 78, 8.5);
      inicio = 96;
    }
    const porColuna = Math.ceil(items.length / 2), metade = largura / 2;
    const passo = Math.min(PROVA.paragrafo, (780 - inicio) / porColuna);
    const dxOrigem = correcao ? 54 : 38;
    items.forEach((q, i) => {
      const c = Math.floor(i / porColuna), y = inicio + (i % porColuna) * passo, x = g.esq + c * metade;
      font("bold", 9.5);
      doc.text(`${i + 1}.`, x + 18, y, { align: "right" });
      doc.text(LETTERS[q.r], x + 24, y);
      if (correcao) {
        const r = info.respostas[i];
        doc.setTextColor(...(r == null ? COR.branco : r === q.r ? COR.certa.texto : COR.errada.texto));
        doc.text(r == null ? txt("–") : LETTERS[r], x + 38, y);
        doc.setTextColor(0, 0, 0);
      }
      font("normal", 8.5);
      doc.text(doc.splitTextToSize(txt(`${q.subjectShort} · ${q.e}, q. ${q.n}`), metade - dxOrigem - 6)[0], x + dxOrigem, y);
    });

    // --- cabeçalho e rodapé de todas as páginas ---
    const total = doc.getNumberOfPages();
    for (let p = 1; p <= total; p++) {
      doc.setPage(p);
      font("normal", 7);
      if (p > 1) doc.text(txt(correcao ? "CORREÇÃO DO SIMULADO OAB – 1ª FASE" : "SIMULADO OAB – 1ª FASE"), A4.w - g.dir, 49, { align: "right" });
      doc.setLineWidth(0.5); doc.line(48, 794, A4.w - 37, 794);
      doc.text("Simulados OAB", 48, 805.5);
      doc.text(txt(`Página ${p} de ${total}`), A4.w - 37, 805.5, { align: "right" });
    }
    return doc;
  }

  function carregarJsPdf() {
    if (root.jspdf && root.jspdf.jsPDF) return Promise.resolve(root.jspdf.jsPDF);
    return new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = JSPDF_URL; s.integrity = JSPDF_SRI; s.crossOrigin = "anonymous"; s.async = true;
      s.onload = () => (root.jspdf && root.jspdf.jsPDF ? resolve(root.jspdf.jsPDF) : reject(new Error("jsPDF indisponível")));
      s.onerror = () => reject(new Error("Não foi possível carregar o gerador de PDF. Verifique a conexão."));
      document.head.appendChild(s);
    });
  }

  let fonteCache = null;
  async function carregarFonte() {
    if (fonteCache) return fonteCache;
    const base64 = (buf) => {
      const bytes = new Uint8Array(buf);
      let bin = "";
      for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
      return btoa(bin);
    };
    const ler = async (url) => {
      const r = await fetch(url);
      if (!r.ok) throw new Error(`${url}: ${r.status}`);
      return base64(await r.arrayBuffer());
    };
    const [normal, bold] = await Promise.all([ler(FONTE_OAB.normal), ler(FONTE_OAB.bold)]);
    fonteCache = { normal, bold };
    return fonteCache;
  }

  async function baixar(items, info, filename, layout) {
    const [jsPDF, fonte] = await Promise.all([
      carregarJsPdf(),
      carregarFonte().catch((e) => { console.warn("Fonte OAB indisponível no PDF; usando Helvetica.", e); return null; }),
    ]);
    montar(jsPDF, items, info, fonte, layout).save(filename);
  }

  const api = { montar, baixar, latin1: latin1Helvetica, oab, PROVA };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.SimuladoPdf = api;
})(typeof window !== "undefined" ? window : globalThis);
