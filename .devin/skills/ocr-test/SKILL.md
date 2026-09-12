---
name: ocr-test
description: 启动 OCR 服务端并运行完整测试
argument-hint: "[port]"
allowed-tools:
  - read
  - exec
permissions:
  allow:
    - Exec(python)
    - Exec(python.exe)
---

启动 `C:\Users\user\Desktop\ocr\server.py`，等待服务就绪，然后依次执行：

1. `GET /` 健康检查，确认 `rapidocr: true`。
2. `python test_http.py` 测试 `/ocr` JSON base64 识别。
3. `python test_ocr.py` 生成测试图并测试 `/ocr`。
4. 用 `test.png` 测试 `/click_text`，关键词 `Game`。
5. 可选测试 multipart 上传 `test.png`。

如果端口 8080 被占用，尝试 `$env:OCR_PORT` 或参数指定端口。完成后关闭服务端进程。

返回：每个测试的结果、识别到的文字数量、发现的任何错误。
