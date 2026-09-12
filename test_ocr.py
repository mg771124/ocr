#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试本地 OCR 服务端"""

import base64
import json
import urllib.request
from PIL import Image, ImageDraw, ImageFont


def create_test_image(path: str = "test.png"):
    """生成一张包含繁体中文、英文、数字的测试图"""
    img = Image.new("RGB", (600, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 尝试用系统字体，没有则用默认字体
    try:
        # Windows 常见中文字体
        font = ImageFont.truetype("msyh.ttc", 32)
    except Exception:
        try:
            font = ImageFont.truetype("msyh.ttf", 32)
        except Exception:
            font = ImageFont.load_default()

    texts = [
        ("Hello World 123", (50, 30)),
        ("繁體中文測試 ABC-789", (50, 80)),
        ("開始 Game 2024", (50, 130)),
    ]
    for text, pos in texts:
        draw.text(pos, text, fill=(0, 0, 0), font=font)

    img.save(path)
    print(f"测试图已保存: {path}")
    return path


def test_base64():
    path = create_test_image("test.png")

    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    data = json.dumps({"image": b64}).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8080/ocr",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        print(e.read().decode("utf-8"))
        raise


if __name__ == "__main__":
    test_base64()
