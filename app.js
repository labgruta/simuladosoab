"use strict";

// Matérias na ordem em que aparecem na prova. w = questões por prova no formato atual.
const SUBJECTS = [
  { id: "etica", name: "Ética Profissional (Estatuto e Código de Ética)", short: "Ética", w: 8, tier: 1 },
  { id: "civil", name: "Direito Civil", short: "Civil", w: 6, tier: 1 },
  { id: "proc_civil", name: "Processo Civil", short: "Proc. Civil", w: 6, tier: 1 },
  { id: "constitucional", name: "Direito Constitucional", short: "Constitucional", w: 6, tier: 1 },
  { id: "penal", name: "Direito Penal", short: "Penal", w: 6, tier: 1 },
  { id: "proc_penal", name: "Processo Penal", short: "Proc. Penal", w: 6, tier: 1 },
  { id: "administrativo", name: "Direito Administrativo", short: "Administrativo", w: 5, tier: 2 },
  { id: "trabalho", name: "Direito do Trabalho", short: "Trabalho", w: 5, tier: 2 },
  { id: "proc_trabalho", name: "Processo do Trabalho", short: "Proc. Trabalho", w: 5, tier: 2 },
  { id: "tributario", name: "Direito Tributário", short: "Tributário", w: 5, tier: 2 },
  { id: "empresarial", name: "Direito Empresarial", short: "Empresarial", w: 4, tier: 2 },
  { id: "dh", name: "Direitos Humanos", short: "Direitos Humanos", w: 2, tier: 3 },
  { id: "internacional", name: "Direito Internacional", short: "Internacional", w: 2, tier: 3 },
  { id: "eca", name: "Estatuto da Criança e do Adolescente", short: "ECA", w: 2, tier: 3 },
  { id: "ambiental", name: "Direito Ambiental", short: "Ambiental", w: 2, tier: 3 },
  { id: "consumidor", name: "Direito do Consumidor", short: "Consumidor", w: 2, tier: 3 },
  { id: "filosofia", name: "Filosofia do Direito", short: "Filosofia", w: 2, tier: 3 },
  { id: "previdenciario", name: "Direito Previdenciário", short: "Previdenciário", w: 2, tier: 3 },
  { id: "financeiro", name: "Direito Financeiro", short: "Financeiro", w: 2, tier: 3 },
  { id: "eleitoral", name: "Direito Eleitoral", short: "Eleitoral", w: 2, tier: 3 },
];
const BY_ID = Object.fromEntries(SUBJECTS.map((s) => [s.id, s]));
const ORDER = Object.fromEntries(SUBJECTS.map((s, i) => [s.id, i]));
const TIER_LABEL = { 1: "Mais recorrentes", 2: "Recorrência média", 3: "Menos recorrentes" };
const PRESETS = {
  todas: { label: "Todas as matérias", ids: SUBJECTS.map((s) => s.id) },
  etica: { label: "Estatuto da OAB e Código de Ética", ids: ["etica"] },
  t1: { label: "Mais recorrentes", ids: SUBJECTS.filter((s) => s.tier === 1).map((s) => s.id) },
  t2: { label: "Recorrência média", ids: SUBJECTS.filter((s) => s.tier === 2).map((s) => s.id) },
  t3: { label: "Menos recorrentes", ids: SUBJECTS.filter((s) => s.tier === 3).map((s) => s.id) },
};
const MAX_MANUAL = 3;
const SEC_PER_Q = 225; // 5h / 80 questões
const LETTERS = "ABCD";
const RECENT_MAX = 400; // questões sorteadas recentemente, evitadas nos próximos sorteios

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

// ---------- armazenamento local (tolerante a falhas) ----------
const store = {
  get(key, fallback) {
    try { const v = localStorage.getItem(key); return v == null ? fallback : JSON.parse(v); }
    catch { return fallback; }
  },
  set(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* sem armazenamento */ }
  },
  del(key) { try { localStorage.removeItem(key); } catch { /* idem */ } },
};

// ---------- estado ----------
let meta = { counts: {}, total: 0, exams: 0 };
const cache = {};
const sel = { ids: new Set(), preset: null };
let session = null;
let tick = null;

// ---------- utilidades ----------
function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}
function examOrdinal(id) {
  const ex = id.slice(0, id.lastIndexOf("-"));
  if (ex === "2010.2") return 2;
  if (ex === "2010.3") return 3;
  return parseInt(ex, 10);
}
function fmtTime(sec) {
  sec = Math.max(0, Math.round(sec));
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = sec % 60;
  const mm = String(m).padStart(2, "0"), ss = String(s).padStart(2, "0");
  return h ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}
