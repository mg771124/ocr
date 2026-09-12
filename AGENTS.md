# OCR 服务端项目规则

## 项目概述

- 本地 OCR HTTP 服务端，默认使用 RapidOCR（ONNX）。
- 监听 `0.0.0.0:8080`，支持 `OCR_HOST` / `OCR_PORT` 环境变量覆盖。
- 支持识别：英文、繁体中文、数字。

## 常用命令

```powershell
# 安装依赖
python -m pip install -r requirements.txt

# 启动服务端
python server.py

# 测试服务端（/ocr JSON base64）
python test_http.py

# 生成测试图并测试
python test_ocr.py
```

## 接口

- `GET  /`：健康检查，返回引擎可用状态。
- `POST /ocr`：识别图片，支持 `?backend=rapidocr|tesseract|auto`。
  - 输入：`multipart/form-data` 上传 `file`；或 JSON `{"image": "base64..."}`；或 JSON `{"image_path": "C:/..."}`。
- `POST /click_text`：查找文字，JSON `{"image": "base64...", "keyword": "..."}`。

## 测试约定

- 测试图片：`test.png`（默认生成 3 行文字：Hello World 123、繁體中文測試 ABC-789、開始 Game 2024）。
- 成功测试应返回 HTTP 200，`success: true`，`count` 接近 3。
- 端口 8080 若被占用，先关闭占用进程或用 `OCR_PORT` 换端口。

## 环境限制

- Tesseract 仅安装 Python 包，未安装主程序，实际不可用。
- 服务端无认证，仅在受信任局域网使用。
- 未启用 HTTPS，跨网段建议加反向代理。

## 代码规范

- 保持 Python 3.8+ 兼容，使用类型注解。
- 所有端点返回 JSON，包含 `success` 字段。
- 不要提交 API Key 或凭据。
