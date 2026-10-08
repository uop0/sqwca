// PY Guard frontend
const $ = id => document.getElementById(id);
let device = localStorage.getItem("pyg_device");
if (!device) { device = "d-" + Math.random().toString(36).slice(2) + Date.now().toString(36); localStorage.setItem("pyg_device", device); }
let lastPayload = "";

async function api(path, body) {
  const r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });
  return r.json();
}
async function refresh() {
  try {
    const s = await (await fetch("/api/status?device=" + device)).json();
    $("dot").classList.add("on"); $("statusTxt").textContent = "متصل ⚡ " + (s.hosted || 0) + " مشروع مستضاف";
    if (s.subscribed) { const b = $("subBadge"); b.textContent = "💎 مشترك VIP"; b.classList.add("vip"); }
  } catch { $("statusTxt").textContent = "غير متصل"; }
}
document.querySelectorAll(".tab").forEach(t => t.onclick = () => {
  document.querySelectorAll(".tab").forEach(x => x.classList.remove("active"));
  document.querySelectorAll(".panel").forEach(x => x.classList.remove("active"));
  t.classList.add("active"); $("tab-" + t.dataset.tab).classList.add("active");
});
$("fileInput").onchange = e => {
  const f = e.target.files[0]; if (!f) return;
  const r = new FileReader(); r.onload = () => $("srcCode").value = r.result; r.readAsText(f);
};
$("btnEnc").onclick = async () => {
  const src = $("srcCode").value; if (!src.trim()) return alert("الصق الكود أو ارفع ملف .py أولاً");
  const d = await api("/api/encrypt", { source: src, password: $("pw").value, method: $("method").value });
  if (d.error) return alert(d.error);
  lastPayload = d.payload; $("outCode").value = d.payload;
  $("encInfo").textContent = `✅ تم التشفير (${d.method}) — الأصلي: ${d.size_in} حرف → المشفر: ${d.size_out} حرف`;
  $("btnDl").disabled = false;
};
$("btnDl").onclick = () => {
  const blob = new Blob([lastPayload], { type: "text/x-python" });
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "encrypted_pyguard.py"; a.click();
};
$("btnDec").onclick = async () => {
  const d = await api("/api/decrypt", { blob: $("blobInput").value.trim(), password: $("pw").value });
  $("decOut").textContent = d.error ? "❌ " + d.error : d.source;
};
$("btnAi").onclick = async () => {
  $("aiOut").textContent = "⏳ جاري التحليل...";
  const d = await api("/api/ai-fix", { code: $("aiCode").value, error: $("aiErr").value });
  $("aiOut").innerHTML = `<b>${d.summary} (صحة الكود: ${d.health}%)</b>\n\n📌 التشخيص:\n- ${d.findings.join("\n- ")}\n\n🛠️ الحلول:\n- ${d.fixes.join("\n- ")}`;
};
$("btnSub").onclick = async () => {
  const d = await api("/api/subscribe", { code: $("asiacell").value.trim(), device });
  $("subMsg").textContent = d.error ? "❌ " + d.error : "✅ " + d.message;
  refresh();
};
$("btnGen").onclick = async () => {
  const d = await api("/api/generate", { prompt: $("toolPrompt").value, device });
  if (d.error) { $("toolOut").textContent = "❌ " + d.error + " (اشترك بـ 5 كوينات آسياسيل أولاً)"; return; }
  $("toolOut").textContent = "# " + d.title + "\n# " + d.note + "\n\n" + d.code;
  $("hostCode").value = d.code; $("hostName").value = d.title;
  $("btnHostTool").disabled = false;
};
async function host(name, code) {
  const d = await api("/api/host", { name, code, device });
  if (d.error) alert(d.error); else { alert("تم النشر: " + d.url); listHosts(); }
  return d;
}
$("btnHost").onclick = () => host($("hostName").value || "أداتي", $("hostCode").value);
$("btnHostTool").onclick = () => host($("hostName").value || "أداتي", $("hostCode").value);
$("btnList").onclick = listHosts;
async function listHosts() {
  const d = await (await fetch("/api/hosts")).json();
  $("hostList").innerHTML = d.hosts.length ? d.hosts.map(h => `🚀 <b>${h.name}</b> — <a href="${h.url}" target="_blank" style="color:#00bfff">${h.url}</a> (${h.size} حرف)`).join("\n") : "لا توجد مشاريع بعد.";
}
refresh(); listHosts();
