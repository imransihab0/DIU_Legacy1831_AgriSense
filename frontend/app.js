const $ = (id) => document.getElementById(id);

let sessionId = localStorage.getItem("agrisense_session");
if (!sessionId) {
  sessionId = "farm-" + Math.random().toString(36).slice(2, 10);
  localStorage.setItem("agrisense_session", sessionId);
}

fetch("/api/health").then(r => r.json()).then(h => {
  $("health").textContent = `${h.provider} · KB ${h.kb_chunks} chunks`;
}).catch(() => { $("health").textContent = "backend offline"; });

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

addMessage(
  "assistant",
  marked.parse(
    "**আসসালামু আলাইকুম! Welcome to AgriSense AI.** 🌾\n\nTell me about your farm and I'll build you a complete, costed, weather-aware season plan. For example:\n\n> *\"I have 2 acres in Bogura, loam soil, tubewell irrigation, budget 80,000 taka, planning for this rabi season.\"*\n\nYou can also just say hello — I'll ask for what I need. আপনি বাংলায়ও লিখতে পারেন।"
  )
);
