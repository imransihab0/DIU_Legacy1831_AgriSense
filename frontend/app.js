const $ = (id) => document.getElementById(id);

let sessionId = localStorage.getItem("agrisense_session");
if (!sessionId) {
  sessionId = "farm-" + Math.random().toString(36).slice(2, 10);
  localStorage.setItem("agrisense_session", sessionId);
}

fetch("/api/health").then(r => r.json()).then(h => {
  $("health").textContent = `KB ${h.kb_chunks} chunks`;
}).catch(() => { $("health").textContent = "backend offline"; });

// Live model switcher
fetch("/api/model").then(r => r.json()).then(m => {
  const sel = $("modelSelect");
  const groups = [["OpenAI", m.openai_models]];
  if (m.anthropic_key_set) groups.push(["Anthropic", m.anthropic_models]);
  for (const [name, models] of groups) {
    const og = document.createElement("optgroup");
    og.label = name;
    for (const opt of models) {
      const o = document.createElement("option");
      o.value = opt.id;
      o.textContent = opt.label;
      if (opt.id === m.current_model) o.selected = true;
      og.appendChild(o);
    }
    sel.appendChild(og);
  }
  sel.addEventListener("change", async () => {
    const r = await fetch("/api/model", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: sel.value }),
    });
    const res = await r.json();
    if (res.ok) addTrace("status", `⚙ model switched to ${res.current_model}`);
  });
});

// --- Proactive weather alerts: poll without a chat turn and show a banner ---
const SEV_ICON = { high: "🔴", medium: "🟠", info: "🔵" };
async function pollAlerts() {
  try {
    const r = await fetch(`/api/alerts/${sessionId}`);
    const data = await r.json();
    const banner = $("alertBanner");
    if (data.status !== "ok" || !data.alerts || !data.alerts.length) {
      banner.classList.add("hidden");
      banner.innerHTML = "";
      return;
    }
    const rows = data.alerts.map(a =>
      `<div class="alert-row ${a.severity}">${SEV_ICON[a.severity] || "⚠️"} `
      + `<b>${escapeHtml(a.message)}</b> — ${escapeHtml(a.suggestion)}</div>`
    ).join("");
    banner.innerHTML = `<div class="alert-title">⛅ Weather alerts for your ${escapeHtml(data.crop || "plan")} `
      + `<span class="alert-meta">live · ${data.alert_count} active</span></div>${rows}`;
    banner.classList.remove("hidden");
  } catch (_) { /* backend offline — leave banner as is */ }
}
pollAlerts();
setInterval(pollAlerts, 5 * 60 * 1000); // re-check every 5 min, no user action needed

function addMessage(role, html) {
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.innerHTML = html;
  $("messages").appendChild(div);
  $("messages").scrollTop = $("messages").scrollHeight;
  return div;
}

function addTrace(kind, title, payload) {
  const div = document.createElement("div");
  div.className = "trace-item " + kind;
  const body = payload !== undefined
    ? `<details ${kind === "tool_call" ? "open" : ""}><summary>${title}</summary><pre>${escapeHtml(JSON.stringify(payload, null, 2))}</pre></details>`
    : `<div class="trace-line">${title}</div>`;
  div.innerHTML = body;
  $("trace").appendChild(div);
  $("trace").scrollTop = $("trace").scrollHeight;
}

function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

async function send(message) {
  addMessage("user", escapeHtml(message));
  const thinking = addMessage("assistant pending", "<em>thinking & calling tools…</em>");
  $("sendBtn").disabled = true;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message }),
    });
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let nl;
      while ((nl = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, nl).trim();
        buf = buf.slice(nl + 1);
        if (!line) continue;
        handleEvent(JSON.parse(line), thinking);
      }
    }
  } catch (e) {
    thinking.innerHTML = `<span class="err">Error: ${escapeHtml(String(e))}</span>`;
  } finally {
    thinking.classList.remove("pending");
    $("sendBtn").disabled = false;
    $("input").focus();
    pollAlerts(); // a turn may have created/updated the plan — refresh the banner now
  }
}

function handleEvent(ev, thinkingEl) {
  if (ev.type === "status") {
    addTrace("status", "▶ " + ev.text);
  } else if (ev.type === "tool_call") {
    addTrace("tool_call", `📤 CALL ${ev.tool}`, ev.params);
    thinkingEl.innerHTML = `<em>calling <b>${ev.tool}</b>…</em>`;
  } else if (ev.type === "tool_result") {
    addTrace("tool_result", `📥 RESULT ${ev.tool} (${ev.ms} ms)`, ev.result);
  } else if (ev.type === "final") {
    renderAgentMessage(thinkingEl, ev.content || "");
    addTrace("status", "✔ turn complete");
  } else if (ev.type === "error") {
    thinkingEl.innerHTML = `<span class="err">${escapeHtml(ev.text)}</span>`;
    addTrace("error", "✖ " + ev.text);
  }
}

