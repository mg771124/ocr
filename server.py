#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地 OCR 服务端
支持：英文、繁体中文、数字
调用方式：HTTP POST /ocr
    - multipart/form-data 上传图片文件
    - JSON: {"image": "base64字符串"}
    - JSON: {"image_path": "C:/xxx/screen.png"}

按键精灵手机助手调用示例见 README.md
"""

import os
import io
import re
import sys
import json
import base64
import logging
import tempfile
from typing import List, Dict, Any, Optional, Tuple

from flask import Flask, request, jsonify
from PIL import Image, ImageOps
import numpy as np

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ==================== OCR 引擎初始化 ====================

ocr_rapid: Any = None
ocr_rapid_force: Any = None
ocr_tesseract_available: bool = False


def init_rapidocr() -> Any:
    """初始化 RapidOCR（ONNX 版，轻量、兼容性好）"""
    try:
        from rapidocr_onnxruntime import RapidOCR
        # 默认模型对中文（含繁体）、英文、数字都有较好支持
        engine = RapidOCR()
        logger.info("RapidOCR 初始化成功")
        return engine
    except Exception as e:
        logger.error(f"RapidOCR 初始化失败: {e}")
        return None


def init_rapidocr_force() -> Any:
    """初始化强制识别引擎（跳过文字检测，直接识别整张图）"""
    try:
        from rapidocr_onnxruntime import RapidOCR
        engine = RapidOCR(use_text_det=False)
        logger.info("RapidOCR 强制识别引擎初始化成功")
        return engine
    except Exception as e:
        logger.error(f"RapidOCR 强制识别引擎初始化失败: {e}")
        return None


def init_tesseract() -> bool:
    """检查 Tesseract 是否可用"""
    try:
        import pytesseract
        # 测试是否安装
        pytesseract.get_tesseract_version()
        logger.info(f"Tesseract 可用，版本: {pytesseract.get_tesseract_version()}")
        return True
    except Exception as e:
        logger.warning(f"Tesseract 未安装或不可用: {e}")
        return False


def load_engines():
    """加载所有可用的 OCR 引擎"""
    global ocr_rapid, ocr_rapid_force, ocr_tesseract_available
    ocr_rapid = init_rapidocr()
    ocr_rapid_force = init_rapidocr_force()
    ocr_tesseract_available = init_tesseract()

    if ocr_rapid is None and not ocr_tesseract_available:
        logger.error("没有可用的 OCR 引擎，请检查依赖安装")
    else:
        logger.info(
            f"引擎状态: RapidOCR={ocr_rapid is not None}, "
            f"RapidOCRForce={ocr_rapid_force is not None}, "
            f"Tesseract={ocr_tesseract_available}"
        )


# ==================== 图片解码工具 ====================

def decode_image(data: bytes) -> Image.Image:
    """将字节流解码为 PIL Image"""
    return Image.open(io.BytesIO(data)).convert("RGB")


def decode_base64_image(b64_str: str) -> Image.Image:
    """解码 base64 图片"""
    # 去掉可能的 data:image/xxx;base64, 前缀
    if "," in b64_str:
        b64_str = b64_str.split(",", 1)[1]
    img_bytes = base64.b64decode(b64_str)
    return decode_image(img_bytes)


def save_temp_image(img: Image.Image, suffix: str = ".png") -> str:
    """保存临时图片并返回路径"""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    img.save(path)
    return path


# ==================== OCR 识别函数 ====================

def rapidocr_recognize(img: Image.Image) -> List[Dict[str, Any]]:
    """使用 RapidOCR 识别，返回带坐标的文本列表"""
    if ocr_rapid is None:
        raise RuntimeError("RapidOCR 引擎未加载")

    # 转为 numpy array (H, W, 3)
    arr = np.array(img)
    result, _ = ocr_rapid(arr)

    if result is None:
        return []

    items = []
    for line in result:
        # line 格式: [box, text, score]
        box, text, score = line
        score = float(score)
        # 计算中心点和宽高
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        x, y = min(xs), min(ys)
        w, h = max(xs) - x, max(ys) - y
        cx, cy = x + w / 2, y + h / 2

        items.append({
            "text": text,
            "confidence": float(score),
            "box": [[int(p[0]), int(p[1])] for p in box],
            "x": int(x),
            "y": int(y),
            "w": int(w),
            "h": int(h),
            "center_x": int(cx),
            "center_y": int(cy),
        })
    return items


def preprocess_for_ocr(img: Image.Image) -> Image.Image:
    """与 UI 一致的图像增强：灰度、暗底反转、自动对比度"""
    gray = img.convert("L")
    arr = np.array(gray)
    if arr.mean() < 128:
        gray = ImageOps.invert(gray)
    img = ImageOps.autocontrast(gray, cutoff=0)
    return img.convert("RGB")


def rapidocr_recognize_force(img: Image.Image, enhance: bool = True) -> List[Dict[str, Any]]:
    """强制识别整张图片，不检测文字位置，返回单行结果"""
    if ocr_rapid_force is None:
        raise RuntimeError("RapidOCR 强制识别引擎未加载")
    if enhance:
        img = preprocess_for_ocr(img)
    arr = np.array(img)
    res, _ = ocr_rapid_force(arr)
    items = []
    if res:
        for line in res:
            box, text, score = line
            # box 可能为空；若为空则使用整张图范围
            if box:
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                x, y = min(xs), min(ys)
                w, h = max(xs) - x, max(ys) - y
                cx, cy = x + w / 2, y + h / 2
            else:
                w, h = img.size
                x, y = 0, 0
                cx, cy = w / 2, h / 2
            items.append({
                "text": text,
                "confidence": float(score),
                "box": [[int(p[0]), int(p[1])] for p in box] if box else [[0, 0], [w, 0], [w, h], [0, h]],
                "x": int(x),
                "y": int(y),
                "w": int(w),
                "h": int(h),
                "center_x": int(cx),
                "center_y": int(cy),
            })
    return items


def tesseract_recognize(img: Image.Image, lang: str = "chi_tra+eng") -> List[Dict[str, Any]]:
    """使用 Tesseract 识别（备用引擎）"""
    if not ocr_tesseract_available:
        raise RuntimeError("Tesseract 不可用")

    import pytesseract
    data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)

    items = []
    n = len(data["text"])
    for i in range(n):
        text = data["text"][i].strip()
        conf = int(data["conf"][i])
        if not text or conf < 0:
            continue

        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        # 过滤置信度太低的
        if conf < 30:
            continue

        items.append({
            "text": text,
            "confidence": conf / 100.0,
            "box": [[x, y], [x + w, y], [x + w, y + h], [x, y + h]],
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "center_x": x + w // 2,
            "center_y": y + h // 2,
        })
    return items


def do_ocr(
    img: Image.Image,
    backend: str = "auto",
    lang: str = "chi_tra+eng",
    min_confidence: float = 0.0,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    执行 OCR，返回 (实际使用的引擎, 结果列表)
    """
    engine = backend
    if engine == "auto":
        if ocr_rapid is not None:
            engine = "rapidocr"
        elif ocr_tesseract_available:
            engine = "tesseract"
        else:
            raise RuntimeError("没有可用的 OCR 引擎")

    if engine == "rapidocr":
        results = rapidocr_recognize(img)
    elif engine == "tesseract":
        results = tesseract_recognize(img, lang=lang)
    else:
        raise ValueError(f"不支持的引擎: {backend}")

    # 过滤低置信度
    if min_confidence > 0:
        results = [r for r in results if r["confidence"] >= min_confidence]

    return engine, results