function toast(msg) {
  const t = $("#toast");
  t.textContent = msg; t.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { t.hidden = true; }, 2600);
}
function show(view) {
  for (const v of ["setup", "quiz", "result"]) $(`#view-${v}`).hidden = v !== view;
  window.scrollTo({ top: 0 });
}
async function loadSubject(id) {
  if (!cache[id]) {
    const r = await fetch(`q-${id}.json`);
    if (!r.ok) throw new Error(`Falha ao carregar ${id}`);
    cache[id] = await r.json();
  }
  return cache[id];
}

// ---------- tema ----------
// Fontes embarcadas (fonts/) e esquemas de cor (style.css). "oab" e "auto" são o padrão.
const FONTS = [
  { id: "oab", name: "Fonte OAB", note: "fonte das provas", family: '"Fonte OAB", Calibri, sans-serif' },
  { id: "iawriter", name: "iA Writer Duo", family: '"iA Writer Duo S", monospace' },
  { id: "atkinson", name: "Atkinson Hyperlegible", family: '"Atkinson Hyperlegible", sans-serif' },
  { id: "lexend", name: "Lexend", family: '"Lexend", sans-serif' },
  { id: "literata", name: "Literata", family: '"Literata", serif' },
  { id: "lora", name: "Lora", family: '"Lora", serif' },
];
const THEMES = [
  { id: "auto", name: "Automático", bg: "linear-gradient(135deg, #f6f4ef 50%, #151515 50%)", ink: "#8a8a8a" },
  { id: "light", name: "Claro", bg: "#f6f4ef", ink: "#1b2330" },
  { id: "dark", name: "Escuro", bg: "#151515", ink: "#ebebeb" },
  { id: "sepia", name: "Sépia", bg: "#f3ead7", ink: "#3d2f1f" },
  { id: "papel", name: "Papel branco", bg: "#ffffff", ink: "#111111" },
  { id: "verde", name: "Verde suave", bg: "#e7efe2", ink: "#1d2b1a" },
  { id: "noite", name: "Azul-noite", bg: "#0e1726", ink: "#dbe5f3" },
  { id: "contraste", name: "Alto contraste", bg: "#000000", ink: "#ffffff" },
];
function currentFont() { return document.documentElement.dataset.font || "oab"; }
function currentTheme() { return document.documentElement.dataset.theme || "auto"; }
function setFont(id) {
  if (id === "oab") delete document.documentElement.dataset.font;
  else document.documentElement.dataset.font = id;
  store.set("oab.font", id);
  paintAppearance();
}
function setTheme(id) {
  if (id === "auto") delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = id;
  store.set("oab.theme", id);
  paintAppearance();
}
function paintAppearance() {
  const f = currentFont(), t = currentTheme();
  for (const b of $$(".ap-font")) b.setAttribute("aria-checked", String(b.dataset.id === f));
  for (const b of $$(".ap-color")) b.setAttribute("aria-checked", String(b.dataset.id === t));
  $("#apCur").textContent = `${FONTS.find((x) => x.id === f).name} · ${THEMES.find((x) => x.id === t).name}`;
}
function renderAppearanceOptions(fbox, cbox) {
  for (const f of FONTS) {
    const b = document.createElement("button");
    b.type = "button"; b.className = "ap-font"; b.dataset.id = f.id; b.setAttribute("role", "radio");
    b.innerHTML = `<span class="aa">Aa Çç</span><span class="nm"></span>`;
    b.querySelector(".aa").style.fontFamily = f.family; // a amostra só baixa a fonte quando aparece na tela
    b.querySelector(".nm").textContent = f.name;
    if (f.note) {
      const nt = document.createElement("span");
      nt.className = "nt"; nt.textContent = f.note;
      b.appendChild(nt);
    }
    b.addEventListener("click", () => setFont(f.id));
    fbox.appendChild(b);
  }
  for (const t of THEMES) {
    const b = document.createElement("button");
    b.type = "button"; b.className = "ap-color"; b.dataset.id = t.id; b.setAttribute("role", "radio");
    b.innerHTML = `<span class="sw">Aa</span><span class="nm"></span>`;
    const sw = b.querySelector(".sw");
    sw.style.background = t.bg; sw.style.color = t.ink;
    b.querySelector(".nm").textContent = t.name;
    b.addEventListener("click", () => setTheme(t.id));
    cbox.appendChild(b);
  }
}
// Menu de formatação do cabeçalho: disponível em todas as telas, inclusive durante o simulado.
function toggleFmtMenu(open) {
  const menu = $("#fmtMenu"), btn = $("#fmtBtn");
  const show = open ?? menu.hidden;
  menu.hidden = !show;
  btn.setAttribute("aria-expanded", String(show));
  if (show) (menu.querySelector('[aria-checked="true"]') || menu.querySelector("button"))?.focus();
}
function initAppearance() {
  renderAppearanceOptions($("#apFonts"), $("#apColors"));
  renderAppearanceOptions($("#fmtMenu .ap-fonts"), $("#fmtMenu .ap-colors"));
  $("#fmtBtn").addEventListener("click", (e) => { e.stopPropagation(); toggleFmtMenu(); });
  document.addEventListener("click", (e) => {
    if (!$("#fmtMenu").hidden && !e.target.closest(".fmt")) toggleFmtMenu(false);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !$("#fmtMenu").hidden) { toggleFmtMenu(false); $("#fmtBtn").focus(); }
  });
  paintAppearance();
}

