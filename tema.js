// Aplica a fonte e as cores salvas antes de desenhar a página. Carregado no <head>, sem async,
// em todas as páginas. Fica num arquivo (e não inline) para a CSP não precisar liberar scripts inline.
try {
  var t = JSON.parse(localStorage.getItem("oab.theme") || "null");
  var f = JSON.parse(localStorage.getItem("oab.font") || "null");
  if (t && t !== "auto") document.documentElement.dataset.theme = t;
  if (f && f !== "oab" && f !== "sistema") document.documentElement.dataset.font = f; // "sistema" saiu: cai na Fonte OAB
} catch (e) {}
