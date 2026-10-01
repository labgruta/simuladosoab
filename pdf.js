"use strict";
// Gera a prova em PDF (questões + gabarito no final) com jsPDF, na Fonte OAB (a mesma do app,
// com as medidas da Calibri dos cadernos). Se a fonte não carregar, usa Helvetica.
// Funciona no navegador (window.SimuladoPdf) e no Node (module.exports), para testes.
(function (root) {
  const JSPDF_URL = "https://cdnjs.cloudflare.com/ajax/libs/jspdf/4.2.1/jspdf.umd.min.js";
  const JSPDF_SRI = "sha384-qovJwSBbRDPP5cEjCp8S0UP66wrvnjaa60XMOGzTNanrThcrGfXfnZkvgY8N1KT3";

  const PAGE_W = 210, PAGE_H = 297, M = 18, W = PAGE_W - 2 * M;
  const BODY = 10, LINE = 4.6; // pt, mm
  const FONTE_OAB = { normal: "fonts/FonteOAB-Regular.ttf", bold: "fonts/FonteOAB-Bold.ttf" };
  const INK = [27, 35, 48], MUTED = [93, 102, 117], BRAND = [31, 58, 95], RULE = [210, 205, 195];
  const LETTERS = "ABCD";

  // As fontes padrão do PDF (Helvetica) só cobrem Latin-1: troca aspas curvas, travessões etc.
  function latin1Helvetica(s) {
    return s
      .replace(/[“”„]/g, '"').replace(/[‘’‚]/g, "'")
      .replace(/[–—−]/g, "-").replace(/…/g, "...").replace(/•/g, "-")
      .replace(/[^\u0000-ÿ]/g, "");
  }

  // A Fonte OAB cobre Latin-1 e a pontuação geral (aspas curvas, travessões, reticências).
  function oab(s) {
    return s.replace(/[^\u0000-\u00ff\u0131\u0152\u0153\u2010-\u2027\u2030-\u205e\u20ac\u2122\u2212]/g, "");
  }

  // fonte: { normal, bold } em base64 (TTF). Sem ela, o PDF sai em Helvetica.
  function montar(jsPDF, items, info, fonte) {
    const doc = new jsPDF({ unit: "mm", format: "a4", compress: true });
    let familia = "helvetica", latin1 = latin1Helvetica, extra = 0;
    if (fonte && fonte.normal && fonte.bold) {
      doc.addFileToVFS("FonteOAB-Regular.ttf", fonte.normal);
      doc.addFont("FonteOAB-Regular.ttf", "FonteOAB", "normal");
      doc.addFileToVFS("FonteOAB-Bold.ttf", fonte.bold);
      doc.addFont("FonteOAB-Bold.ttf", "FonteOAB", "bold");
      familia = "FonteOAB"; latin1 = oab; extra = 0.5; // a Calibri é visualmente menor que a Helvetica
    }
    const titulo = familia === "FonteOAB" ? "Simulado OAB – 1ª fase" : "Simulado OAB - 1ª fase";
    doc.setProperties({ title: titulo, subject: info.label, creator: "Simulados OAB" });
    let y = M;

    const color = (c) => doc.setTextColor(c[0], c[1], c[2]);
    const font = (style, size) => { doc.setFont(familia, style); doc.setFontSize(size + extra); };
    const room = (h) => { if (y + h > PAGE_H - M - 6) { doc.addPage(); y = M; return true; } return false; };
    const write = (text, x, width, style = "normal", size = BODY, c = INK, lh = LINE) => {
      font(style, size); color(c);
      for (const line of doc.splitTextToSize(latin1(text), width)) {
        room(lh);
        doc.text(line, x, y + lh * 0.75);
        y += lh;
      }
    };

    // Cabeçalho
    font("bold", 17); color(BRAND);
    doc.text(titulo, M, y + 6);
    y += 10;
    write(`${items.length} questões · ${info.label}`, M, W, "normal", 10.5, INK, 5);
    write(`Gerado em ${info.date} · questões oficiais do Exame de Ordem Unificado (OAB/FGV), sem as anuladas. Gabarito na última página.`,
      M, W, "normal", 8.5, MUTED, 4);
    y += 2;
    doc.setDrawColor(RULE[0], RULE[1], RULE[2]); doc.setLineWidth(0.3); doc.line(M, y, PAGE_W - M, y);
    y += 6;

    let subject = null;
    items.forEach((q, i) => {
      if (q.subjectName !== subject) {
        subject = q.subjectName;
        room(20);
        write(subject.toUpperCase(), M, W, "bold", 8.5, BRAND, 4.5);
        y += 1.5;
      }
      // cabeçalho da questão + ao menos 3 linhas juntos
      room(LINE * 4);
      font("bold", 10.5); color(INK);
      const head = `Questão ${i + 1}`;
      doc.text(head, M, y + LINE * 0.75);
      const hw = doc.getTextWidth(head);
      font("normal", 8); color(MUTED);
      doc.text(latin1(`  ${q.e}, questão ${q.n}${q.topicName ? " · " + q.topicName : ""}`), M + hw, y + LINE * 0.75);
      y += LINE + 1;
      for (const para of q.q.split("\n")) write(para, M, W);
      y += 1.5;
      q.a.forEach((alt, k) => {
        font("normal", BODY);
        const lines = doc.splitTextToSize(latin1(alt), W - 8);
        lines.forEach((line, j) => {
          room(LINE);
          if (j === 0) { font("bold", BODY); color(INK); doc.text(`(${LETTERS[k]})`, M, y + LINE * 0.75); }
          font("normal", BODY); color(INK);
          doc.text(line, M + 8, y + LINE * 0.75);
          y += LINE;
        });
        y += 0.8;
      });
      y += 5;
    });

    // Gabarito
    doc.addPage(); y = M;
    font("bold", 16); color(BRAND);
    doc.text("Gabarito", M, y + 6);
    y += 12;
    // Duas colunas numa página só (até 80 questões cabem com folga).
    const colW = W / 2, perCol = Math.ceil(items.length / 2), top = y;
    const rowH = Math.min(5, (PAGE_H - M - 8 - top) / perCol);
    items.forEach((q, i) => {
      const col = Math.floor(i / perCol);
      const yy = top + (i % perCol) * rowH;
      const x = M + col * colW;
      font("bold", 9.5); color(INK);
      doc.text(`${i + 1}.`, x + 7, yy + 3.6, { align: "right" });
      color(BRAND);
      doc.text(LETTERS[q.r], x + 10, yy + 3.6);
      font("normal", 8); color(MUTED);
      doc.text(doc.splitTextToSize(latin1(`${q.subjectShort} · ${q.e}, q. ${q.n}`), colW - 18)[0], x + 16, yy + 3.6);
    });

    // Rodapé com numeração
    const total = doc.getNumberOfPages();
    for (let p = 1; p <= total; p++) {
      doc.setPage(p);
      font("normal", 8); color(MUTED);
      doc.text(`Simulados OAB · página ${p} de ${total}`, PAGE_W / 2, PAGE_H - 10, { align: "center" });
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

  async function baixar(items, info, filename) {
    const [jsPDF, fonte] = await Promise.all([
      carregarJsPdf(),
      carregarFonte().catch((e) => { console.warn("Fonte OAB indisponível no PDF; usando Helvetica.", e); return null; }),
    ]);
    montar(jsPDF, items, info, fonte).save(filename);
  }

  const api = { montar, baixar, latin1: latin1Helvetica, oab };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.SimuladoPdf = api;
})(typeof window !== "undefined" ? window : globalThis);
