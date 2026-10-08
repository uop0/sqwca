#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PY Guard 🛡️ — تطبيق تشفير بايثون + AI + قسم مدفوع + استضافة
عربي • أسود + أخضر/أزرق • سريع (stdlib فقط) • قوي
المطور: @FFQPU | الاشتراك: 5 كوينات آسياسيل
تشغيل: python3 app.py --port 8000
"""
import argparse
import html
import json
import os
import re
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pyguard
import ai_engine

BASE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(BASE, "store.json")
HOSTED = os.path.join(BASE, "hosted")
os.makedirs(HOSTED, exist_ok=True)

MAX_BODY = 2 * 1024 * 1024  # 2MB — سريع ويمنع الإغراق


def load_store():
    try:
        with open(STORE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"devices": {}, "hosts": []}


def save_store(s):
    tmp = STORE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False)
    os.replace(tmp, STORE)


def subscribed(store, device):
    d = (device or "")[:64]
    return bool(d and store.get("devices", {}).get(d, {}).get("active"))


class Handler(BaseHTTPRequestHandler):
    server_version = "PYGuard/1.0"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False))

    def _file(self, path, ctype):
        try:
            with open(path, "rb") as f:
                data = f.read()
            self._send(200, data, ctype)
        except FileNotFoundError:
            self._send(404, "غير موجود", "text/plain; charset=utf-8")

    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        path, qs = p.path, urllib.parse.parse_qs(p.query)
        if path in ("/", "/index.html"):
            return self._file(os.path.join(BASE, "templates", "index.html"), "text/html; charset=utf-8")
        if path.startswith("/static/"):
            name = path[len("/static/"):]
            if ".." in name or "/" in name:
                return self._send(400, "{}")
            ctype = "text/plain; charset=utf-8"
            if name.endswith(".css"):
                ctype = "text/css; charset=utf-8"
            elif name.endswith(".js"):
                ctype = "application/javascript; charset=utf-8"
            return self._file(os.path.join(BASE, "static", name), ctype)
        if path == "/api/status":
            s = load_store()
            return self._json({"ok": True, "subscribed": subscribed(s, qs.get("device", [""])[0]),
                               "hosted": len(s.get("hosts", [])), "price": "5 كوينات آسياسيل",
                               "dev": "@FFQPU"})
        if path == "/api/hosts":
            s = load_store()
            return self._json({"hosts": s.get("hosts", [])[-20:][::-1]})
        if path.startswith("/h/"):
            hid = re.sub(r"[^a-zA-Z0-9_-]", "", path[3:])[:32]
            fp = os.path.join(HOSTED, hid + ".py")
            if not os.path.exists(fp):
                return self._send(404, "المشروع غير موجود", "text/plain; charset=utf-8")
            with open(fp, encoding="utf-8") as f:
                code = f.read()
            page = f"""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<title>{html.escape(hid)} | PY Guard hosting</title>
<style>body{{background:#000;color:#00ff88;font-family:monospace;padding:20px}}a{{color:#00bfff}}pre{{border:1px solid #00ff88;border-radius:8px;padding:12px;direction:ltr;text-align:left}}</style>
</head><body><h2>🚀 {html.escape(hid)}</h2><p>مستضاف مجاناً عبر PY Guard | @FFQPU</p>
<a href="/h/{hid}/download">⬇️ تحميل .py</a><pre>{html.escape(code[:20000])}</pre></body></html>"""
            return self._send(200, page, "text/html; charset=utf-8")
        if path.startswith("/h/") and path.endswith("/download"):
            hid = re.sub(r"[^a-zA-Z0-9_-]", "", path[3:-9])[:32]
            return self._file(os.path.join(HOSTED, hid + ".py"), "text/x-python; charset=utf-8")
        return self._send(404, "غير موجود", "text/plain; charset=utf-8")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length > MAX_BODY:
            return self._json({"error": "الحجم كبير جداً (الحد 2MB)"}, 413)
        try:
            raw = self.rfile.read(length) if length else b"{}"
            data = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            return self._json({"error": "JSON غير صالح"}, 400)

        if self.path == "/api/encrypt":
            src = data.get("source", "")
            if not src.strip():
                return self._json({"error": "لا يوجد كود للتشفير"}, 400)
            if len(src) > 500_000:
                return self._json({"error": "الملف كبير جداً"}, 400)
            try:
                r = pyguard.encrypt(src, data.get("password", ""), data.get("method", "secure"))
                return self._json({"ok": True, **r})
            except ValueError as e:
                return self._json({"error": str(e)}, 400)
        if self.path == "/api/decrypt":
            try:
                src = pyguard.decrypt_secure_blob(data.get("blob", ""), data.get("password", ""))
                return self._json({"ok": True, "source": src})
            except Exception as e:
                return self._json({"error": str(e)}, 400)
        if self.path == "/api/ai-fix":
            d = ai_engine.diagnose(data.get("code", ""), data.get("error", ""))
            return self._json({"ok": True, **d})
        if self.path == "/api/subscribe":
            code = re.sub(r"\D", "", str(data.get("code", "")))
            device = str(data.get("device", ""))[:64]
            if not device:
                return self._json({"error": "معرّف الجهاز مفقود"}, 400)
            # سعر الاشتراك: 5 كوينات آسياسيل — يقبل كارت 14-16 رقماً (تجريبي)
            if len(code) not in (14, 15, 16):
                return self._json({"error": "كارت آسياسيل غير صالح (14-16 رقم). للمساعدة: @FFQPU"}, 400)
            s = load_store()
            s.setdefault("devices", {})[device] = {"active": True, "at": time.time(), "card_tail": code[-4:]}
            save_store(s)
            return self._json({"ok": True, "message": "تم تفعيل اشتراك VIP بنجاح (5 كوينات آسياسيل) 🎉"})
        if self.path == "/api/generate":
            s = load_store()
            if not subscribed(s, str(data.get("device", ""))):
                return self._json({"error": "هذه الميزة للمشتركين فقط"}, 403)
            g = ai_engine.generate_tool(data.get("prompt", ""))
            return self._json({"ok": True, **g})
        if self.path == "/api/host":
            s = load_store()
            if not subscribed(s, str(data.get("device", ""))):
                return self._json({"error": "الاستضافة المجانية للمشتركين فقط (5 كوينات آسياسيل)"}, 403)
            name = str(data.get("name", "أداتي"))[:60] or "أداتي"
            code = data.get("code", "")
            if not code.strip():
                return self._json({"error": "لا يوجد كود للنشر"}, 400)
            hid = "app-" + os.urandom(4).hex()
            with open(os.path.join(HOSTED, hid + ".py"), "w", encoding="utf-8") as f:
                f.write(code)
            s.setdefault("hosts", []).append({"id": hid, "name": name, "url": f"/h/{hid}", "size": len(code)})
            save_store(s)
            return self._json({"ok": True, "id": hid, "url": f"/h/{hid}"})
        return self._json({"error": "مسار غير معروف"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    ap.add_argument("--host", default="0.0.0.0")
    a = ap.parse_args()
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    print(f"PY Guard 🛡️ يعمل على http://{a.host}:{a.port} — @FFQPU")
    srv.serve_forever()


if __name__ == "__main__":
    main()
