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
    thinkingEl.innerHTML = marked.parse(ev.content || "");
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

// ---- Quick-action chips ----
const QUICK_ACTIONS = [
  { label: "🌾 প্ল্যান দিন", text: "আমার জমির জন্য একটি সম্পূর্ণ মৌসুমি প্ল্যান দিন।" },
  { label: "🌦️ আবহাওয়া", text: "এই সপ্তাহের আবহাওয়া আমার প্ল্যানে কোনো ঝুঁকি তৈরি করছে কি?" },
  { label: "💰 দামের তালিকা", text: "সার ও বীজের দামের তালিকা দিন।" },
  { label: "🐛 পোকা-রোগ", text: "আমার ফসলে কোন পোকা বা রোগের ঝুঁকি আছে?" },
  { label: "🛒 এখুনি কিনুন", text: "আমার প্ল্যানের দরকারি সার এখন কিনতে চাই। আমার নম্বর 8801875191553।", cls: "buy" },
  { label: "✅ কনফার্ম করুন", text: "কনফার্ম, পেমেন্ট করে দিন।", cls: "confirm" },
];
const qa = $("quickActions");
for (const a of QUICK_ACTIONS) {
  const b = document.createElement("button");
  b.className = "chip" + (a.cls ? " " + a.cls : "");
  b.textContent = a.label;
  b.addEventListener("click", () => { if (!$("sendBtn").disabled) send(a.text); });
  qa.appendChild(b);
}

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