$("composer").addEventListener("submit", (e) => {
  e.preventDefault();
  const v = $("input").value.trim();
  if (!v) return;
  $("input").value = "";
  send(v);
});

$("resetBtn").addEventListener("click", async () => {
  await fetch(`/api/reset/${sessionId}`, { method: "POST" });
  localStorage.removeItem("agrisense_session");
  location.reload();
});

// ---- Agent message rendering: extract action tokens ----
const PAY_RE = /\[\[CONFIRM_PAY:([^\]|]+)\|([^\]|]+)\|([^\]]+)\]\]/g;
const TOKEN_RE = /\[\[(BUTTON|SHORTCUT|REMOVE_SHORTCUT):([^\]|]+)(?:\|([^\]]+))?\]\]/g;

function renderAgentMessage(el, content) {
  const buttons = [];
  let pay = null;
  let text = content.replace(PAY_RE, (_, amt, item, num) => {
    pay = { amt: amt.trim(), item: item.trim(), num: num.trim() };
    return "";
  });
  text = text.replace(TOKEN_RE, (_, kind, label, msg) => {
    if (kind === "SHORTCUT" && msg) addShortcut(label.trim(), msg.trim());
    else if (kind === "REMOVE_SHORTCUT") removeShortcutFuzzy(label.trim());
    else if (kind === "BUTTON" && msg) buttons.push({ label: label.trim(), msg: msg.trim() });
    return "";
  }).trim();

  el.innerHTML = marked.parse(text);

  if (buttons.length || pay) {
    const row = document.createElement("div");
    row.className = "inline-actions";
    for (const b of buttons) {
      const btn = document.createElement("button");
      const buy = /কিন|buy|🛒/i.test(b.label);
      btn.className = "chip inline " + (buy ? "buy" : "confirm");
      btn.textContent = b.label;
      btn.addEventListener("click", () => {
        if ($("sendBtn").disabled) return;
        if (buy && INPUT_CATALOG.length) { openOrderModal(); return; }  // open the order builder
        row.querySelectorAll("button").forEach((x) => (x.disabled = true));
        send(b.msg);
      });
      row.appendChild(btn);
    }
    if (pay) {
      const btn = document.createElement("button");
      btn.className = "chip inline confirm";
      btn.textContent = "✅ কনফার্ম করুন";
      btn.addEventListener("click", () => { if (!$("sendBtn").disabled) openPayModal(pay); });
      row.appendChild(btn);
    }
    el.appendChild(row);
  }
}

// ---- Order builder dialog (pick product -> quantity -> live total -> pay) ----
let INPUT_CATALOG = [];  // [{key, name, unit, price, cat}]
fetch("/api/inputs").then((r) => r.json()).then((d) => {
  const label = { fertilizers: "সার", seeds: "বীজ", pesticides: "কীটনাশক", livestock: "পশুখাদ্য/ঔষধ" };
  for (const [cat, items] of Object.entries(d.catalog || {}))
    for (const [key, it] of Object.entries(items))
      INPUT_CATALOG.push({ key, name: it.name, unit: it.unit, price: it.price, cat: label[cat] || cat });
}).catch(() => {});

const MAX_QTY = 999;            // per-item quantity cap
const MAX_ORDER_BDT = 100000;   // total order ceiling (like any real checkout)

function addOrderRow() {
  const row = document.createElement("div");
  row.className = "order-row";
  const sel = document.createElement("select");
  sel.innerHTML = INPUT_CATALOG
    .map((it, i) => `<option value="${i}">${it.cat} — ${escapeHtml(it.name)} (৳${it.price}/${escapeHtml(it.unit)})</option>`)
    .join("");
  const qty = document.createElement("input");
  qty.type = "number"; qty.min = "1"; qty.max = String(MAX_QTY); qty.step = "1"; qty.value = "1"; qty.className = "order-qty";
  const line = document.createElement("span"); line.className = "order-line";
  const rm = document.createElement("button");
  rm.type = "button"; rm.className = "order-rm"; rm.textContent = "✕";
  rm.onclick = () => { row.remove(); updateOrderTotal(); };
  sel.onchange = updateOrderTotal; qty.oninput = updateOrderTotal;
  row.append(sel, qty, line, rm);
  $("orderRows").appendChild(row);
  updateOrderTotal();
}