// ---------- PDF: diagramação ----------
const PDF_PADRAO = { modo: "prova", colunas: 2, tamanho: 10 };
function pdfLayout() { return { ...PDF_PADRAO, ...store.get("oab.pdf", {}) }; }
function paintPdfOptions() {
  const l = pdfLayout();
  const radio = $(`input[name=pdfModo][value=${l.modo}]`);
  if (radio) radio.checked = true;
  $("#pdfCols").value = String(l.colunas);
  $("#pdfSize").value = String(l.tamanho);
  $("#pdfPers").hidden = l.modo !== "personalizado";
  $("#pdfResumo").textContent = l.modo === "personalizado"
    ? `personalizado, ${l.colunas} coluna${l.colunas > 1 ? "s" : ""}, letra ${l.tamanho}, Fonte OAB, preto no branco`
    : "igual à prova da OAB, Fonte OAB, preto no branco";
}
function initPdfOptions() {
  const salvar = () => {
    store.set("oab.pdf", {
      modo: $("input[name=pdfModo]:checked").value,
      colunas: parseInt($("#pdfCols").value, 10),
      tamanho: parseInt($("#pdfSize").value, 10),
    });
    paintPdfOptions();
  };
  for (const el of [...$$("input[name=pdfModo]"), $("#pdfCols"), $("#pdfSize")]) el.addEventListener("change", salvar);
  $("#pdfInfo").addEventListener("click", () => {
    const ap = $("#appearance");
    ap.open = true;
    $("#pdfOpcoes").scrollIntoView({ behavior: "smooth", block: "center" });
  });
  paintPdfOptions();
}