# ==================== Flask 路由 ====================

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "ok",
        "rapidocr": ocr_rapid is not None,
        "tesseract": ocr_tesseract_available,
        "usage": "POST /ocr with file, base64 image, or image_path",
    })


@app.route("/ping", methods=["GET", "POST"])
def ping():
    return "pong\n"


def parse_json_body():
    """解析请求体，兼容未设置 Content-Type: application/json 的客户端"""
    data = request.get_json(silent=True)
    if data is not None:
        return data
    raw = request.get_data(as_text=True)
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return {}


def get_request_image():
    """从请求中解析图片，返回 (PIL.Image, 来源) 或 (None, 错误信息)"""
    if "file" in request.files:
        file = request.files["file"]
        if file.filename == "":
            return None, "空文件名"
        return decode_image(file.read()), "file"

    data = parse_json_body()
    if data and ("image" in data or "image_path" in data):
        if "image" in data:
            return decode_base64_image(data["image"]), "base64"
        elif "image_path" in data:
            path = data["image_path"]
            if not os.path.exists(path):
                return None, f"图片不存在: {path}"
            return Image.open(path).convert("RGB"), "path"
        else:
            return None, "缺少参数: 请提供 file、image(base64) 或 image_path"

    return None, "不支持的请求格式，请用 multipart/form-data 或 application/json"


@app.route("/ocr", methods=["POST"])
def ocr_endpoint():
    try:
        img, source = get_request_image()
        if img is None:
            return jsonify({"success": False, "error": source}), 400

        backend = request.args.get("backend", "auto")
        lang = request.args.get("lang", "chi_tra+eng")
        min_conf = float(request.args.get("min_confidence", "0.0"))

        engine, results = do_ocr(img, backend=backend, lang=lang, min_confidence=min_conf)
        results.sort(key=lambda r: (r["y"], r["x"]))

        logger.info(f"来源={source}, 引擎={engine}, 识别到 {len(results)} 个文本块")

        return jsonify({
            "success": True,
            "engine": engine,
            "source": source,
            "count": len(results),
            "results": results,
        })

    except Exception as e:
        logger.exception("OCR 处理失败")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/ocr_simple", methods=["POST"])
