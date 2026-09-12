# OCR 服务端专案交接记录

## 专案位置

```
C:\Users\user\Desktop\ocr
```

## 目标

为「按键精灵手机助手（破解版，无法使用官方 OcrEx）」架设一个**本地 OCR 服务端**，支援识别：

- 英文
- 繁体中文
- 数字

手机端按键精灵通过 HTTP POST 把截图传给 PC 上的本服务端，服务端回传文字与坐标。

## 当前档案结构

```
C:\Users\user\Desktop\ocr\
├── server.py           # 主服务端程式（Flask + Waitress）
├── requirements.txt    # Python 依赖
├── README.md           # 使用说明 + 按键精灵调用范例
├── HANDOVER.md         # 本文件
├── test_ocr.py         # 生成测试图 + base64 测试
├── test_http.py        # 直接 HTTP 测试 /ocr 端点
└── test.png            # 测试图片（繁中英文数字混合）
```

## 已完成的部份

1. **环境确认**
   - 本机 Python 3.14.6 已安装
   - pip 可用

2. **依赖安装**
   - `flask` ✅
   - `waitress` ✅
   - `rapidocr-onnxruntime` ✅
   - `pytesseract` ✅（但本机未安装 Tesseract 主程式，所以实际不可用）
   - `opencv-python`、`onnxruntime`、`numpy`、`Pillow` 等都已安装

3. **服务端程式 `server.py` 完成**
   - 监听 `0.0.0.0:8080`
   - 提供 `/` 健康检查
   - 提供 `/ocr` 识别端点，支援三种输入：
     - `multipart/form-data` 上传图片文件
     - JSON `{"image": "base64字符串"}`
     - JSON `{"image_path": "C:/xxx/screen.png"}`
   - 提供 `/click_text` 找字端点，回传文字中心坐标
   - 自动排序结果（从上到下、从左到右）
   - 可透过 `?backend=rapidocr|tesseract|auto` 切换引擎

4. **已修正一个重要 bug**
   - 最初假设 RapidOCR 回传格式是 `(box, (text, score))`
   - 实测发现是 `[box, text, score]`
   - 已修正 `server.py` 第 124~126 行：
     ```python
     box, text, score = line
     score = float(score)
     ```

5. **测试图片已生成**
   - 包含：`Hello World 123`、`繁體中文測試 ABC-789`、`開始 Game 2024`

6. **RapidOCR 引擎已实测可用**
   - 直接执行 OCR 可识别出 3 行文字
   - 服务端 `/` 健康检查显示 `rapidocr: true`

## 还没验证 / 待完成的部份

1. **HTTP `/ocr` 端点完整验证**
   - 之前因为多个旧版 python 进程占用 8080 端口，导致测试打到旧版本服务
   - 已清除所有旧进程，但需要重新启动并再次验证
   - 验证命令：
     ```powershell
     cd C:\Users\user\Desktop\ocr
     python server.py
     # 另开终端
     python test_http.py
     ```

2. **繁体中文识别率实测**
   - 当前使用 RapidOCR 内建中文模型（`ch_PP-OCRv3_rec_infer.onnx`）
   - 对繁体已有一定支持，但需用真实截图实测
   - 若效果不佳，方案：
     - 安装 Tesseract + `chi_tra+eng` 语言包，改用 `?backend=tesseract`
     - 或下载 PaddleOCR 繁体模型替换 RapidOCR 默认模型

3. **按键精灵手机端集成测试**
   - 需要确认手机助手里的 HTTP 插件/命令名称
   - 需要确认 Base64 编码插件/命令名称
   - 需要确认 JSON 解析命令名称
   - README.md 里的范例用的是通用名称，需按实际环境替换

## 关键程式码说明

### `server.py` 主要流程

1. 启动时调用 `load_engines()` 初始化 RapidOCR 与 Tesseract
2. `/ocr` 收到请求后解码图片
3. 调用 `do_ocr()`，默认优先使用 RapidOCR
4. 回传 JSON：
   ```json
   {
     "success": true,
     "engine": "rapidocr",
     "count": 3,
     "results": [
       {
         "text": "Hello World 123",
         "confidence": 0.87,
         "box": [[50,38],[299,37],[299,68],[50,68]],
         "x": 50,
         "y": 37,
         "w": 249,
         "h": 31,
         "center_x": 174,
         "center_y": 52
       }
     ]
   }
   ```

### RapidOCR 结果格式

```python
[
  [ [[x1,y1],[x2,y2],[x3,y3],[x4,y4]], "文字", "0.95" ],
  ...
]
```

注意：score 是**字符串**，需 `float(score)`。

## 环境变量

- `OCR_HOST`：监听地址，默认 `0.0.0.0`
- `OCR_PORT`：监听端口，默认 `8080`

```powershell
$env:OCR_PORT="9000"
python server.py
```

## 建议接手后的步骤

1. **重新启动服务端并验证**
   ```powershell
   cd C:\Users\user\Desktop\ocr
   python server.py
   ```

2. **执行测试**
   ```powershell
   cd C:\Users\user\Desktop\ocr
   python test_http.py
   ```
   预期结果：HTTP 200，回传 JSON 包含 3 个 results。

3. **若测试失败**
   - 检查是否有其他程式占用 8080 端口
   - 检查 `server.py` 中 RapidOCR 结果解析是否正确
   - 查看服务端命令行错误讯息

4. **优化繁体识别**
   - 用真实截图测试
   - 若不准，安装 Tesseract 并启用 `?backend=tesseract`

5. **手机端集成**
   - 将 `README.md` 中的按键精灵范例改成用户实际使用的插件命令
   - 确认手机和 PC 在同一局域网
   - 用 PC 的实际局域网 IP（如 `192.168.x.x`）替换 `127.0.0.1`

## 注意事项

- **不要**把任何 API Key 或凭证写进代码后提交到公开仓库
- 服务端监听 `0.0.0.0`，在同一局域网内的装置都能存取，请确认网络安全
- 若长期运行，建议把服务端注册为 Windows 服务或排程任务

## 已知限制

- 当前 Tesseract 不可用（只装了 Python 套件，未装主程式）
- 服务端未做认证，建议仅在受信任的局域网使用
- 未做 HTTPS，若跨网段建议加一层反向代理

---

交接时间：2026-09-09
前置作业者：Devin
