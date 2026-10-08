"""
AI Engine — محلل أخطاء بايثون + مولّد أدوات (يعمل محلياً بدون إنترنت — سريع)
"""
import ast
import re

COMMON_FIXES = [
    (re.compile(r"IndentationError.*unexpected indent", re.S), "خطأ مسافة بادئة: وحّد المسافات (4 مسافات) ولا تخلط Tab مع Space.", "وحّد المسافات البادئة إلى 4 مسافات لكل مستوى."),
    (re.compile(r"expected an indented block", re.S), "يوجد سطر يحتاج كتلة (بعد :): أضف سطراً مزاحاً تحته.", "أضف:\n    pass"),
    (re.compile(r"SyntaxError.*invalid syntax", re.S), "خطأ صياغي: غالباً قوس أو نقطتين ناقصة. راجع السطر المشار إليه والسطر الذي قبله.", "تحقق من الأقواس و : في نهاية def/if/for."),
    (re.compile(r"NameError: name '(\w+)'", re.S), "متغير غير معرّف. عرّفه قبل الاستخدام أو استورد المكتبة.", None),
    (re.compile(r"ModuleNotFoundError: No module named '(\w+)'", re.S), "مكتبة ناقصة. ثبّتها عبر pip.", None),
    (re.compile(r"ImportError.*cannot import name", re.S), "استيراد خاطئ: الاسم غير موجود في المكتبة. تحقق من اسم الدالة والنسخة.", "راجع توثيق المكتبة."),
    (re.compile(r"TypeError.*'NoneType'", re.S), "قيمة None غير متوقعة: دالة لم تُرجع شيئاً أو متغير لم يُعيَّن.", "أضف return وتحقق من القيم قبل الاستخدام."),
    (re.compile(r"IndexError: list index out of range", re.S), "تجاوزت طول القائمة. تحقق من الطول قبل الوصول بالفهرس.", "استخدم: if i < len(lst): ..."),
    (re.compile(r"KeyError: (.+)", re.S), "مفتاح غير موجود في القاموس.", "استخدم: d.get(key) بدل d[key]."),
    (re.compile(r"ZeroDivisionError", re.S), "قسمة على صفر.", "تحقق: if b != 0 قبل القسمة."),
    (re.compile(r"AttributeError: (.+)", re.S), "خاصية/دالة غير موجودة في الكائن. ربما خطأ إملائي أو نوع خاطئ.", "اطبع type(obj) للتأكد."),
    (re.compile(r"FileNotFoundError", re.S), "الملف غير موجود. تحقق من المسار ومجلد العمل.", "استخدم مساراً مطلقاً أو os.path.exists."),
    (re.compile(r"UnicodeDecodeError", re.S), "مشكلة ترميز. افتح الملف مع encoding='utf-8'.", 'open(path, encoding="utf-8")'),
    (re.compile(r"RecursionError", re.S), "استدعاء ذاتي لا نهائي.", "أضف شرط توقف."),
    (re.compile(r"pip.*not recognized|ModuleNotFoundError.*pip", re.S), "مشكلة pip.", "python -m pip install <pkg>"),
]


