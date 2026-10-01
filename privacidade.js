"use strict";
// Botão "Apagar meus dados": remove do localStorage tudo o que o app guardou (chaves "oab.*").
// Sem JavaScript o botão fica oculto, e a página explica como apagar pelo navegador.
(function () {
  const btn = document.getElementById("apagarBtn");
  const msg = document.getElementById("apagarMsg");

  function chaves() {
    try { return Object.keys(localStorage).filter((k) => k.startsWith("oab.")); }
    catch { return null; }
  }

  btn.hidden = false;
  btn.addEventListener("click", () => {
    const ks = chaves();
    if (ks === null) {
      msg.textContent = "Este navegador não permite o armazenamento local, então nada foi guardado.";
      return;
    }
    if (!ks.length) {
      msg.textContent = "Não há dados do Simulados OAB guardados neste navegador.";
      return;
    }
    if (!confirm("Apagar o histórico, o simulado em andamento, as questões já vistas e as preferências de aparência e de PDF guardados neste navegador? Não será possível recuperá-los.")) return;
    for (const k of ks) { try { localStorage.removeItem(k); } catch { /* segue com as demais */ } }
    delete document.documentElement.dataset.theme;
    delete document.documentElement.dataset.font;
    msg.textContent = "Pronto: os dados do Simulados OAB foram apagados deste navegador.";
  });
})();
