# LocalOCR 插件说明

按键精灵手机助手 Lua 插件，通过 HTTP 把截图发送到本地 OCR 服务端识别。

## 文件

- `LocalOCR.lua`：OCR 调用插件
- `ScanApi.lua`：扫描 `LuaAuxLib` 中 HTTP/文件相关命令（调试用）

## 安装

把两个 `.lua` 文件复制到按键精灵手机助手的 `plugin` 目录：

| 版本 | 插件目录 |
|---|---|
| 安卓版 | `C:\ProgramData\aaj\aaj\Plugin\` |
| 手机助手/iOS 版 | `C:\Program Files (x86)\nsaj\nsaj\Plugin\` |

也可以双击项目根目录的 `install_ocr_plugins.bat`（需要管理员权限），自动复制到两个目录。

复制后**重启按键精灵手机助手**或刷新插件列表。

## 命令列表

| 命令 | 说明 |
|---|---|
| `LocalOCR.SetServer host_port` | 设置默认服务端地址，例如 `"192.168.1.101:8080"` |
| `LocalOCR.Ping host_port` | 测试手机到 PC 服务端的连通性，返回 `"OK"` 或 `"ERROR|..."` |
| `LocalOCR.RecognizeStr host_port, image_path` | 识别整张图片，返回 `text\|conf\|x\|y\|w\|h\|cx\|cy;...` |
| `LocalOCR.FindTextStr host_port, image_path, keyword` | 查找文字，返回 `x\|y\|conf\|text`，未找到返回 `ERROR|...` |
| `LocalOCR.SetScreenshotPath path` | 设置区域查找时临时截图路径，默认 `/sdcard/LocalOCR_region.png` |
| `LocalOCR.识别 x1, y1, x2, y2` | 识别指定区域内所有文字，返回文字字符串 |
| `LocalOCR.ocr x1, y1, x2, y2, text, click` | 在指定区域精确查找文字，找到返回 `true`，`click=1` 自动点击 |
| `LocalOCR.ocra x1, y1, x2, y2, text, click` | 在指定区域模糊查找文字（包含即可），找到返回 `true` |

`host_port` 可省略，使用 `SetServer` 设置的默认值。
找到文字后，坐标通过 `LocalOCR.LastFindX()` 和 `LocalOCR.LastFindY()` 获取。

## 脚本示例

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

## 服务端要求

- PC 上运行 OCR 服务端：`python server.py` 或打包版 `OCR_Server.exe`
- 服务端监听 `0.0.0.0:8080`，手机和 PC 在同一局域网
- PC 防火墙放行 8080 端口

## 常见问题

### 导入插件后崩溃

- `Import "LocalOCR.lua"` 必须放在脚本**第 1 行**。
- 插件内部没有中文字符串和大量顶层局部变量，兼容 Lua 5.2。

### `ERROR|HTTP POST failed: server returned empty`

- 服务端未启动。
- 手机与 PC 不在同一 WiFi。
- IP 填错，请用 `ipconfig` 查看 PC 的真实局域网 IP。
- 防火墙拦截，可在 PC 运行：
  ```powershell
  New-NetFirewallRule -DisplayName "OCR Server 8080" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow
  ```

### 查看手机里有哪种 HTTP 命令

```vb
Import "ScanApi.lua"
TracePrint ScanApi.Scan()
```

LocalOCR.lua 会自动尝试 `Url.Post`、`Url.HttpPost`、`URL_OperationPost`、`PostHttp` 等常见命令。