// ---------- configuração ----------
function renderSubjects() {
  const box = $("#subjects");
  box.innerHTML = "";
  for (const tier of [1, 2, 3]) {
    const wrap = document.createElement("div");
    const h = document.createElement("p");
    h.className = "tier-h"; h.textContent = TIER_LABEL[tier];
    const chips = document.createElement("div");
    chips.className = "chips";
    for (const s of SUBJECTS.filter((x) => x.tier === tier)) {
      const b = document.createElement("button");
      b.type = "button"; b.className = "chip"; b.dataset.id = s.id;
      b.setAttribute("aria-pressed", "false");
      b.title = s.name;
      b.innerHTML = `<span></span><span class="n"></span>`;
      b.firstChild.textContent = s.short;
      b.lastChild.textContent = meta.counts[s.id] ?? "";
      b.addEventListener("click", () => toggleSubject(s.id));
      chips.appendChild(b);
    }
    wrap.append(h, chips);
    box.appendChild(wrap);
  }
}
function toggleSubject(id) {
  if (sel.preset) { sel.ids.clear(); sel.preset = null; }
  if (sel.ids.has(id)) sel.ids.delete(id);
  else if (sel.ids.size >= MAX_MANUAL) { $("#limitMsg").hidden = false; return; }
  else sel.ids.add(id);
  $("#limitMsg").hidden = true;
  syncSelection();
}
function applyPreset(key) {
  $("#limitMsg").hidden = true;
  if (sel.preset === key) { sel.preset = null; sel.ids.clear(); }
  else {
    sel.preset = key; sel.ids = new Set(PRESETS[key].ids);
    if (key === "todas") $("#qty").value = "80";
  }
  syncSelection();
}
function syncSelection() {
  for (const b of $$(".chip")) b.setAttribute("aria-pressed", String(sel.ids.has(b.dataset.id)));
  for (const b of $$(".preset")) b.classList.toggle("on", b.dataset.preset === sel.preset);
  const pill = $("#selCount");
  if (sel.preset) { pill.textContent = `Grupo: ${sel.ids.size} matéria${sel.ids.size > 1 ? "s" : ""}`; pill.classList.add("group"); }
  else { pill.textContent = `${sel.ids.size} de ${MAX_MANUAL}`; pill.classList.remove("group"); }
  updatePlan();
}
function settings() {
  return {
    qty: parseInt($("#qty").value, 10),
    period: $("#period").value,
    mode: $("input[name=mode]:checked").value,
    timed: $("#timed").checked,
    fresh: $("#fresh").checked,
    rec: $("#rec").checked,
  };
}
// Distribui N questões entre as matérias proporcionalmente ao peso na prova (maiores restos).
function allocate(ids, n, avail) {
  const res = Object.fromEntries(ids.map((id) => [id, 0]));
  let left = n;
  while (left > 0) {
    const pool = ids.filter((id) => res[id] < avail[id]);
    if (!pool.length) break;
    const wsum = pool.reduce((a, id) => a + BY_ID[id].w, 0);
    const raw = pool.map((id) => ({ id, x: (left * BY_ID[id].w) / wsum }));
    for (const r of raw) {
      const k = Math.min(Math.floor(r.x), avail[r.id] - res[r.id]);
      res[r.id] += k; left -= k; r.rem = r.x - Math.floor(r.x);
    }
    raw.sort((a, b) => b.rem - a.rem || BY_ID[b.id].w - BY_ID[a.id].w);
    for (const r of raw) {
      if (left <= 0) break;
      if (res[r.id] < avail[r.id]) { res[r.id]++; left--; }
    }
  }
  return res;
}
function updatePlan() {
  const ids = [...sel.ids].sort((a, b) => ORDER[a] - ORDER[b]);
  const btn = $("#startBtn");
  if (!ids.length) {
    $("#planInfo").textContent = "Selecione ao menos uma matéria.";
    btn.disabled = true; $("#pdfBtn").disabled = true; renderRecList([], false);
    return;
  }
  const st = settings();
  const avail = Object.fromEntries(ids.map((id) => [id, st.rec ? recCount(id) : meta.counts[id] || 0]));
  const plan = allocate(ids, st.qty, avail);
  const total = Object.values(plan).reduce((a, b) => a + b, 0);
  const parts = ids.filter((id) => plan[id]).map((id) => `${BY_ID[id].short} ${plan[id]}`);
  $("#planInfo").textContent = `${total} questões: ${parts.join(" · ")}`
    + (st.rec ? " · só temas recorrentes" : "")
    + (st.timed ? ` · tempo: ${fmtTime(total * SEC_PER_Q)}` : "");
  btn.disabled = total === 0;
  $("#pdfBtn").disabled = total === 0;
  renderRecList(ids, st.rec);
}

// ---------- temas ----------
function topics(id) { return (meta.temas && meta.temas[id]) || []; }
function recTopics(id) { return new Set(topics(id).filter((t) => t.rec).map((t) => t.id)); }
function recCount(id) { return topics(id).filter((t) => t.rec).reduce((a, t) => a + t.n, 0); }
function topicName(sid, tid) {
  const t = topics(sid).find((x) => x.id === tid);
  return t && tid !== "outros" ? t.nome : "";
}
function renderRecList(ids, on) {
  const box = $("#recBox");
  box.hidden = !on || !ids.length;
  if (box.hidden) return;
  const list = $("#recList");
  list.innerHTML = "";
  for (const id of ids) {
    const p = document.createElement("p");
    const b = document.createElement("strong");
    b.textContent = `${BY_ID[id].short}: `;
    p.append(b, document.createTextNode(topics(id).filter((t) => t.rec).map((t) => `${t.nome} (${t.n})`).join(" · ")));
    list.appendChild(p);
  }
}

