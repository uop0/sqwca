"""
PY Guard — محرك تشفير ملفات بايثون (stdlib فقط — سريع وقوي)
الطرق:
  - secure (افتراضي): PBKDF2-HMAC-SHA256 + XOR-Stream + HMAC + zlib
    ينتج ملف .py مشفّر ذاتي فك التشفير (loader stub) يعمل بكلمة مرور.
  - marshal: compile + marshal + zlib + base64 (تعتيم سريع بدون كلمة مرور)
  - base64: zlib + base64 (تعتيم خفيف)
"""
import base64
import hashlib
import hmac
import marshal
import os
import zlib


def _derive_key(password: str, salt: bytes, length: int = 32) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000, dklen=length)


def _xor_stream(data: bytes, key: bytes) -> bytes:
    # keystream = SHA256(key || counter) chained — سريع وقوي بدون مكتبات خارجية
    out = bytearray(len(data))
    counter = 0
    pos = 0
    while pos < len(data):
        block = hashlib.sha256(key + counter.to_bytes(8, "big")).digest()
        chunk = min(len(block), len(data) - pos)
        for i in range(chunk):
            out[pos + i] = data[pos + i] ^ block[i]
        pos += chunk
        counter += 1
    return bytes(out)


def encrypt_secure(source: str, password: str) -> dict:
    if not password or len(password) < 4:
        raise ValueError("كلمة المرور يجب أن تكون 4 أحرف على الأقل")
    raw = zlib.compress(source.encode("utf-8"), 9)
    salt = os.urandom(16)
    key = _derive_key(password, salt)
    enc = _xor_stream(raw, key)
    tag = hmac.new(key, salt + enc, hashlib.sha256).digest()
    blob = salt + tag + enc
    b64 = base64.b64encode(blob).decode("ascii")

    loader = f'''# -*- coding: utf-8 -*-
# تم التشفير بواسطة PY Guard 🛡️ | تواصل: @FFQPU
import base64 as _b, hashlib as _h, hmac as _m, zlib as _z, getpass as _g
_B="{b64}"
def _x(_d,_k):
    _o=bytearray(len(_d));_c=0;_p=0
    while _p<len(_d):
        _blk=_h.sha256(_k+_c.to_bytes(8,"big")).digest()
        _n=min(len(_blk),len(_d)-_p)
        for _i in range(_n):_o[_p+_i]=_d[_p+_i]^_blk[_i]
        _p+=_n;_c+=1
    return bytes(_o)
def _run():
    try:_pw=_g.getpass("🔑 كلمة المرور: ")
    except Exception:_pw=input("🔑 كلمة المرور: ")
    _raw=_b.b64decode(_B)
    _s,_t,_e=_raw[:16],_raw[16:48],_raw[48:]
    _k=_h.pbkdf2_hmac("sha256",_pw.encode(),_s,200000,dklen=32)
    if not _m.compare_digest(_m.new(_k,_s+_e,_h.sha256).digest(),_t):
        print("❌ كلمة المرور خاطئة أو الملف تالف");return
    _src=_z.decompress(_x(_e,_k)).decode()
    exec(compile(_src,"<PYGuard>","exec"),{{"__name__":"__main__"}})
if __name__=="__main__":_run()
else:_run()
'''
    return {"method": "secure", "payload": loader, "size_in": len(source), "size_out": len(loader)}


def decrypt_secure_blob(blob_b64: str, password: str) -> str:
    raw = base64.b64decode(blob_b64)
    salt, tag, enc = raw[:16], raw[16:48], raw[48:]
    key = _derive_key(password, salt)
    if not hmac.compare_digest(hmac.new(key, salt + enc, hashlib.sha256).digest(), tag):
        raise ValueError("كلمة المرور خاطئة أو البيانات تالفة")
    return zlib.decompress(_xor_stream(enc, key)).decode("utf-8")


def encrypt_marshal(source: str) -> dict:
    code_obj = compile(source, "<PYGuard>", "exec")
    blob = base64.b64encode(zlib.compress(marshal.dumps(code_obj), 9)).decode("ascii")
    loader = f'''# مشفّر PY Guard (marshal) | @FFQPU
import base64 as _b, zlib as _z, marshal as _m
exec(_m.loads(_z.decompress(_b.b64decode("{blob}"))))
'''
    return {"method": "marshal", "payload": loader, "size_in": len(source), "size_out": len(loader)}


def encrypt_base64(source: str) -> dict:
    blob = base64.b64encode(zlib.compress(source.encode("utf-8"), 9)).decode("ascii")
    loader = f'''# مشفّر PY Guard (base64) | @FFQPU
import base64 as _b, zlib as _z
exec(_z.decompress(_b.b64decode("{blob}")).decode())
'''
    return {"method": "base64", "payload": loader, "size_in": len(source), "size_out": len(loader)}


def encrypt(source: str, password: str = "", method: str = "secure") -> dict:
    if method == "secure":
        return encrypt_secure(source, password)
    if method == "marshal":
        return encrypt_marshal(source)
    if method == "base64":
        return encrypt_base64(source)
    raise ValueError("طريقة غير مدعومة: " + method)