function updateOrderTotal() {
  let total = 0;
  $("orderRows").querySelectorAll(".order-row").forEach((row) => {
    const it = INPUT_CATALOG[+row.querySelector("select").value];
    const input = row.querySelector(".order-qty");
    let q = Math.floor(parseFloat(input.value)) || 0;   // floor handles scientific/decimal input
    q = Math.min(MAX_QTY, Math.max(0, q));               // clamp to [0, MAX_QTY]
    if (String(q) !== input.value && document.activeElement !== input) input.value = q; // correct absurd entries
    const lt = it ? it.price * q : 0;
    total += lt;
    row.querySelector(".order-line").textContent = `৳${lt}`;
  });
  $("orderTotal").textContent = total;
  const warn = $("orderWarn");
  if (total > MAX_ORDER_BDT) {
    warn.textContent = `⚠️ এক অর্ডারে সর্বোচ্চ ৳${MAX_ORDER_BDT.toLocaleString()} পর্যন্ত কেনা যাবে — পরিমাণ কমান।`;
    warn.classList.remove("hidden");
    $("orderConfirm").disabled = true;
  } else {
    warn.classList.add("hidden");
    $("orderConfirm").disabled = false;
  }
  return total;
}

function openOrderModal() {
  $("orderRows").innerHTML = "";
  addOrderRow();
  $("orderPhone").value = localStorage.getItem("agrisense_phone") || "";
  $("orderPhone").classList.remove("err");
  updateOrderTotal();
  $("orderModal").classList.remove("hidden");
}

$("orderAddRow").onclick = addOrderRow;
$("orderCancel").onclick = () => $("orderModal").classList.add("hidden");
$("orderConfirm").onclick = () => {
  const total = updateOrderTotal();
  const phone = $("orderPhone").value.replace(/\s/g, "");
  const items = [...$("orderRows").querySelectorAll(".order-row")].map((row) => {
    const it = INPUT_CATALOG[+row.querySelector("select").value];
    const q = Math.min(MAX_QTY, Math.max(1, Math.floor(parseFloat(row.querySelector(".order-qty").value)) || 1));
    return `${q} x ${it.name} (${it.unit})`;  // include the unit so "1 bag/50kg" is unambiguous (ASCII for SMS)
  });
  if (!total || total > MAX_ORDER_BDT) return;  // block empty or over-limit orders
  if (phone.replace(/\D/g, "").length < 11) { $("orderPhone").classList.add("err"); $("orderPhone").focus(); return; }
  localStorage.setItem("agrisense_phone", phone);
  $("orderModal").classList.add("hidden");
  openPayModal({ amt: String(total), item: items.join(" + "), num: phone });  // final confirm
};

// ---- Payment confirmation modal ----
function openPayModal(pay) {
  $("payDetails").innerHTML =
    `<div class="pay-row">পণ্য: <b>${escapeHtml(pay.item)}</b></div>` +
    `<div class="pay-row">মোবাইল নম্বর: <b>${escapeHtml(pay.num)}</b></div>` +
    `<div class="pay-row total">মোট কাটা হবে: <b>৳${escapeHtml(pay.amt)}</b></div>` +
    `<div class="pay-warn">আপনার মোবাইল ব্যালেন্স থেকে ৳${escapeHtml(pay.amt)} কেটে নেওয়া হবে। আপনি কি নিশ্চিত?</div>`;
  const modal = $("payModal");
  modal.classList.remove("hidden");
  $("payYes").onclick = () => {
    modal.classList.add("hidden");
    if (!$("sendBtn").disabled) send(`কনফার্ম, ${pay.item} এর জন্য ৳${pay.amt} পেমেন্ট করে দিন, নম্বর ${pay.num}`);
  };
  $("payNo").onclick = () => modal.classList.add("hidden");
}

// ---- Quick-action chips (advisory suggestions) + user-created shortcuts ----
const QUICK_ACTIONS = [
  { label: "🌾 প্ল্যান দিন", text: "আমার জমির জন্য একটি সম্পূর্ণ মৌসুমি প্ল্যান দিন।" },
  { label: "🌦️ আবহাওয়া", text: "এই সপ্তাহের আবহাওয়া আমার প্ল্যানে কোনো ঝুঁকি তৈরি করছে কি?" },
  { label: "💰 দামের তালিকা", text: "সার ও বীজের দামের তালিকা দিন।" },
  { label: "🐛 পোকা-রোগ", text: "আমার ফসলে কোন পোকা বা রোগের ঝুঁকি আছে?" },
];
const qa = $("quickActions");