// ---------- montagem do simulado ----------
// Sorteia as questões conforme a seleção atual. Cada chamada gera um sorteio novo: as questões
// dos sorteios recentes (e, se marcado, as já respondidas) só entram se faltar questão.
async function draw() {
  const st = settings();
  const ids = [...sel.ids].sort((a, b) => ORDER[a] - ORDER[b]);
  const minEx = st.period === "all" ? 0 : parseInt(st.period, 10);
  const seen = st.fresh ? new Set(store.get("oab.seen", [])) : new Set();
  const recent = new Set(store.get("oab.recent", []));
  const pools = {};
  for (const id of ids) {
    const all = await loadSubject(id);
    const rec = st.rec ? recTopics(id) : null;
    pools[id] = all.filter((q) => examOrdinal(q.id) >= minEx && (!rec || rec.has(q.t)));
  }
  const avail = Object.fromEntries(ids.map((id) => [id, pools[id].length]));
  const plan = allocate(ids, st.qty, avail);
  const items = [];
  for (const id of ids) {
    const tier = (q) => (seen.has(q.id) ? 2 : recent.has(q.id) ? 1 : 0);
    const list = shuffle(pools[id].slice()).sort((a, b) => tier(a) - tier(b));
    for (const q of list.slice(0, plan[id])) items.push({ ...q, s: id });
  }
  if (!items.length) throw new Error("Não há questões para esse filtro.");
  const drawn = items.map((q) => q.id);
  store.set("oab.recent", drawn.concat([...recent].filter((x) => !drawn.includes(x))).slice(0, RECENT_MAX));
  let label = sel.preset ? PRESETS[sel.preset].label : ids.map((id) => BY_ID[id].short).join(", ");
  if (st.rec) label += " (temas recorrentes)";
  const cfg = { ids, preset: sel.preset, st };
  return { items, label, st, cfg };
}
async function buildSession() {
  const { items, label, st, cfg } = await draw();
  const s = newSession(items, st.mode, st.timed, label);
  s.cfg = cfg;
  return s;
}
function applyConfig(cfg) {
  sel.ids = new Set(cfg.ids); sel.preset = cfg.preset;
  $("#qty").value = String(cfg.st.qty);
  $("#period").value = cfg.st.period;
  $(`input[name=mode][value=${cfg.st.mode}]`).checked = true;
  $("#timed").checked = cfg.st.timed;
  $("#fresh").checked = cfg.st.fresh;
  $("#rec").checked = !!cfg.st.rec;
  syncSelection();
}
async function startNew() {
  const btn = $("#startBtn");
  btn.disabled = true; btn.textContent = "Sorteando…";
  try {
    session = await buildSession();
    if (session.items.length < settings().qty) toast(`Só havia ${session.items.length} questões disponíveis com esse filtro.`);
    saveSession();
    startQuiz();
  } catch (e) {
    toast(e.message || "Erro ao montar o simulado.");
  } finally {
    btn.textContent = "Sortear simulado"; updatePlan();
  }
}
async function downloadPdf() {
  const btn = $("#pdfBtn");
  btn.disabled = true; btn.textContent = "Gerando PDF…";
  try {
    const { items, label } = await draw();
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    const stamp = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}`;
    const rich = items.map((q) => ({ ...q, subjectName: BY_ID[q.s].name, subjectShort: BY_ID[q.s].short, topicName: topicName(q.s, q.t) }));
    await window.SimuladoPdf.baixar(rich, { label, date: now.toLocaleDateString("pt-BR") }, `simulado-oab-${stamp}.pdf`, pdfLayout());
    toast(`PDF com ${items.length} questões baixado. Clique de novo para sortear outra prova.`);
  } catch (e) {
    toast(e.message || "Erro ao gerar o PDF.");
  } finally {
    btn.textContent = "Baixar prova em PDF"; updatePlan();
  }
}
function newSession(items, mode, timed, label) {
  return {
    label, mode, timed,
    items,
    answers: items.map(() => null),
    flags: items.map(() => false),
    idx: 0,
    elapsed: 0,
    limit: timed ? items.length * SEC_PER_Q : 0,
    created: Date.now(),
  };
}
function saveSession() { if (session) store.set("oab.session", session); }

// ---------- prova ----------
function startQuiz() {
  show("quiz");
  $("#grid").hidden = true;
  $("#gridBtn").setAttribute("aria-expanded", "false");
  renderGrid();
  renderQuestion();
  startTimer();
}
function startTimer() {
  clearInterval(tick);
  const el = $("#timer");
  el.hidden = false;
  const paint = () => {
    if (session.limit) {
      const left = session.limit - session.elapsed;
      el.textContent = `⏱ ${fmtTime(left)}`;
      el.classList.toggle("low", left <= 300);
    } else {
      el.textContent = `⏱ ${fmtTime(session.elapsed)}`;
      el.classList.remove("low");
    }
  };
  paint();
  tick = setInterval(() => {
    if (document.hidden) return;
    session.elapsed++;
    paint();
    if (session.elapsed % 10 === 0) saveSession();
    if (session.limit && session.elapsed >= session.limit) {
      toast("Tempo esgotado. Simulado finalizado.");
      finish();
    }
  }, 1000);
}
function stopTimer() { clearInterval(tick); tick = null; $("#timer").hidden = true; }

function renderGrid() {
  const g = $("#grid");
  g.innerHTML = "";
  session.items.forEach((_, i) => {
    const b = document.createElement("button");
    b.type = "button"; b.textContent = i + 1;
    b.addEventListener("click", () => { session.idx = i; renderQuestion(); });
    g.appendChild(b);
  });
  paintGrid();
}
function paintGrid() {
  const btns = $("#grid").children;
  session.items.forEach((q, i) => {
    const b = btns[i]; if (!b) return;
    const a = session.answers[i];
    b.className = "";
    if (a != null) {
      if (session.mode === "study") b.classList.add(a === q.r ? "right" : "wrong");
      else b.classList.add("ans");
    }
    if (session.flags[i]) b.classList.add("flag");
    if (i === session.idx) b.classList.add("cur");
    b.setAttribute("aria-label", `Questão ${i + 1}${a != null ? ", respondida" : ""}${session.flags[i] ? ", marcada" : ""}`);
  });
  const done = session.answers.filter((a) => a != null).length;
  $("#progBar").style.width = `${(done / session.items.length) * 100}%`;
  $("#progText").textContent = `Questão ${session.idx + 1} de ${session.items.length} · ${done} respondida${done === 1 ? "" : "s"}`;
}
function renderQuestion() {
  const i = session.idx, q = session.items[i], a = session.answers[i];
  const locked = session.mode === "study" && a != null;
  $("#qSubject").textContent = BY_ID[q.s].name;
  const tn = topicName(q.s, q.t);
  $("#qSource").textContent = `${q.e} · questão ${q.n}` + (tn ? ` · ${tn}` : "");
  $("#qText").textContent = q.q;
  const box = $("#alts");
  box.innerHTML = "";
  q.a.forEach((txt, k) => {
    const b = document.createElement("button");
    b.type = "button"; b.className = "alt";
    b.setAttribute("role", "radio");
    b.setAttribute("aria-checked", String(a === k));
    b.innerHTML = `<span class="l"></span><span class="t"></span>`;
    b.querySelector(".l").textContent = LETTERS[k];
    b.querySelector(".t").textContent = txt;
    if (a === k) b.classList.add("chosen");
    if (locked) {
      b.disabled = true;
      if (k === q.r) b.classList.add("right");
      else if (k === a) b.classList.add("wrong");
    }
    b.addEventListener("click", () => choose(k));
    box.appendChild(b);
  });
  const fb = $("#feedback");
  if (locked) {
    fb.hidden = false;
    fb.className = `feedback ${a === q.r ? "ok" : "bad"}`;
    fb.textContent = a === q.r ? "Correta!" : `Incorreta. Resposta certa: ${LETTERS[q.r]}.`;
  } else fb.hidden = true;
  $("#prevBtn").disabled = i === 0;
  $("#nextBtn").textContent = i === session.items.length - 1 ? "Concluir" : "Próxima →";
  $("#flagBtn").textContent = session.flags[i] ? "★ Marcada" : "☆ Marcar";
  paintGrid();
}
function choose(k) {
  const i = session.idx;
  if (session.mode === "study" && session.answers[i] != null) return;
  session.answers[i] = session.answers[i] === k && session.mode === "exam" ? null : k;
  saveSession();
  renderQuestion();
}
function go(delta) {
  const n = session.idx + delta;
  if (n < 0) return;
  if (n >= session.items.length) { confirmFinish(); return; }
  session.idx = n;
  saveSession();
  renderQuestion();
  $("#qcard").scrollIntoView({ block: "start", behavior: "smooth" });
}
function confirmFinish() {
  const blank = session.answers.filter((a) => a == null).length;
  const msg = blank
    ? `Você deixou ${blank} questão${blank > 1 ? "ões" : ""} em branco. Finalizar mesmo assim?`
    : "Finalizar o simulado e ver o resultado?";
  if (confirm(msg)) finish();
}

// ---------- resultado ----------
function finish() {
  stopTimer();
  const s = session;
  const correct = s.items.reduce((acc, q, i) => acc + (s.answers[i] === q.r ? 1 : 0), 0);
  const seen = new Set(store.get("oab.seen", []));
  s.items.forEach((q, i) => { if (s.answers[i] != null) seen.add(q.id); });
  store.set("oab.seen", [...seen].slice(-6000));
  const hist = store.get("oab.history", []);
  hist.unshift({ t: Date.now(), label: s.label, n: s.items.length, c: correct, mode: s.mode, time: s.elapsed });
  store.set("oab.history", hist.slice(0, 30));
  store.del("oab.session");
  renderResult(s, correct);
  show("result");
}
function renderResult(s, correct) {
  const n = s.items.length, pct = Math.round((correct / n) * 100);
  const ring = $("#scoreRing");
  ring.style.setProperty("--p", pct);
  ring.style.setProperty("--ring", pct >= 50 ? "var(--ok)" : "var(--bad)");
  $("#scorePct").textContent = `${pct}%`;
  $("#scoreTitle").textContent = `${correct} de ${n} acertos`;
  const blank = s.answers.filter((a) => a == null).length;
  $("#scoreSub").textContent = `${s.label} · ${s.mode === "study" ? "modo estudo" : "modo prova"} · ${fmtTime(s.elapsed)}`
    + (blank ? ` · ${blank} em branco` : "");
  $("#scoreNote").textContent = pct >= 50
    ? "Acima da nota de corte da 1ª fase (50% de acertos, ou 40 de 80)."
    : "Abaixo da nota de corte da 1ª fase (50% de acertos, ou 40 de 80). Revise os erros abaixo.";

  const by = {};
  s.items.forEach((q, i) => {
    by[q.s] = by[q.s] || { n: 0, c: 0 };
    by[q.s].n++; if (s.answers[i] === q.r) by[q.s].c++;
  });
  const bars = $("#bySubject");
  bars.innerHTML = "";
  Object.keys(by).sort((a, b) => ORDER[a] - ORDER[b]).forEach((id) => {
    const r = by[id], p = Math.round((r.c / r.n) * 100);
    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML = `<span class="k"></span><div class="bar"><i></i></div><span class="v"></span>`;
    row.querySelector(".k").textContent = BY_ID[id].short;
    row.querySelector("i").style.width = `${p}%`;
    row.querySelector("i").style.background = p >= 50 ? "var(--ok)" : "var(--bad)";
    row.querySelector(".v").textContent = `${r.c}/${r.n} · ${p}%`;
    bars.appendChild(row);
  });

  const wrong = s.items.filter((q, i) => s.answers[i] !== q.r);
  $("#retryWrong").hidden = wrong.length === 0;
  $("#retryWrong").onclick = () => {
    session = newSession(wrong.map((q) => ({ ...q })), s.mode, s.timed, `Revisão: ${s.label}`);
    session.cfg = s.cfg;
    saveSession();
    startQuiz();
  };
  $("#againBtn").onclick = () => {
    if (s.cfg) { applyConfig(s.cfg); startNew(); } else goHome();
  };
  renderReview(s);
  $("#onlyWrong").onchange = () => renderReview(s);
}
function renderReview(s) {
  const only = $("#onlyWrong").checked;
  const box = $("#review");
  box.innerHTML = "";
  s.items.forEach((q, i) => {
    const a = s.answers[i];
    const status = a == null ? "blank" : a === q.r ? "ok" : "bad";
    if (only && status === "ok") return;
    const d = document.createElement("details");
    d.className = "rv";
    const sm = document.createElement("summary");
    const st = document.createElement("span");
    st.className = `st ${status}`;
    st.textContent = status === "ok" ? `${i + 1} ✓` : status === "bad" ? `${i + 1} ✗` : `${i + 1} —`;
    const sum = document.createElement("span");
    sum.className = "sum";
    sum.textContent = `${BY_ID[q.s].short}: ${q.q}`;
    sm.append(st, sum);
    const body = document.createElement("div");
    body.className = "body";
    const src = document.createElement("p");
    src.className = "muted small";
    const tn = topicName(q.s, q.t);
    src.textContent = `${q.e} · questão ${q.n}${tn ? ` · ${tn}` : ""} · sua resposta: ${a == null ? "em branco" : LETTERS[a]} · gabarito: ${LETTERS[q.r]}`;
    const txt = document.createElement("div");
    txt.className = "qtext"; txt.textContent = q.q;
    const alts = document.createElement("div");
    alts.className = "alts";
    q.a.forEach((t, k) => {
      const el = document.createElement("div");
      el.className = "alt" + (k === q.r ? " right" : k === a ? " wrong" : "");
      el.innerHTML = `<span class="l"></span><span class="t"></span>`;
      el.querySelector(".l").textContent = LETTERS[k];
      el.querySelector(".t").textContent = t;
      alts.appendChild(el);
    });
    body.append(src, txt, alts);
    d.append(sm, body);
    box.appendChild(d);
  });
  if (!box.children.length) box.innerHTML = `<p class="muted">Nenhum erro. Parabéns!</p>`;
}

// ---------- tela inicial ----------
function renderHistory() {
  const hist = store.get("oab.history", []);
  $("#historyBox").hidden = hist.length === 0;
  const ul = $("#history");
  ul.innerHTML = "";
  for (const h of hist.slice(0, 10)) {
    const li = document.createElement("li");
    const d = new Date(h.t);
    const left = document.createElement("span");
    left.textContent = `${d.toLocaleDateString("pt-BR")} · ${h.label}`;
    const right = document.createElement("span");
    right.className = "sc";
    right.textContent = `${h.c}/${h.n} (${Math.round((h.c / h.n) * 100)}%)`;
    li.append(left, right);
    ul.appendChild(li);
  }
}
function renderResume() {
  const saved = store.get("oab.session", null);
  const box = $("#resume");
  if (!saved || !saved.items || !saved.items.length) { box.hidden = true; return; }
  const done = saved.answers.filter((a) => a != null).length;
  $("#resumeInfo").textContent = `${saved.label} · ${done} de ${saved.items.length} respondidas`;
  box.hidden = false;
}
function goHome() {
  if (!$("#view-quiz").hidden && session) {
    saveSession();
    stopTimer();
  }
  renderResume();
  renderHistory();
  show("setup");
}

// ---------- inicialização ----------
async function init() {
  initAppearance();
  initPdfOptions();
  try {
    const r = await fetch("meta.json");
    meta = await r.json();
    $("#introStats").textContent =
      `${meta.total.toLocaleString("pt-BR")} questões oficiais de ${meta.exams} provas (Exame 2010.2 ao 47º), sem as anuladas.`;
  } catch {
    $("#introStats").textContent = "Não foi possível carregar o banco de questões. Recarregue a página.";
  }
  renderSubjects();
  syncSelection();
  renderResume();
  renderHistory();

  for (const b of $$(".preset")) b.addEventListener("click", () => applyPreset(b.dataset.preset));
  for (const el of ["#qty", "#period", "#timed"]) $(el).addEventListener("change", updatePlan);
  for (const el of ["#rec", "#fresh"]) $(el).addEventListener("change", updatePlan);
  $("#startBtn").addEventListener("click", startNew);
  $("#pdfBtn").addEventListener("click", downloadPdf);
  $("#resumeBtn").addEventListener("click", () => {
    session = store.get("oab.session", null);
    if (session) startQuiz();
  });
  $("#discardBtn").addEventListener("click", () => { store.del("oab.session"); renderResume(); });
  $("#clearHist").addEventListener("click", () => {
    if (confirm("Apagar o histórico e a lista de questões já respondidas?")) {
      store.del("oab.history"); store.del("oab.seen"); renderHistory();
    }
  });
  $("#homeBtn").addEventListener("click", goHome);
  $("#newBtn").addEventListener("click", goHome);
  $("#prevBtn").addEventListener("click", () => go(-1));
  $("#nextBtn").addEventListener("click", () => go(1));
  $("#finishBtn").addEventListener("click", confirmFinish);
  $("#flagBtn").addEventListener("click", () => {
    session.flags[session.idx] = !session.flags[session.idx];
    saveSession(); renderQuestion();
  });
  $("#gridBtn").addEventListener("click", () => {
    const g = $("#grid"); g.hidden = !g.hidden;
    $("#gridBtn").setAttribute("aria-expanded", String(!g.hidden));
    $("#gridBtn").textContent = g.hidden ? "Ver todas" : "Ocultar";
  });
  document.addEventListener("keydown", (e) => {
    if ($("#view-quiz").hidden || !$("#fmtMenu").hidden || e.metaKey || e.ctrlKey || e.altKey) return;
    if (/^(INPUT|SELECT|TEXTAREA)$/.test(document.activeElement?.tagName || "")) return;
    const k = e.key.toUpperCase();
    if (LETTERS.includes(k) && k.length === 1) { choose(LETTERS.indexOf(k)); e.preventDefault(); }
    else if (e.key === "ArrowRight") go(1);
    else if (e.key === "ArrowLeft") go(-1);
  });
  window.addEventListener("beforeunload", saveSession);
}
init();
