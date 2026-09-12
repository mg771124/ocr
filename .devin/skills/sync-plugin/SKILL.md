---
name: sync-plugin
description: 同步 OCR 插件文件到两个按键精灵插件目录
argument-hint: ""
allowed-tools:
  - exec
permissions:
  allow:
    - Exec(cmd.exe)
    - Exec(powershell.exe)
---

把 `C:\Users\user\Desktop\ocr\mobile_plugin\` 下的插件文件同步到两个按键精灵目录：

- `C:\ProgramData\aaj\aaj\Plugin\`
- `C:\Program Files (x86)\nsaj\nsaj\Plugin\`

同步的文件包括：

- `LocalOCR.lua`
- `LocalOCR.info`
- `LocalOCR.html`
- `ScanApi.lua`
- `ScanApi.info`
- `ScanApi.html`

操作步骤：

1. 提醒用户先关闭按键精灵手机助手，避免 `.info` 等文件被占用。
2. 优先运行 `C:\Users\user\Desktop\ocr\install_plugins.bat`，提示用户右键选择 **以管理员身份运行**。
3. 如果无法自动运行批处理，则分别复制：
   - `aaj` 目录：`Copy-Item mobile_plugin\*.* C:\ProgramData\aaj\aaj\Plugin\`
   - `nsaj` 目录：需要管理员权限执行
     ```bat
     xcopy /Y C:\Users\user\Desktop\ocr\mobile_plugin\*.* "C:\Program Files (x86)\nsaj\nsaj\Plugin\"
     ```
4. 复制完成后提示用户重启按键精灵手机助手或刷新插件列表。

返回：每个目录的复制结果（成功/失败）。
