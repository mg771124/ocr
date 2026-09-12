# OCR 本地服务端项目交接文档

## 项目目标

为「按键精灵手机助手（破解版，无法使用官方 OcrEx）」架设一个本地 OCR 服务端，实现：

- 识别英文、繁体中文、简体中文、数字。
- 手机端通过 HTTP 把截图发送到 PC 服务端识别。
- 返回文字 + 坐标，支持区域查找与点击。
- 提供桌面 UI 测试工具、可打包为无需 Python 的 EXE。
- 提供按键精灵 Lua 插件，方便脚本调用。

## 仓库

- GitHub: `https://github.com/mg771124/ocr`
- 本地路径: `C:\Users\user\Desktop\ocr`
- 分支: `main`

## 核心文件

| 文件 | 说明 |
|---|---|
| `server.py` | Flask + Waitress OCR HTTP 服务端 |
| `ocr_ui.py` | 桌面测试 UI（选区、截图、识别、增强） |
| `server.spec` | PyInstaller 服务端打包配置 |
| `OCR_UI.spec` | PyInstaller UI 打包配置 |
| `mobile_plugin/LocalOCR.lua` | 按键精灵 Lua 插件 |
| `mobile_plugin/ScanApi.lua` | 扫描 `LuaAuxLib` 中 HTTP/文件命令（调试用） |
| `mobile_plugin/LocalOCR.info` | 插件 IDE 提示文件 |
| `mobile_plugin/LocalOCR.html` | 插件帮助文档 |
| `mobile_plugin/gen_info.py` | 生成 `.info` 的脚本 |
| `mobile_plugin/gen_html.py` | 生成 `.html` 的脚本 |
| `install_plugins.bat` | 把插件复制到两个按键精灵目录 |
| `AGENTS.md` | 项目规则 |
| `.devin/skills/ocr-test/SKILL.md` | OCR 测试 Skill |
| `.devin/skills/sync-plugin/SKILL.md` | 插件同步 Skill |

## 服务端接口

| 接口 | 说明 |
|---|---|
| `GET/POST /ping` | 健康检查，返回 `pong\n` |
| `POST /ocr` | 标准 OCR，返回 JSON |
| `POST /ocr_simple` | 简化 OCR，返回 `OK\t<count>\n` + 每行结果 |
| `POST /ocr_simple?force=1&enhance=1` | 强制识别 + 图像增强（区域/单行文字推荐） |
| `POST /ocr_force` | 强制识别（旧接口，保留兼容） |
| `POST /click_text` | JSON 查找文字坐标 |
| `POST /click_text_simple` | 简化查找文字坐标 |

简化结果每行格式：

```
text\tconfidence\tx\ty\tw\th\tcenter_x\tcenter_y
```

## 插件命令

| 命令 | 说明 |
|---|---|
| `LocalOCR.SetServer host_port` | 设置默认服务端地址 |
| `LocalOCR.Ping host_port` | 测试连通性 |
| `LocalOCR.RecognizeStr host_port, image_path` | 识别整张图片，返回 `text\|conf\|...;...` |
| `LocalOCR.FindTextStr host_port, image_path, keyword` | 查找文字坐标 |
| `LocalOCR.ocrText x1, y1, x2, y2` | 识别指定区域内文字（强制识别+增强） |
| `LocalOCR.ocr x1, y1, x2, y2, text, click` | 区域内精确查找，click=1 自动点击 |
| `LocalOCR.ocra x1, y1, x2, y2, text, click` | 区域内模糊查找 |
| `LocalOCR.LastFindX()` / `LastFindY()` / `LastFindText()` | 获取上次查找结果 |
| `LocalOCR.SetScreenshotPath path` | 设置临时截图路径 |

注意：Lua 不支持中文函数名，因此用 `ocrText/ocr/ocra` 代替原来的中文名。

## 最近完成的关键修复

### 1. 区域识别使用强制识别 + 图像增强

- 服务端 `/ocr_simple` 新增 `force=1` 参数，走 `RapidOCR(use_text_det=False)`。
- 插件 `ocrText/ocr/ocra` 改为请求 `/ocr_simple?force=1&enhance=1`。
- 这样与 UI 中「截图区域 + 图像增强」的效果一致。

### 2. HTTP 命令选择

- 用户环境里的可用命令是 `NET_httpPost` / `URL_OperationPost`。
- `URL_OperationPost` 返回空，因此插件优先使用 `NET_httpPost`。
- `NET_httpPost` 需要传 table：`{url=..., data=..., header=..., timeout=..., code="UTF-8"}`。

### 3. Base64 编码器修复

- 旧版 `_priv.base64_encode` 在编码末尾不会生成 `=` 填充。
- 导致服务端解码时报 `Incorrect padding`。
- 已修复，现在会正确补 `=`。

### 4. 插件同步

- `install_plugins.bat` 会复制 `.lua`、`.info`、`.html` 到两个目录：
  - `C:\ProgramData\aaj\aaj\Plugin\`
  - `C:\Program Files (x86)\nsaj\nsaj\Plugin\`
- 同步前必须**关闭按键精灵手机助手**，否则 `.info`/`.html` 会被占用导致复制失败。

## 当前状态（截至最新提交）

- 插件版本: `1.2.0`
- 服务端 EXE 已重新打包：`C:\Users\user\Desktop\ocr\dist\OCR_Server\OCR_Server.exe`
- GitHub 已推送最新代码。
- 本地调试时 `/ocr_simple?force=1&enhance=1` 能正确识别测试图片中的「快速引导」。

## 已知问题 / 待确认

1. **用户尚未验证修复后的完整流程**
   - 已给出测试脚本，等待用户运行后反馈。
2. **坐标缩放问题**
   - 用户从 UI 抄下来的坐标可能是缩放后的，实际设备坐标可能不同。
   - 若区域识别仍不准，建议用全屏 `ocrText(0,0,0,0)` 或校验坐标。
3. **插件安装权限**
   - `nsaj` 目录需要管理员权限。
   - `aaj` 目录在按键精灵运行时会被锁定。
4. **大图片问题**
   - 全屏截图 base64 较大，某些 HTTP 命令可能传输失败。
   - 区域识别应尽量只截取目标文字附近的小区域。

## 推荐下一步验证

让用户运行：

```vb
Import "LocalOCR.lua"
LocalOCR.SetServer "192.168.1.101:8080"

Dim ping = LocalOCR.Ping("")
TracePrint "ping: " & ping

Dim text = LocalOCR.ocrText(109, 19, 187, 47)
TracePrint "识别: " & text

If LocalOCR.ocra(109, 19, 187, 47, "快速", 0) = True Then
    TracePrint "找到: " & LocalOCR.LastFindX() & "," & LocalOCR.LastFindY()
Else
    TracePrint "没找到"
End If
```

## 技能与规则

- `.devin/skills/ocr-test/SKILL.md`：启动服务端并跑完整测试。
- `.devin/skills/sync-plugin/SKILL.md`：同步插件到两个按键精灵目录。
- `AGENTS.md`：项目规则与常用命令。

## 打包说明

- 服务端：`python -m PyInstaller -y server.spec`，产物在 `dist\OCR_Server\`。
- UI：`python -m PyInstaller -y OCR_UI.spec`，产物在 `dist\OCR_UI\`。
- 目标机器不需要安装 Python，直接复制整个 `dist\OCR_Server` 文件夹。