def diagnose(code: str, error_text: str = "") -> dict:
    findings = []
    fixes = []

    # 1) فحص صياغي عبر ast
    try:
        tree = ast.parse(code or "")
    except SyntaxError as e:
        findings.append(f"خطأ صياغي في السطر {e.lineno}: {e.msg}")
        fixes.append(f"راجع السطر {e.lineno}: «{e.text.strip() if e.text else ''}» — تأكد من الأقواس والنقطتين والمسافات.")
        tree = None
    else:
        findings.append("لا يوجد خطأ صياغي (الكود يُترجم بنجاح).")

    if code:
        lines = code.splitlines()
        # tabs vs spaces
        if any(l.startswith("\t") for l in lines) and any(l.startswith(" ") for l in lines):
            findings.append("خلط بين Tab و Space في المسافات البادئة — سبب شائع لـ IndentationError.")
            fixes.append("وحّد كل المسافات إلى 4 مسافات (ابحث واستبدل \\t).")
        # python2 print
        if re.search(r"print\s+[^(]", code):
            findings.append("صيغة print قديمة (Python 2).")
            fixes.append("استخدم print(...) بأقواس.")
        # استيرادات غير مستخدمة / متغيرات
        imports = re.findall(r"^\s*(?:import\s+(\w+)|from\s+(\w+))", code, re.M)
        for a, b in imports:
            mod = a or b
            if mod and code.count(mod) < 2:
                findings.append(f"استيراد «{mod}» يبدو غير مستخدم.")
        if "input(" in code and "strip()" not in code:
            fixes.append("نصيحة: استخدم input(...).strip() لتفادي مسافات زائدة.")
        # ملاحظة الأداء
        if len(code) > 20000:
            fixes.append("الملف كبير: قسّمه إلى وحدات لتسريع التحميل.")
        if tree is not None:
            # دوال بلا return
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not any(isinstance(n, ast.Return) and n.value is not None for n in ast.walk(node)):
                        findings.append(f"الدالة «{node.name}» لا تُرجع قيمة (تُرجع None).")
                        break

    # 2) تحليل نص الخطأ
    error_text = error_text or ""
    if error_text.strip():
        matched = False
        for pat, desc, fix in COMMON_FIXES:
            m = pat.search(error_text)
            if m:
                extra = f" ({m.group(1)})" if m.groups() else ""
                findings.append("تشخيص الخطأ: " + desc + extra)
                dyn_fix = fix
                if "No module named" in desc and m.groups():
                    dyn_fix = f"نفّذ: pip install {m.group(1)}"
                if "NameError" in error_text and m.groups():
                    dyn_fix = f"عرّف المتغير «{m.group(1)}» قبل السطر الخاطئ أو استورده."
                if dyn_fix:
                    fixes.append(dyn_fix)
                matched = True
                break
        if not matched:
            findings.append("رسالة خطأ غير مألوفة — راجع أول سطر من Traceback فهو الأهم.")
            fixes.append("انسخ أول وآخر سطر من الخطأ وابحث عنهما، وتأكد من إصدار بايثون والمكتبات.")
    else:
        fixes.append("الصق رسالة الخطأ الكاملة (Traceback) للحصول على تشخيص أدق.")

    score = 100
    if any("خطأ صياغي" in f for f in findings):
        score -= 40
    if any("Tab" in f for f in findings):
        score -= 15
    score = max(score, 5)

    return {
        "findings": findings,
        "fixes": fixes,
        "health": score,
        "summary": "✅ الكود سليم صياغياً." if score >= 90 else "⚠️ توجد ملاحظات تحتاج إصلاحاً (انظر التفاصيل).",
    }


TOOL_TEMPLATES = {
    "port_scanner": ("فاحص منافذ", '''import socket
target = input("الهدف (IP/دومين): ").strip()
ports = [21,22,23,25,53,80,110,143,443,445,3306,8080]
print(f"فحص {{target}} ...")
for p in ports:
    s = socket.socket(); s.settimeout(0.7)
    try:
        s.connect((target, p)); print(f"[مفتوح] {{p}}")
    except Exception: print(f"[مغلق] {{p}}")
    finally: s.close()
'''),
    "password_gen": ("مولّد كلمات مرور", '''import secrets, string
n = int(input("الطول (مثلا 16): ") or "16")
alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
print("".join(secrets.choice(alphabet) for _ in range(n)))
'''),
    "file_encrypt": ("مشفر ملفات", '''from pathlib import Path
import hashlib
pw = input("كلمة المرور: ")
data = Path("secret.txt").read_bytes()
key = hashlib.sha256(pw.encode()).digest()
enc = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
Path("secret.txt.enc").write_bytes(enc)
print("تم التشفير -> secret.txt.enc")
'''),
    "hash_crack_demo": ("مدقق هاشات تعليمي", '''import hashlib
h = input("MD5 المستهدف: ").strip()
for w in open(input("ملف الكلمات: ")).read().split():
    if hashlib.md5(w.encode()).hexdigest() == h:
        print("وجدت:", w); break
else: print("لم توجد كلمة مطابقة")
'''),
}


def generate_tool(prompt: str) -> dict:
    p = (prompt or "").lower()
    key = "password_gen"
    if any(w in p for w in ["port", "port scan", "منافذ", "سكان", "فحص"]):
        key = "port_scanner"
    elif any(w in p for w in ["تشفير", "encrypt", "ملف"]):
        key = "file_encrypt"
    elif any(w in p for w in ["هاش", "hash", "كراك", "كلمات مرور"]):
        key = "hash_crack_demo"
    title, code = TOOL_TEMPLATES[key]
    readme = f"# {title}\nطلبك: {prompt}\nتشغيل: python tool.py\nتواصل: @FFQPU"
    return {"title": title, "code": code, "readme": readme, "note": "تم التوليد بواسطة ذكاء PY Guard (القسم المدفوع)."}
