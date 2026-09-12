#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ctypes
import json
import os
import socket
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk, ImageGrab, ImageOps
import numpy as np
from rapidocr_onnxruntime import RapidOCR

_engine = None
_engine_force = None

def get_engine(force=False):
    global _engine, _engine_force
    if force:
        if _engine_force is None:
            _engine_force = RapidOCR(use_text_det=False)
        return _engine_force
    if _engine is None:
        _engine = RapidOCR()
    return _engine


class OCRUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR 测试 UI")
        self.root.geometry("1280x800")
        self.root.minsize(800, 600)

        self.img = None
        self.scaled_img = None
        self.photo = None
        self.scale = 1.0
        self.rect = None
        self.start = None
        self.selection = None

        self.overlay = None
        self.shot = None
        self.shot_photo = None
        self.shot_rect = None
        self.shot_start = None

        main = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(main)
        right = ttk.Frame(main, width=320)
        main.add(left, weight=3)
        main.add(right, weight=1)

        self.canvas = tk.Canvas(left, bg="#333")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_down)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_up)

        ttk.Button(right, text="打开图片", command=self.open_image).pack(pady=(10, 5))
        ttk.Button(right, text="截图", command=self.snip_screen).pack(pady=5)
        ttk.Button(right, text="识别整张图片", command=self.ocr_full).pack(pady=5)
        ttk.Button(right, text="识别选中区域", command=self.ocr_selection).pack(pady=5)
        ttk.Button(right, text="清空选区", command=self.clear_selection).pack(pady=5)

        self.enhance = tk.BooleanVar(value=True)
        ttk.Checkbutton(right, text="图像增强", variable=self.enhance).pack(anchor=tk.W, pady=5)

        self.add_server_info(right)

        ttk.Label(right, text="识别结果").pack(anchor=tk.W, pady=(15, 0))
        self.result = scrolledtext.ScrolledText(right, wrap=tk.WORD, height=25)
        self.result.pack(fill=tk.BOTH, expand=True, pady=5)

        self.status = ttk.Label(right, text="未加载图片")
        self.status.pack(anchor=tk.W, pady=5)

    def add_server_info(self, right):
        host = socket.gethostbyname(socket.gethostname()) or '127.0.0.1'
        port = int(os.environ.get('OCR_PORT', 8080))
        url = f"http://{host}:{port}"

        frame = ttk.LabelFrame(right, text="HTTP 服务端", padding=5)
        frame.pack(fill=tk.X, pady=10)

        ttk.Label(frame, text=f"IP: {host}").pack(anchor=tk.W)
        ttk.Label(frame, text=f"Port: {port}").pack(anchor=tk.W)

        example = {
            "image": "data:image/png;base64,iVBORw0...",
            "image_path": "C:/test.png"
        }
        text = (
            f"POST {url}/ocr\n"
            f"Content-Type: application/json\n\n"
            f"{json.dumps(example, indent=2, ensure_ascii=False)}\n\n"
            f"POST {url}/click_text\n"
            f"{{\"keyword\": \"冒險\", \"image\": \"...\"}}\n\n"
            f"POST {url}/ocr_simple\n"
            f"POST {url}/click_text_simple\n"
            f"(plain text response for Lua plugin)"
        )
        box = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=10)
        box.pack(fill=tk.X)
        box.insert(tk.END, text)
        box.config(state=tk.DISABLED)

    def open_image(self):
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self.img = Image.open(path).convert("RGB")
            self.show_image()
            self.status.config(text=f"已加载: {path}")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开图片: {e}")

    def show_image(self):
        MAX_W, MAX_H = 1000, 700
        w, h = self.img.size
        self.scale = min(MAX_W / w, MAX_H / h, 1.0)
        nw, nh = int(w * self.scale), int(h * self.scale)
        self.scaled_img = self.img.resize((nw, nh), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.scaled_img)
        self.canvas.delete("all")
        self.canvas.config(width=nw, height=nh)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.clear_selection()

    def on_down(self, e):
        self.start = (e.x, e.y)
        if self.rect:
            self.canvas.delete(self.rect)
            self.rect = None
        self.selection = None

    def on_drag(self, e):
        if not self.start:
            return
        if self.rect:
            self.canvas.delete(self.rect)
        x1, y1 = self.start
        x2, y2 = e.x, e.y
        self.rect = self.canvas.create_rectangle(
            x1, y1, x2, y2, outline="red", width=2
        )

    def on_up(self, e):
        if not self.start:
            return
        x1, y1 = self.start
        x2, y2 = e.x, e.y
        if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
            self.start = None
            return
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        self.selection = (
            int(x1 / self.scale),
            int(y1 / self.scale),
            int(x2 / self.scale),
            int(y2 / self.scale),
        )
        self.start = None

    def clear_selection(self):
        if self.rect:
            self.canvas.delete(self.rect)
            self.rect = None
        self.selection = None

    def snip_screen(self):
        self.root.withdraw()
        self.root.update()
        try:
            self.shot = ImageGrab.grab()
        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("错误", f"截图失败: {e}")
            return

        sw, sh = self.shot.size

        self.overlay = tk.Toplevel(self.root)
        self.overlay.attributes("-topmost", True)
        self.overlay.overrideredirect(True)
        self.overlay.geometry(f"{sw}x{sh}+0+0")
        self.overlay.bind("<Escape>", lambda e: self.cancel_snip())

        c = tk.Canvas(self.overlay, width=sw, height=sh, cursor="cross", bg="black", highlightthickness=0)
        c.pack(fill=tk.BOTH, expand=True)
        self.shot_photo = ImageTk.PhotoImage(self.shot)
        c.create_image(0, 0, anchor=tk.NW, image=self.shot_photo)
        c.bind("<Button-1>", self.on_snip_down)
        c.bind("<B1-Motion>", self.on_snip_drag)
        c.bind("<ButtonRelease-1>", self.on_snip_up)
        self.overlay_canvas = c

    def on_snip_down(self, e):
        self.shot_start = (e.x, e.y)
        if self.shot_rect:
            self.overlay_canvas.delete(self.shot_rect)
            self.shot_rect = None

    def on_snip_drag(self, e):
        if not self.shot_start:
            return
        if self.shot_rect:
            self.overlay_canvas.delete(self.shot_rect)
        x1, y1 = self.shot_start
        x2, y2 = e.x, e.y
        self.shot_rect = self.overlay_canvas.create_rectangle(
            x1, y1, x2, y2, outline="red", width=3
        )

    def on_snip_up(self, e):
        if not self.shot_start:
            return
        x1, y1 = self.shot_start
        x2, y2 = e.x, e.y
        if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
            self.shot_start = None
            return
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        self.shot_start = None

        sw, sh = self.shot.size
        x1, x2 = max(0, x1), min(sw, x2)
        y1, y2 = max(0, y1), min(sh, y2)

        self.img = self.shot.crop((x1, y1, x2, y2))
        self.overlay.destroy()
        self.overlay = None
        self.root.deiconify()
        self.root.lift()
        self.show_image()
        try:
            results = self.run_ocr(self.img, force=True)
            self.display(results, "截图区域")
            self.status.config(text="截图并识别完成")
        except Exception as e:
            messagebox.showerror("错误", f"识别失败: {e}")
            self.status.config(text="识别失败")

    def cancel_snip(self):
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None
        self.root.deiconify()

    def preprocess(self, pil_img):
        gray = pil_img.convert("L")
        arr = np.array(gray)
        if arr.mean() < 128:
            gray = ImageOps.invert(gray)
        img = ImageOps.autocontrast(gray, cutoff=0)
        return img.convert("RGB")

    def run_ocr(self, pil_img, force=False):
        if force and self.enhance.get():
            pil_img = self.preprocess(pil_img)
        arr = np.array(pil_img)
        res, _ = get_engine(force=force)(arr)
        out = []
        if res:
            for line in res:
                box, text, score = line
                out.append((text, float(score), box))
            out.sort(key=lambda r: (min(p[1] for p in r[2]), min(p[0] for p in r[2])))
        return out

    def display(self, results, title=""):
        self.result.delete("1.0", tk.END)
        if title:
            self.result.insert(tk.END, f"=== {title} ===\n")
        if not results:
            self.result.insert(tk.END, "未识别到文字\n")
            return
        for text, score, _ in results:
            self.result.insert(tk.END, f"{text}  (置信度: {score:.2f})\n")
        self.result.insert(tk.END, f"\n共识别 {len(results)} 行文字\n")

    def ocr_full(self):
        if not self.img:
            messagebox.showwarning("提示", "请先打开图片或截图")
            return
        self.status.config(text="正在识别...")
        self.root.update()
        try:
            results = self.run_ocr(self.img)
            self.display(results, "识别结果")
            self.status.config(text="识别完成")
        except Exception as e:
            messagebox.showerror("错误", f"识别失败: {e}")
            self.status.config(text="识别失败")

    def ocr_selection(self):
        if not self.img:
            messagebox.showwarning("提示", "请先打开图片或截图")
            return
        if not self.selection:
            messagebox.showwarning("提示", "请先框选要识别的区域")
            return
        x1, y1, x2, y2 = self.selection
        x1, x2 = max(0, x1), min(self.img.width, x2)
        y1, y2 = max(0, y1), min(self.img.height, y2)
        if x2 - x1 < 10 or y2 - y1 < 10:
            messagebox.showwarning("提示", "选区太小")
            return
        self.status.config(text="正在强制识别选中区域...")
        self.root.update()
        try:
            crop = self.img.crop((x1, y1, x2, y2))
            results = self.run_ocr(crop, force=True)
            self.display(results, "选中区域")
            self.status.config(text="选中区域识别完成")
        except Exception as e:
            messagebox.showerror("错误", f"识别失败: {e}")
            self.status.config(text="识别失败")


def main():
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass
    root = tk.Tk()
    OCRUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