def ocr_simple_endpoint():
    """返回简化版 OCR 结果，每行：text confidence x y w h center_x center_y"""
    try:
        img, err = get_request_image()
        if img is None:
            return f"ERROR\t{err}\n", 400

        backend = request.args.get("backend", "auto")
        lang = request.args.get("lang", "chi_tra+eng")
        min_conf = float(request.args.get("min_confidence", "0.0"))

        engine, results = do_ocr(img, backend=backend, lang=lang, min_confidence=min_conf)
        results.sort(key=lambda r: (r["y"], r["x"]))

        lines = []
        for r in results:
            text = str(r["text"]).replace("\t", " ").replace("\n", " ")
            lines.append(
                f"{text}\t{r['confidence']:.4f}\t{r['x']}\t{r['y']}\t{r['w']}\t{r['h']}\t{r['center_x']}\t{r['center_y']}"
            )

        if not lines:
            return "OK\t0\n"
        return "OK\t" + str(len(lines)) + "\n" + "\n".join(lines) + "\n"

    except Exception as e:
        logger.exception("OCR 简单结果处理失败")
        return f"ERROR\t{str(e)}\n", 500


@app.route("/ocr_force", methods=["POST"])
def ocr_force_endpoint():
    """强制识别整张图片，适合区域截图、单行文字；默认开启图像增强"""
    try:
        img, err = get_request_image()
        if img is None:
            return f"ERROR\t{err}\n", 400

        enhance = request.args.get("enhance", "1") in ("1", "true", "True")
        results = rapidocr_recognize_force(img, enhance=enhance)
        results.sort(key=lambda r: (r["y"], r["x"]))

        lines = []
        for r in results:
            text = str(r["text"]).replace("\t", " ").replace("\n", " ")
            lines.append(
                f"{text}\t{r['confidence']:.4f}\t{r['x']}\t{r['y']}\t{r['w']}\t{r['h']}\t{r['center_x']}\t{r['center_y']}"
            )

        if not lines:
            return "OK\t0\n"
        return "OK\t" + str(len(lines)) + "\n" + "\n".join(lines) + "\n"

    except Exception as e:
        logger.exception("OCR 强制识别处理失败")
        return f"ERROR\t{str(e)}\n", 500


@app.route("/click_text", methods=["POST"])
def click_text_endpoint():
    """
    查找指定文字并返回中心坐标（方便按键精灵直接点击）
    请求: {"image": "base64", "keyword": "目标文字"}
    """
    try:
        data = request.get_json() or {}
        if "image" not in data or "keyword" not in data:
            return jsonify({"success": False, "error": "缺少 image 或 keyword 参数"}), 400

        img = decode_base64_image(data["image"])
        keyword = data["keyword"]
        backend = data.get("backend", "auto")

        engine, results = do_ocr(img, backend=backend)

        matches = [r for r in results if keyword in r["text"]]
        exact = [r for r in matches if r["text"] == keyword]
        if exact:
            matches = exact

        if not matches:
            return jsonify({"success": False, "error": "未找到文字", "engine": engine}), 404

        matches.sort(key=lambda r: r["confidence"], reverse=True)
        best = matches[0]

        return jsonify({
            "success": True,
            "engine": engine,
            "text": best["text"],
            "x": best["center_x"],
            "y": best["center_y"],
            "box": best["box"],
            "confidence": best["confidence"],
        })

    except Exception as e:
        logger.exception("查找文字失败")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/click_text_simple", methods=["POST"])
def click_text_simple_endpoint():
    """返回简化版文字坐标：x y confidence text，未找到返回 NOT_FOUND"""
    try:
        data = parse_json_body()
        if not data or "image" not in data or "keyword" not in data:
            return "ERROR\t缺少 image 或 keyword 参数\n", 400

        img = decode_base64_image(data["image"])
        keyword = data["keyword"]
        backend = data.get("backend", "auto")

        engine, results = do_ocr(img, backend=backend)

        matches = [r for r in results if keyword in r["text"]]
        exact = [r for r in matches if r["text"] == keyword]
        if exact:
            matches = exact

        if not matches:
            return "NOT_FOUND\n"

        matches.sort(key=lambda r: r["confidence"], reverse=True)
        best = matches[0]
        text = str(best["text"]).replace("\t", " ").replace("\n", " ")
        return f"{best['center_x']}\t{best['center_y']}\t{best['confidence']:.4f}\t{text}\n"

    except Exception as e:
        logger.exception("查找文字简单结果处理失败")
        return f"ERROR\t{str(e)}\n", 500


# ==================== 启动入口 ====================

def main():
    load_engines()

    host = os.environ.get("OCR_HOST", "0.0.0.0")
    port = int(os.environ.get("OCR_PORT", "8080"))

    # 生产环境推荐用 waitress，否则用 Flask 开发服务器
    try:
        from waitress import serve
        logger.info(f"OCR 服务端启动中: http://{host}:{port}")
        serve(app, host=host, port=port)
    except ImportError:
        logger.warning("未安装 waitress，使用 Flask 开发服务器（仅用于测试）")
        app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
