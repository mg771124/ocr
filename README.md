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

## 按键精灵手机助手插件

项目已提供 Lua 插件，封装了 HTTP、Base64、JSON 解析，直接调用即可。

### 插件文件

- `mobile_plugin/LocalOCR.lua`：OCR 调用插件
- `mobile_plugin/ScanApi.lua`：扫描 `LuaAuxLib` 中 HTTP/文件相关命令（调试用）
- `install_ocr_plugins.bat`：自动把插件复制到按键精灵插件目录

### 安装插件

把两个 `.lua` 文件复制到按键精灵手机助手的 `plugin` 目录：

| 版本 | 插件目录 |
|---|---|
| 安卓版 | `C:\ProgramData\aaj\aaj\Plugin\` |
| 手机助手/iOS 版 | `C:\Program Files (x86)\nsaj\nsaj\Plugin\` |

推荐双击运行 `install_ocr_plugins.bat`（需要管理员权限），它会自动复制到上述两个目录。

复制后**重启按键精灵手机助手**或刷新插件列表。

### 插件命令

| 命令 | 说明 |
|---|---|
| `LocalOCR.SetServer host_port` | 设置默认服务端地址，如 `"192.168.1.101:8080"` |
| `LocalOCR.Ping host_port` | 测试连通性，返回 `"OK"` 或 `"ERROR|..."` |
| `LocalOCR.RecognizeStr host_port, image_path` | 识别整张图片，返回 `text\|conf\|x\|y\|w\|h\|cx\|cy;...` |
| `LocalOCR.FindTextStr host_port, image_path, keyword` | 查找文字，返回 `x\|y\|conf\|text`，未找到返回 `ERROR|...` |
| `LocalOCR.SetScreenshotPath path` | 设置区域查找时临时截图路径，默认 `/sdcard/LocalOCR_region.png` |
| `LocalOCR.识别 x1, y1, x2, y2` | 识别指定区域内所有文字，返回文字字符串 |
| `LocalOCR.ocr x1, y1, x2, y2, text, click` | 在指定区域精确查找文字，找到返回 `true`，`click=1` 自动点击 |
| `LocalOCR.ocra x1, y1, x2, y2, text, click` | 在指定区域模糊查找文字（包含即可），找到返回 `true` |

`host_port` 可省略，使用 `SetServer` 设置的默认值。

找到文字后，坐标通过 `LocalOCR.LastFindX()` 和 `LocalOCR.LastFindY()` 获取。

### 脚本示例

```vb
Import "LocalOCR.lua"

// 设置为 PC 端服务端 IP，在 OCR 服务端 UI 或 ipconfig 中查看
LocalOCR.SetServer "192.168.1.101:8080"

// 1. 先测连通
Dim ping = LocalOCR.Ping("")
TracePrint ping

// 2. 区域内查找"开始"并自动点击
If LocalOCR.ocr(100, 200, 400, 500, "开始", 1) = True Then
    TracePrint "点击了 " & LocalOCR.LastFindX() & "," & LocalOCR.LastFindY()
Else
    TracePrint "未找到"
End If

// 3. 识别区域内文字
Dim text = LocalOCR.识别(100, 200, 400, 250)
TracePrint "识别结果: " & text

// 4. 区域内模糊查找包含"T"的文字，不点击
If LocalOCR.ocra(100, 200, 400, 500, "T", 0) = True Then
    TracePrint "找到在 " & LocalOCR.LastFindX() & "," & LocalOCR.LastFindY()
End If
```

### 常见问题

1. **导入插件后崩溃/报错**
   - `Import "LocalOCR.lua"` 必须放在脚本**第 1 行**。
   - 插件使用兼容 Lua 5.2 语法，顶层局部变量不超过 200 个。

2. **`ERROR|HTTP POST failed: server returned empty`**
   - 服务端未启动，或手机与 PC 不在同一局域网。
   - 检查 PC 防火墙是否放行 8080 端口。
   - 确认 IP 是 PC 的真实局域网 IP（`ipconfig` 查看）。

3. **查看可用的 HTTP 命令**
   ```vb
   Import "ScanApi.lua"
   TracePrint ScanApi.Scan()
   ```

## 打包版 EXE（无需 Python）

已提供 PyInstaller 一键打包脚本，可在没有 Python 的 Windows 机器上直接运行。

### 1. 服务端打包版

- 入口：`dist\OCR_Server\OCR_Server.exe`
- 把整个 `dist\OCR_Server` 文件夹复制到目标电脑，双击 `OCR_Server.exe` 即可启动
- 启动后会监听 `0.0.0.0:8080`，黑色命令行窗口是日志，不要关闭
- 目标电脑需放行 8080 端口防火墙

### 2. 桌面测试/管理端打包版

- 入口：`dist\OCR_UI\OCR_UI.exe`
- 把整个 `dist\OCR_UI` 文件夹复制到目标电脑，双击 `OCR_UI.exe` 可打开桌面 UI
- UI 中可加载图片测试识别、截图选区、查看服务端 IP 与接口示例

### 重新打包

```powershell
cd C:\Users\user\Desktop\ocr
python -m PyInstaller --noconfirm server.spec
python -m PyInstaller --noconfirm OCR_UI.spec
```

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