function makeChip(label, text, custom) {
  const b = document.createElement("button");
  b.className = "chip" + (custom ? " custom" : "");
  b.textContent = label;
  b.title = text;
  b.addEventListener("click", () => { if (!$("sendBtn").disabled) send(text); });
  if (custom) {
    const x = document.createElement("span");
    x.className = "chip-x"; x.textContent = "✕"; x.title = "Remove shortcut";
    x.addEventListener("click", (e) => { e.stopPropagation(); removeShortcut(label); });
    b.appendChild(x);
  }
  return b;
}

function loadShortcuts() {
  try { return JSON.parse(localStorage.getItem("agrisense_shortcuts") || "[]"); }
  catch { return []; }
}
function saveShortcuts(list) { localStorage.setItem("agrisense_shortcuts", JSON.stringify(list)); }

function addShortcut(label, text) {
  const list = loadShortcuts();
  if (list.some((s) => s.label === label)) return;
  list.push({ label, text });
  saveShortcuts(list);
  renderChips();
  addTrace("status", `⭐ shortcut saved: ${label}`);
}
function removeShortcut(label) {
  const raw = label.replace(/^⭐\s*/, "").trim();  // chip shows "⭐ <label>"; stored label has no star
  saveShortcuts(loadShortcuts().filter((s) => s.label !== raw));
  renderChips();
}

// fuzzy removal by label OR message text, for conversational "remove X"
function normLabel(s) {
  return s.replace(/⭐/g, "").replace(/[^\p{L}\p{N}]/gu, "").toLowerCase().trim();
}
function removeShortcutFuzzy(target) {
  const t = normLabel(target);
  if (!t) return;
  const list = loadShortcuts();
  const kept = list.filter((s) => {
    const nl = normLabel(s.label), nt = normLabel(s.text);
    return !(nl === t || nl.includes(t) || t.includes(nl) || nt.includes(t));
  });
  if (kept.length !== list.length) {
    saveShortcuts(kept);
    renderChips();
    addTrace("status", `🗑 shortcut removed: ${target}`);
  }
}

function renderChips() {
  qa.innerHTML = "";
  for (const a of QUICK_ACTIONS) qa.appendChild(makeChip(a.label, a.text, false));
  for (const s of loadShortcuts()) qa.appendChild(makeChip("⭐ " + s.label, s.text, true));
  const add = document.createElement("button");
  add.className = "chip add"; add.textContent = "＋ শর্টকাট";
  add.title = "Create your own shortcut button";
  add.addEventListener("click", () => {
    const label = prompt("Shortcut button name (e.g. আজকের আবহাওয়া):");
    if (!label) return;
    const text = prompt("Message it should send:", "");
    if (text) addShortcut(label.trim(), text.trim());
  });
  qa.appendChild(add);
}
renderChips();

// ---- Draggable divider between chat and trace ----
(function () {
  const bar = $("dragbar");
  const trace = $("tracePane");
  let dragging = false;
  bar.addEventListener("mousedown", (e) => {
    dragging = true; bar.classList.add("dragging");
    document.body.style.userSelect = "none"; e.preventDefault();
  });
  window.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    const w = Math.min(Math.max(window.innerWidth - e.clientX, 60), window.innerWidth - 320);
    trace.classList.remove("collapsed");
    trace.style.flex = `0 0 ${w}px`;
  });
  window.addEventListener("mouseup", () => {
    dragging = false; bar.classList.remove("dragging"); document.body.style.userSelect = "";
  });
  bar.addEventListener("dblclick", () => { trace.style.flex = ""; trace.classList.remove("collapsed"); });
  $("traceToggle").addEventListener("click", () => {
    trace.classList.toggle("collapsed");
    trace.style.flex = "";
    $("traceToggle").textContent = trace.classList.contains("collapsed") ? "⟨" : "⟩";
  });
})();

addMessage(
  "assistant",
  marked.parse(
    "**আসসালামু আলাইকুম! Welcome to AgriSense AI.** 🌾\n\nTell me about your farm and I'll build you a complete, costed, weather-aware season plan. For example:\n\n> *\"I have 2 acres in Bogura, loam soil, tubewell irrigation, budget 80,000 taka, planning for this rabi season.\"*\n\nYou can also just say hello — I'll ask for what I need. আপনি বাংলায়ও লিখতে পারেন।"
  )
);
