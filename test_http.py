#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64
import json
import urllib.request
import urllib.error

with open("test.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode("utf-8")

body = json.dumps({"image": b64}).encode("utf-8")
req = urllib.request.Request(
    "http://127.0.0.1:8080/ocr",
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)

try:
    resp = urllib.request.urlopen(req, timeout=60)
    data = resp.read().decode("utf-8")
    print("SUCCESS:")
    print(data)
except urllib.error.HTTPError as e:
    data = e.read().decode("utf-8")
    print("HTTP ERROR", e.code)
    print("BODY:", repr(data))
except Exception as e:
    print("OTHER ERROR", type(e), e)
