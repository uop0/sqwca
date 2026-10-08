// PY Guard — نسخة ستاتيكية (تعمل دون خادم) — أسود/أخضر/أزرق
const $ = id => document.getElementById(id);
let lastPayload = "";
const enc = new TextEncoder(), dec = new TextDecoder();
const b64e = bytes => { let s=""; bytes.forEach(b=>s+=String.fromCharCode(b)); return btoa(s); };
const b64d = s => Uint8Array.from(atob(s), c=>c.charCodeAt(0));
async function sha256(data){ const h = await crypto.subtle.digest("SHA-256", data); return new Uint8Array(h); }
function concat(...arrs){ const t=new Uint8Array(arrs.reduce((a,x)=>a+x.length,0)); let o=0; for(const a of arrs){t.set(a,o);o+=a.length;} return t; }
function toB64Py(s){ return btoa(unescape(encodeURIComponent(s))); }
async function keystreamXor(data, key){
  const out = new Uint8Array(data.length); let pos=0, counter=0n;
  const dv = new DataView(new ArrayBuffer(8));
  while(pos < data.length){
    dv.setBigUint64(0, counter, false);
    const ctr = new Uint8Array(dv.buffer.slice(0));
    const block = await sha256(concat(key, ctr));
    for(let i=0;i<block.length && pos<data.length;i++,pos++) out[pos]=data[pos]^block[i];
    counter++;
  }
  return out;
}
async function encryptSecure(src, pw){
  const srcB = enc.encode(src), pwB = enc.encode(pw);
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const key = await sha256(concat(pwB, salt));
  const e = await keystreamXor(srcB, key);
  const tag = await sha256(concat(key, salt, e));
  const blob = b64e(concat(salt, tag, e));
  const loader = `# -*- coding: utf-8 -*-\n# تم التشفير بواسطة PY Guard 🛡️ (نسخة ستاتيكية) | @FFQPU\nimport base64 as _b, hashlib as _h, getpass as _g\n_B="${blob}"\ndef _x(_d,_k):\n    _o=bytearray(len(_d));_c=0;_p=0\n    while _p<len(_d):\n        _blk=_h.sha256(_k+_c.to_bytes(8,"big")).digest()\n        _n=min(len(_blk),len(_d)-_p)\n        for _i in range(_n):_o[_p+_i]=_d[_p+_i]^_blk[_i]\n        _p+=_n;_c+=1\n    return bytes(_o)\ndef _run():\n    try:_pw=_g.getpass("\\U0001f511 كلمة المرور: ")\n    except Exception:_pw=input("\\U0001f511 كلمة المرور: ")\n    _raw=_b.b64decode(_B)\n    _s,_t,_e=_raw[:16],_raw[16:48],_raw[48:]\n    _k=_h.sha256(_pw.encode()+_s).digest()\n    assert _h.sha256(_k+_s+_e).digest()==_t, "❌ كلمة المرور خاطئة"\n    exec(compile(_x(_e,_k).decode()," <PYGuard>","exec"),{"__name__":"__main__"})\nif __name__=="__main__":_run()\nelse:_run()\n`;
  return { method:"secure", payload: loader, blob };
}
async function decryptSecure(blobB64, pw){
  const raw = b64d(blobB64.trim()); const salt=raw.slice(0,16), tag=raw.slice(16,48), e=raw.slice(48);
  const key = await sha256(concat(enc.encode(pw), salt));
  const expect = await sha256(concat(key, salt, e));
  if(b64e(expect)!==b64e(tag)) throw new Error("كلمة المرور خاطئة أو البيانات تالفة");
  return dec.decode(await keystreamXor(e, key));
}
function encryptB64(src){
  const b = toB64Py(src);
  return { method:"base64", payload:`# مشفّر PY Guard (base64) | @FFQPU\nimport base64 as _b\nexec(_b.b64decode("${b}").decode())\n` };
}
function diagnose(code, err){
  const findings=[], fixes=[];
  if(!code.trim()) findings.push("لا يوجد كود للتحليل.");
  else {
    if(code.includes("\t") && /^ /m.test(code)){ findings.push("خلط بين Tab و Space — سبب شائع لـ IndentationError."); fixes.push("وحّد المسافات إلى 4 مسافات."); }
    else findings.push("فحص أولي: راجع الأقواس والنقطتين (:) والمسافات البادئة.");
    if(/print\s+[^(]/.test(code)){ findings.push("صيغة print قديمة (Python 2)."); fixes.push("استخدم print(...) بأقواس."); }
  }
  err = err||"";
  const rules=[
    [/ZeroDivisionError/, "قسمة على صفر.", "تحقق: if b != 0 قبل القسمة."],
    [/NameError: name '(\w+)'/, "متغير غير معرّف.", null],
    [/ModuleNotFoundError: No module named '(\w+)'/, "مكتبة ناقصة.", null],
    [/IndentationError/, "خطأ مسافة بادئة.", "وحّد المسافات إلى 4 مسافات."],
    [/expected an indented block/, "كتلة ناقصة بعد (:).", "أضف سطراً مزاحاً أو pass."],
    [/invalid syntax/, "خطأ صياغي.", "راجع الأقواس والنقطتين في السطر المشار إليه وما قبله."],
    [/IndexError/, "تجاوز طول القائمة.", "استخدم if i < len(lst)."],
    [/KeyError/, "مفتاح غير موجود.", "استخدم d.get(key)."],
    [/AttributeError/, "خاصية غير موجودة.", "اطبع type(obj) للتأكد."],
    [/FileNotFoundError/, "الملف غير موجود.", "تحقق من المسار."],
    [/TypeError.*NoneType/, "قيمة None غير متوقعة.", "أضف return وتحقق من القيم."],
    [/ImportError/, "استيراد خاطئ.", "راجع اسم الدالة ونسخة المكتبة."]
  ];
  let hit=false;
  for(const [rx,d,f] of rules){ const m=err.match(rx); if(m){ findings.push("تشخيص الخطأ: "+d+(m[1]?" ("+m[1]+")":"")); let fx=f;
    if(/No module named/.test(d)&&m[1]) fx="نفّذ: pip install "+m[1];
    if(/غير معرّف/.test(d)&&m[1]) fx="عرّف «"+m[1]+"» قبل الاستخدام أو استورده.";
    if(fx) fixes.push(fx); hit=true; break; } }
  if(err.trim()&&!hit){ findings.push("رسالة غير مألوفة — راجع أول وآخر سطر من Traceback."); fixes.push("تأكد من إصدار بايثون والمكتبات."); }
  if(!err.trim()) fixes.push("الصق رسالة الخطأ الكاملة (Traceback) لتشخيص أدق.");
  return { findings, fixes, health: findings.length<=1?90:60, summary: findings.length<=1?"✅ الكود يبدو سليماً.":"⚠️ توجد ملاحظات تحتاج إصلاحاً." };
}
const TOOLS={
  port:{t:"فاحص منافذ",c:`import socket\ntarget = input("الهدف (IP/دومين): ").strip()\nfor p in [21,22,23,25,53,80,110,143,443,445,3306,8080]:\n    s=socket.socket(); s.settimeout(0.7)\n    try:\n        s.connect((target,p)); print(f"[مفتوح] {p}")\n    except Exception: print(f"[مغلق] {p}")\n    finally: s.close()\n`},
  pass:{t:"مولّد كلمات مرور",c:`import secrets, string\nn=int(input("الطول (مثلا 16): ") or "16")\nalphabet=string.ascii_letters+string.digits+"!@#$%^&*"\nprint("".join(secrets.choice(alphabet) for _ in range(n)))\n`},
  enc:{t:"مشفر ملفات",c:`from pathlib import Path\nimport hashlib\npw=input("كلمة المرور: ")\ndata=Path("secret.txt").read_bytes()\nkey=hashlib.sha256(pw.encode()).digest()\nPath("secret.txt.enc").write_bytes(bytes(b^key[i%len(key)] for i,b in enumerate(data)))\nprint("تم التشفير -> secret.txt.enc")\n`}
};
function genTool(prompt){
  const p=(prompt||"").toLowerCase();
  const k=(/port|منافذ|سكان|فحص/.test(p))?"port":(/تشفير|encrypt|ملف/.test(p))?"enc":"pass";
  return TOOLS[k];
}
function isVip(){ return localStorage.getItem("pyg_vip")==="1"; }
function paintVip(){ if(isVip()){ const b=$("subBadge"); b.textContent="💎 مشترك VIP"; b.classList.add("vip"); } }
document.querySelectorAll(".tab").forEach(t=>t.onclick=()=>{
  document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));
  document.querySelectorAll(".panel").forEach(x=>x.classList.remove("active"));
  t.classList.add("active"); $("tab-"+t.dataset.tab).classList.add("active");
});
$("fileInput").onchange=e=>{ const f=e.target.files[0]; if(!f) return; const r=new FileReader(); r.onload=()=>$("srcCode").value=r.result; r.readAsText(f); };
$("btnEnc").onclick=async()=>{
  const src=$("srcCode").value; if(!src.trim()) return alert("الصق الكود أو ارفع ملف .py أولاً");
  const m=$("method").value, pw=$("pw").value;
  try{
    if(m==="secure"){ if(pw.length<4) return alert("كلمة المرور 4 أحرف على الأقل");
      const r=await encryptSecure(src,pw); lastPayload=r.payload; $("outCode").value=r.payload;
      $("blobInput").value=r.blob;
      $("encInfo").textContent=`✅ تم التشفير (secure) — ${src.length} حرف ← ${r.payload.length} حرف`;
    } else { const r=encryptB64(src); lastPayload=r.payload; $("outCode").value=r.payload;
      $("encInfo").textContent=`✅ تم التشفير (${m || "base64"}) — ${src.length} حرف`; }
    $("btnDl").disabled=false;
  }catch(e){ alert("فشل التشفير: "+e.message); }
};
$("btnDl").onclick=()=>{ const b=new Blob([lastPayload],{type:"text/x-python"}); const a=document.createElement("a"); a.href=URL.createObjectURL(b); a.download="encrypted_pyguard.py"; a.click(); };
$("btnDec").onclick=async()=>{ try{ $("decOut").textContent=await decryptSecure($("blobInput").value,$("pw").value); }catch(e){ $("decOut").textContent="❌ "+e.message; } };
$("btnAi").onclick=()=>{ const d=diagnose($("aiCode").value,$("aiErr").value);
  $("aiOut").innerHTML=`<b>${d.summary} (صحة الكود: ${d.health}%)</b>\n\n📌 التشخيص:\n- ${d.findings.join("\n- ")}\n\n🛠️ الحلول:\n- ${d.fixes.join("\n- ")}`; };
