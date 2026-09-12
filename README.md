# 本地 OCR 服务端

支持：**英文、繁体中文、数字** 混合识别，供按键精灵手机助手通过 HTTP 调用。

## 功能

- 默认引擎：**RapidOCR**（ONNX，轻量、兼容 Python 3.14）
- 备用引擎：**Tesseract**（需自行安装并配置语言包）
- 接口支持：
  - 上传图片文件（multipart/form-data）
  - Base64 图片（JSON）
  - 服务器本地图片路径（JSON）
  - 查找指定文字并返回点击坐标

## 安装

### 1. 安装依赖

```powershell
cd C:\Users\user\Desktop\ocr
python -m pip install -r requirements.txt
```

### 2. （可选）安装 Tesseract 备用引擎

如果你希望使用 Tesseract 作为备用，下载安装：

- 下载地址：https://github.com/UB-Mannheim/tesseract/wiki
- 安装时勾选 **Chinese (Traditional)** 和 **English** 语言包
- 安装后把安装路径加入系统环境变量 `PATH`，例如：
  ```
  C:\Program Files\Tesseract-OCR
  ```

## 启动服务

```powershell
cd C:\Users\user\Desktop\ocr
python server.py
```

成功后会显示：

```
OCR 服务端启动中: http://0.0.0.0:8080
```

## API 说明

### 1. 识别整张图片

**POST** `/ocr`

#### 方式 A：JSON + Base64

```json
{
  "image": "/9j/4AAQ..."
}
```

#### 方式 B：multipart 上传文件

```http
POST /ocr
Content-Type: multipart/form-data

file: screen.png
```

#### 返回示例

```json
{
  "success": true,
  "engine": "rapidocr",
  "count": 3,
  "results": [
    {
      "text": "Hello 世界123",
      "confidence": 0.95,
      "box": [[10,20],[120,20],[120,40],[10,40]],
      "x": 10,
      "y": 20,
      "w": 110,
      "h": 20,
      "center_x": 65,
      "center_y": 30
    }
  ]
}
```

### 2. 查找文字并返回坐标

**POST** `/click_text`

```json
{
  "image": "/9j/4AAQ...",
  "keyword": "開始"
}
```

返回：

```json
{
  "success": true,
  "text": "開始",
  "x": 300,
  "y": 450,
  "confidence": 0.92
}
```

## 按键精灵手机助手调用示例

假设 PC 服务端 IP 是 `192.168.1.100:8080`。

### 示例 1：截图后 POST 到服务端识别

```vb
Dim 图片路径 = "/sdcard/screen.png"
Call CaptureScreen(图片路径)  // 手机截图，保存到路径

// 把图片转成 base64（需有 Base64 编码插件或自己实现）
Dim base64Img = 文件转Base64(图片路径)

Dim url = "http://192.168.1.100:8080/ocr"
Dim body = "{\"image\":\"" & base64Img & "\"}"
Dim ret = HttpPost(url, body, "application/json")
TracePrint ret
```

### 示例 2：查找文字并点击

```vb
Dim 图片路径 = "/sdcard/screen.png"
Call CaptureScreen(图片路径)
Dim base64Img = 文件转Base64(图片路径)

Dim url = "http://192.168.1.100:8080/click_text"
Dim body = "{\"image\":\"" & base64Img & "\",\"keyword\":\"開始\"}"
Dim ret = HttpPost(url, body, "application/json")

// 解析 JSON（需有 JSON 解析插件）
Dim x = JSON_Get(ret, "x")
Dim y = JSON_Get(ret, "y")

If x <> "" And y <> "" Then
    Touch x, y
End If
```

### 示例 3：识别后遍历结果

```vb
Dim ret = HttpPost(url, body, "application/json")
Dim count = JSON_Get(ret, "count")
For i = 1 To count
    Dim text = JSON_Get(ret, "results[" & i & "].text")
    Dim cx = JSON_Get(ret, "results[" & i & "].center_x")
    Dim cy = JSON_Get(ret, "results[" & i & "].center_y")
    TracePrint text & " (" & cx & "," & cy & ")"
Next
```

> 注：按键精灵里的 `文件转Base64`、`HttpPost`、`JSON_Get`、`Touch` 等函数名称取决于你实际使用的插件/扩展命令，请替换成你环境里真实存在的命令。

## 环境变量

- `OCR_HOST`：监听地址，默认 `0.0.0.0`
- `OCR_PORT`：监听端口，默认 `8080`

```powershell
$env:OCR_PORT="9000"
python server.py
```

## 切换 OCR 引擎

在请求 URL 中加 `?backend=tesseract` 或 `?backend=rapidocr`：

```http
POST /ocr?backend=tesseract
```

默认 `auto`：优先 RapidOCR，不可用则 fallback 到 Tesseract。

## 提高繁体识别率

RapidOCR 默认模型对繁体已有一定支持。若效果不好，可：

1. 改用 Tesseract + `chi_tra+eng` 语言包
2. 自行下载 PaddleOCR 繁体模型，放到 RapidOCR 配置目录替换默认模型
