#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sync upstream TeamRatko sub (INCY-style request with x-hwid) -> sub_plain.txt.

Логика зеркала:
- тянет ориг с тем же HWID, что и клиент INCY
- полностью перезаписывает sub_plain.txt (новые добавляются, пропавшие удаляются)
- печатает дифф added/removed по именам серверов

URL и HWID берутся из env (для GitHub Actions secrets),
иначе используются дефолты ниже.
"""
import os
import ssl
import sys
import urllib.parse
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

UPSTREAM_URL = os.environ.get(
    "UPSTREAM_URL",
    "https://sub.teamratko.online:9443/558403932/LHzhT2PN03aKyEWoc78BXWqj5MgGTIbu",
)
SUB_HWID = os.environ.get("SUB_HWID", "270DD26E-160D-4257-B8AC-654800E12F24")
OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sub_plain.txt")

CTX = ssl._create_unverified_context()


def fetch_plain() -> str:
    req = urllib.request.Request(
        UPSTREAM_URL,
        headers={
            "User-Agent": "v2rayNG/1.9.42",
            "Accept": "*/*",
            "x-hwid": SUB_HWID,
            "x-device-os": "Windows",
            "x-ver-os": "10.0.26100",
            "x-device-model": "Desktop",
        },
    )
    with urllib.request.urlopen(req, context=CTX, timeout=30) as r:
        if r.status != 200:
            raise RuntimeError(f"upstream HTTP {r.status}")
        return r.read().decode("utf-8", errors="replace")


def names_of(text: str) -> list:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "#" in line:
            out.append(urllib.parse.unquote(line.split("#", 1)[1]))
        else:
            out.append(line)
    return out


def main() -> None:
    new_text = fetch_plain()
    if "127.0.0.1:9" in new_text and "не поддерживается" in new_text:
        raise RuntimeError("upstream вернул заглушку: HWID не принят")
    new_names = names_of(new_text)

    old_names: list = []
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE, encoding="utf-8", errors="replace") as f:
            old_names = names_of(f.read())

    with open(OUT_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_text if new_text.endswith("\n") else new_text + "\n")

    old_set, new_set = set(old_names), set(new_names)
    print(f"old={len(old_names)} new={len(new_names)}")
    for n in sorted(new_set - old_set):
        print(f"+ {n}")
    for n in sorted(old_set - new_set):
        print(f"- {n}")


if __name__ == "__main__":
    main()