$("btnSub").onclick=()=>{ const c=$("asiacell").value.replace(/\D/g,"");
  if(![14,15,16].includes(c.length)){ $("subMsg").textContent="❌ كارت آسياسيل غير صالح (14-16 رقم). للمساعدة: @FFQPU"; return; }
  localStorage.setItem("pyg_vip","1"); $("subMsg").textContent="✅ تم تفعيل اشتراك VIP (5 كوينات آسياسيل) 🎉"; paintVip(); };
$("btnGen").onclick=()=>{ if(!isVip()){ $("toolOut").textContent="❌ للمشتركين فقط — فعّل الاشتراك بـ 5 كوينات آسياسيل"; return; }
  const t=genTool($("toolPrompt").value); $("toolOut").textContent="# "+t.t+"\n\n"+t.c;
  $("hostCode").value=t.c; $("hostName").value=t.t; $("btnHostTool").disabled=false; };
function hosts(){ try{return JSON.parse(localStorage.getItem("pyg_hosts")||"[]");}catch{return[];} }
function listHosts(){ const h=hosts(); $("hostList").innerHTML=h.length?h.map((x,i)=>`🚀 <b>${x.name}</b> (${x.code.length} حرف) <button class="btn" onclick="dlHost(${i})">⬇️ تحميل</button>`).join("\n"):"لا توجد مشاريع بعد — انشر أداتك الأولى 🚀"; }
window.dlHost=i=>{ const h=hosts()[i]; const b=new Blob([h.code],{type:"text/x-python"}); const a=document.createElement("a"); a.href=URL.createObjectURL(b); a.download=(h.name||"tool")+".py"; a.click(); };
function pub(n,c){ const h=hosts(); h.unshift({name:n,code:c,at:Date.now()}); localStorage.setItem("pyg_hosts",JSON.stringify(h.slice(0,20))); listHosts(); }
$("btnHost").onclick=()=>{ if(!isVip()) return alert("الاستضافة للمشتركين فقط (5 كوينات آسياسيل)"); if(!$("hostCode").value.trim()) return alert("لا يوجد كود للنشر"); pub($("hostName").value||"أداتي",$("hostCode").value); alert("تم النشر محلياً ✅"); };
$("btnHostTool").onclick=$("btnHost").onclick;
$("btnList").onclick=listHosts;
$("dot").classList.add("on"); $("statusTxt").textContent="يعمل محلياً ⚡ نسخة ستاتيكية سريعة"; paintVip(); listHosts();
