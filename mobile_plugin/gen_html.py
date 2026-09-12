# -*- coding: utf-8 -*-
import os


def build_html(title, commands):
    header = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=gb2312" />
<title>{title}</title>
<style>
body{{font-size:12px; font-family:Verdana,"宋体"}}
.ts{{ background:#fff; margin:0 0 40px 0;}}
.ts th{{ color:#7B797B; background:#DEDFDE; line-height:24px;}}
.ts td {{padding:6px 0;}}
.name {{ font-size:16px; font-weight:bold; border-top:1px dashed #9C9A9C; border-bottom:1px dashed #9C9A9C; color:#006939;}}
.canshu {{ background:#E7E7EF;}}
.red{{ color:#d60000;}}
.green{{ color:#006939;}}
.blue{{ color:#316AC5;}}
.fanhui{{ border-bottom:1px dashed #9C9A9C;}}
.lizi{{ border-bottom:1px dashed #9C9A9C;}}
</style></head><body>
'''.format(title=title)

    footer = '''</body>
</html>
'''

    tables = []
    for cmd in commands:
        tables.append('''
<table width="100%" border="0" cellpadding="0" cellspacing="1" class="ts">
<tr><th width="100px">命令名称：</th><td class="name">
<a name="{anchor}"></a>{cmd_name} {cmd_brief}
</td></tr><tr><th>命令功能：</th><td>
{cmd_func}
</td></tr><tr><th>参数说明：</th><td class="canshu"><pre>
{cmd_args}
</pre></td></tr><tr><th>返回值：</th><td class="fanhui">
{cmd_return}
</td></tr><tr><th>脚本示例：<br /><span class="red">此为安卓手机语法</span>
</th><td class="lizi"><pre>
{cmd_example}
</pre></td></tr></table>
'''.format(
            anchor=cmd["anchor"],
            cmd_name=cmd["name"],
            cmd_brief=cmd["brief"],
            cmd_func=cmd["func"],
            cmd_args=cmd["args"],
            cmd_return=cmd["return"],
            cmd_example=cmd["example"]
        ))

    return header + "".join(tables) + footer


localocr_commands = [
    {
        "anchor": "SetServer",
        "name": "LocalOCR.SetServer",
        "brief": "设置默认OCR服务端地址",
        "func": "设置后续调用使用的默认OCR服务端地址，例如 192.168.1.101:8080。",
        "args": "参数1: 服务端地址(字符串), 例如 \"192.168.1.101:8080\"",
        "return": "无返回值",
        "example": '''Import "LocalOCR.lua"
<span class="green">// 设置PC端OCR服务端地址</span>
LocalOCR.SetServer "192.168.1.101:8080"'''
    },
    {
        "anchor": "Ping",
        "name": "LocalOCR.Ping",
        "brief": "测试与服务端是否连通",
        "func": "发送一个测试请求到OCR服务端，判断手机与PC的网络是否通。",
        "args": "参数1: 服务端地址(字符串, 可省略, 使用SetServer默认值)",
        "return": "字符串: OK 表示连通; ERROR|错误信息 表示失败",
        "example": '''Import "LocalOCR.lua"
LocalOCR.SetServer "192.168.1.101:8080"
Dim ping = LocalOCR.Ping("")
TracePrint ping'''
    },
    {
        "anchor": "RecognizeStr",
        "name": "LocalOCR.RecognizeStr",
        "brief": "识别图片中所有文字(字符串版)",
        "func": "把整张图片发到PC服务端识别,返回所有文字和坐标信息,以分号分隔每条结果。",
        "args": "参数1: 服务端地址(字符串, 可省略)\n参数2: 图片完整路径(字符串), 例如 /sdcard/screen.png",
        "return": "字符串: text|置信度|x|y|w|h|中心x|中心y;text|...\n每条结果以 | 分隔字段, 多条结果以 ; 分隔",
        "example": '''Import "LocalOCR.lua"
Dim 图片路径 = "/sdcard/screen.png"
SnapShot 图片路径
Dim ret = LocalOCR.RecognizeStr("", 图片路径)
TracePrint ret
Dim lines = Split(ret, ";")
For i = 0 To UBound(lines)
    Dim cols = Split(lines(i), "|")
    If UBound(cols) >= 7 Then
        TracePrint cols(0) & " (" & cols(6) & "," & cols(7) & ")"
    End If
Next'''
    },
    {
        "anchor": "FindTextStr",
        "name": "LocalOCR.FindTextStr",
        "brief": "查找文字并返回点击坐标(字符串版)",
        "func": "在图片中搜索指定关键字,返回找到的中心坐标,用于点击。",
        "args": "参数1: 服务端地址(字符串, 可省略)\n参数2: 图片完整路径(字符串)\n参数3: 要查找的关键字(字符串)",
        "return": "字符串: x|y|置信度|文字\n未找到返回 ERROR|未找到 或 ERROR|错误信息",
        "example": '''Import "LocalOCR.lua"
Dim 图片路径 = "/sdcard/screen.png"
SnapShot 图片路径
Dim ret = LocalOCR.FindTextStr("", 图片路径, "开始")
If Left(ret, 5) <> "ERROR" Then
    Dim cols = Split(ret, "|")
    Touch cols(0), cols(1)
Else
    TracePrint "未找到"
End If'''
    },
    {
        "anchor": "Recognize",
        "name": "LocalOCR.Recognize",
        "brief": "识别图片中所有文字(表格版)",
        "func": "与RecognizeStr功能相同,但返回Lua表格,方便脚本内遍历。",
        "args": "参数1: 服务端地址(字符串, 可省略)\n参数2: 图片完整路径(字符串)",
        "return": "Lua表格数组,每个元素包含 text, confidence, x, y, w, h, center_x, center_y",
        "example": '''Import "LocalOCR.lua"
Dim 图片路径 = "/sdcard/screen.png"
SnapShot 图片路径
Dim results = LocalOCR.Recognize("", 图片路径)
For i = 0 To results.Length - 1
    TracePrint results(i)["text"] & " (" & results(i)["center_x"] & "," & results(i)["center_y"] & ")"
Next'''
    },
    {
        "anchor": "FindText",
        "name": "LocalOCR.FindText",
        "brief": "查找文字并返回坐标表格",
        "func": "与FindTextStr功能相同,但返回Lua表格,包含 found/x/y/confidence/text 字段。",
        "args": "参数1: 服务端地址(字符串, 可省略)\n参数2: 图片完整路径(字符串)\n参数3: 关键字(字符串)",
        "return": "Lua表格: {found=true/false, x=..., y=..., confidence=..., text=..., error=...}",
        "example": '''Import "LocalOCR.lua"
Dim 图片路径 = "/sdcard/screen.png"
SnapShot 图片路径
Dim ret = LocalOCR.FindText("", 图片路径, "开始")
If ret["found"] = True Then
    Touch ret["x"], ret["y"]
Else
    TracePrint ret["error"]
End If'''
    },
    {
        "anchor": "SetScreenshotPath",
        "name": "LocalOCR.SetScreenshotPath",
        "brief": "设置区域查找时临时截图路径",
        "func": "设置FindAt/FuzzyFindAt在区域内截图保存的临时文件路径。",
        "args": "参数1: 图片路径(字符串), 例如 /sdcard/LocalOCR_region.png",
        "return": "无",
        "example": '''Import "LocalOCR.lua"
LocalOCR.SetScreenshotPath "/sdcard/LocalOCR_region.png"'''
    },
    {
        "anchor": "ocr",
        "name": "LocalOCR.ocr",
        "brief": "区域内精确查找文字并可选点击",
        "func": "在指定屏幕区域内截图,精确查找目标文字。找到后可选自动点击,坐标保存在 LastFindX/LastFindY。",
        "args": "参数1-4: 区域左上角/右下角坐标(x1,y1,x2,y2)\n参数5: 要查找的文字(字符串)\n参数6: 是否点击(1=点击, 0=不点击)",
        "return": "true=找到, false=未找到。点击坐标写入 LocalOCR.LastFindX / LocalOCR.LastFindY",
        "example": '''Import "LocalOCR.lua"
LocalOCR.SetServer "192.168.1.101:8080"
If LocalOCR.ocr(100, 200, 400, 500, "开始", 1) = True Then
    TracePrint "点击了 " & LocalOCR.LastFindX & "," & LocalOCR.LastFindY
Else
    TracePrint "未找到"
End If'''
    },
    {
        "anchor": "ocra",
        "name": "LocalOCR.ocra",
        "brief": "区域内模糊查找文字并可选点击",
        "func": "在指定屏幕区域内截图,查找包含目标关键字的文字。找到后可选自动点击。",
        "args": "参数1-4: 区域坐标(x1,y1,x2,y2)\n参数5: 关键字(字符串)\n参数6: 是否点击(1=点击, 0=不点击)",
        "return": "true=找到, false=未找到。点击坐标写入 LocalOCR.LastFindX / LocalOCR.LastFindY",
        "example": '''Import "LocalOCR.lua"
If LocalOCR.ocra(100, 200, 400, 500, "开始", 0) = True Then
    TracePrint "找到在 " & LocalOCR.LastFindX & "," & LocalOCR.LastFindY
End If'''
    }
]

scanapi_commands = [
    {
        "anchor": "Scan",
        "name": "ScanApi.Scan",
        "brief": "扫描LuaAuxLib中的HTTP/文件命令",
        "func": "遍历按键精灵的LuaAuxLib库,列出包含 url/http/file/base64/encode 的命令名称,用于排查环境。",
        "args": "无参数",
        "return": "字符串,每行一个 命令名=类型",
        "example": '''Import "ScanApi.lua"
Dim list = ScanApi.Scan()
TracePrint list'''
    }
]

html_localocr = build_html("本地OCR插件", localocr_commands)
html_scanapi = build_html("ScanApi插件", scanapi_commands)

with open("LocalOCR.html", "w", encoding="gb2312") as f:
    f.write(html_localocr)

with open("ScanApi.html", "w", encoding="gb2312") as f:
    f.write(html_scanapi)

print("HTML files created")
