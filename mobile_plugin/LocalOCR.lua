-- LocalOCR.lua
-- A lightweight plugin for Anjian mobile assistant.
-- It sends a screenshot as base64 to the local OCR HTTP server and parses the simple text response.
--
-- Usage:
--   Import "LocalOCR.lua"
--   LocalOCR.SetServer "192.168.1.100:8080"
--
--   Dim ret = LocalOCR.Recognize("192.168.1.100:8080", "/sdcard/screen.png")
--   If ret <> "" Then
--       For i = 0 To ret.Length - 1
--           TracePrint ret(i)["text"] & " (" & ret(i)["center_x"] & "," & ret(i)["center_y"] & ")"
--       Next
--   End If
--
--   Dim click = LocalOCR.FindText("192.168.1.100:8080", "/sdcard/screen.png", "Adventure")
--   If click["found"] = True Then
--       Touch click["x"], click["y"]
--   End If

local LocalOCR = {}
local _priv = {}
QMPlugin = LocalOCR

_priv.default_server = "192.168.1.100:8080"
_priv.b64chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

function LocalOCR.SetServer(host_port)
    _priv.default_server = tostring(host_port)
end

-- ============================================================
-- Base64 encoder, only uses math (compatible with Lua 5.1/5.2)
-- ============================================================
function _priv.base64_encode(data)
    local b64 = _priv.b64chars
    local out = {}
    local n = #data
    local i = 1
    while i <= n do
        local a = string.byte(data, i)
        local b = string.byte(data, i + 1)
        local c = string.byte(data, i + 2)

        local b1 = math.floor(a / 4)
        local b2 = ((a % 4) * 16) + math.floor((b or 0) / 16)
        local b3 = b and (((b % 16) * 4) + math.floor((c or 0) / 64)) or 64
        local b4 = c and (c % 64) or 64

        table.insert(out, string.sub(b64, b1 + 1, b1 + 1))
        table.insert(out, string.sub(b64, b2 + 1, b2 + 1))
        table.insert(out, string.sub(b64, b3 + 1, b3 + 1))
        table.insert(out, string.sub(b64, b4 + 1, b4 + 1))

        i = i + 3
    end
    return table.concat(out)
end

-- ============================================================
-- File read
-- ============================================================
function _priv.read_file(path)
    if not io then
        return nil, "io library not available"
    end
    local f, err = io.open(path, "rb")
    if not f then
        return nil, "open file failed: " .. tostring(err)
    end
    local data = f:read("*all")
    f:close()
    if not data or #data == 0 then
        return nil, "empty file"
    end
    return data
end

-- ============================================================
-- String utilities
-- ============================================================
function _priv.split(str, sep)
    local t = {}
    if str == nil or str == "" then
        return t
    end
    local pattern = "([^" .. sep .. "]+)"
    for s in string.gmatch(str, pattern) do
        table.insert(t, s)
    end
    return t
end

function _priv.split_lines(str)
    local t = {}
    if str == nil or str == "" then
        return t
    end
    for s in string.gmatch(str, "[^\r\n]+") do
        table.insert(t, s)
    end
    return t
end

function _priv.json_escape(s)
    s = string.gsub(s, "\\", "\\\\")
    s = string.gsub(s, "\"", "\\\"")
    s = string.gsub(s, "\n", "\\n")
    s = string.gsub(s, "\r", "\\r")
    s = string.gsub(s, "\t", "\\t")
    return s
end

-- ============================================================
-- HTTP POST command detection
-- ============================================================
function _priv.find_http_post()
    if type(LuaAuxLib) ~= "table" then
        return nil, "LuaAuxLib not found"
    end

    local names = {
        "URL_OperationPost",
        "Url_OperationPost",
        "url_OperationPost",
        "Url.Post",
        "URL.Post",
        "url.Post",
        "Url.HttpPost",
        "url.HttpPost",
        "URL.HttpPost",
        "Url_HttpPost",
        "Http.Post",
        "http.Post",
        "HttpPost",
        "Http_Post",
        "HTTPPost",
        "HTTP_Post",
        "PostHttp",
        "Post_Http",
    }
    for _, name in ipairs(names) do
        local f = LuaAuxLib[name]
        if type(f) == "function" then
            return f, name
        end
    end

    for name, value in pairs(LuaAuxLib) do
        local lower = string.lower(tostring(name))
        if string.find(lower, "post")
           and (string.find(lower, "http")
                or string.find(lower, "url")
                or string.find(lower, "operation")) then
            if type(value) == "function" then
                return value, name
            end
        end
    end

    return nil, "HTTP POST command not found"
end

function _priv.extract_body(resp)
    if type(resp) ~= "string" then
        return ""
    end
    -- Some HTTP commands return raw HTTP response with headers.
    if string.sub(resp, 1, 4) == "HTTP" then
        local idx = string.find(resp, "\r\n\r\n", 1, true)
        if idx then
            return string.sub(resp, idx + 4)
        end
        idx = string.find(resp, "\n\n", 1, true)
        if idx then
            return string.sub(resp, idx + 2)
        end
    end
    return resp
end

function _priv.http_post(url, body, header, timeout)
    timeout = timeout or 30
    local f, name = _priv.find_http_post()
    if not f then
        return nil, name
    end

    local last_err = ""
    local function use_value(v)
        if v == nil then
            return nil
        end
        if type(v) == "table" then
            if v.body then
                return _priv.extract_body(tostring(v.body))
            end
            return _priv.extract_body(tostring(v[1]) or "")
        end
        if type(v) == "string" and v ~= "" then
            return _priv.extract_body(v)
        end
        if type(v) == "number" or type(v) == "boolean" then
            -- Some commands return status code first; ignore single number/boolean
            return nil
        end
        return nil
    end

    local function handle_results(ok, r1, r2, r3)
        if not ok then
            last_err = tostring(r1)
            return nil
        end
        if r1 == false then
            last_err = tostring(r2 or "request failed")
            return nil
        end
        for _, v in ipairs({r1, r2, r3}) do
            local b = use_value(v)
            if b then
                return b
            end
        end
        last_err = "server returned empty"
        return nil
    end

    -- Table-based commands (Url.HttpPost etc.)
    if name == "Url.HttpPost"
       or name == "url.HttpPost"
       or name == "URL.HttpPost"
       or name == "Url_HttpPost"
       or name == "Http.Post"
       or name == "http.Post" then
        local req = { url = url, data = body, code = "UTF-8" }
        if header and header ~= "" then
            local k, v = string.match(header, "([^:]+):%s*(.+)")
            if k then
                req.header = { [k] = v }
            end
        end
        if timeout then
            req.timeout = timeout
        end
        local r = handle_results(pcall(f, req))
        if r then
            return r
        end
        return nil, "HTTP POST failed: " .. last_err
    end

    -- Positional without header (Url.Post)
    if name == "Url.Post"
       or name == "url.Post"
       or name == "URL.Post" then
        local r = handle_results(pcall(f, url, body, timeout))
        if r then
            return r
        end
        r = handle_results(pcall(f, url, body))
        if r then
            return r
        end
        return nil, "HTTP POST failed: " .. last_err
    end

    -- Positional with header (URL_OperationPost, PostHttp, HttpPost, etc.)
    local r = handle_results(pcall(f, url, body, timeout, header))
    if r then
        return r
    end
    r = handle_results(pcall(f, url, body, timeout))
    if r then
        return r
    end
    r = handle_results(pcall(f, url, body))
    if r then
        return r
    end

    return nil, "HTTP POST failed: " .. last_err
end

-- ============================================================
-- Public API
-- ============================================================
function LocalOCR.Recognize(host_port, image_path)
    local server = host_port or _priv.default_server

    local data, err = _priv.read_file(image_path)
    if not data then
        return nil, err
    end

    local b64 = _priv.base64_encode(data)
    local body = '{"image":"' .. b64 .. '"}'
    local header = "Content-Type: application/json"

    local resp, err2 = _priv.http_post("http://" .. server .. "/ocr_simple", body, header, 30)
    if not resp then
        return nil, err2
    end

    local lines = _priv.split_lines(resp)
    if #lines == 0 then
        return nil, "empty response"
    end

    local head = _priv.split(lines[1], "\t")
    if head[1] ~= "OK" then
        return nil, head[2] or "recognition failed"
    end

    local out = {}
    for i = 2, #lines do
        local cols = _priv.split(lines[i], "\t")
        table.insert(out, {
            text = cols[1] or "",
            confidence = tonumber(cols[2]) or 0,
            x = tonumber(cols[3]) or 0,
            y = tonumber(cols[4]) or 0,
            w = tonumber(cols[5]) or 0,
            h = tonumber(cols[6]) or 0,
            center_x = tonumber(cols[7]) or 0,
            center_y = tonumber(cols[8]) or 0,
        })
    end

    return out
end

function LocalOCR.FindText(host_port, image_path, keyword)
    local server = host_port or _priv.default_server
    local out = { found = false }

    local data, err = _priv.read_file(image_path)
    if not data then
        out.error = err
        return out
    end

    local b64 = _priv.base64_encode(data)
    local safe_keyword = _priv.json_escape(keyword)
    local body = '{"image":"' .. b64 .. '","keyword":"' .. safe_keyword .. '"}'
    local header = "Content-Type: application/json"

    local resp, err2 = _priv.http_post("http://" .. server .. "/click_text_simple", body, header, 30)
    if not resp then
        out.error = err2
        return out
    end

    local lines = _priv.split_lines(resp)
    if #lines == 0 then
        out.error = "empty response"
        return out
    end

    local cols = _priv.split(lines[1], "\t")
    if cols[1] == "NOT_FOUND" then
        out.error = "text not found"
        return out
    end
    if cols[1] == "ERROR" then
        out.error = cols[2] or "server error"
        return out
    end

    out.found = true
    out.x = tonumber(cols[1]) or 0
    out.y = tonumber(cols[2]) or 0
    out.confidence = tonumber(cols[3]) or 0
    out.text = cols[4] or ""
    return out
end

-- ============================================================
-- String versions for easier use from MQ/VB-like scripts
-- ============================================================
function LocalOCR.RecognizeStr(host_port, image_path)
    local results, err = LocalOCR.Recognize(host_port, image_path)
    if not results then
        return "ERROR|" .. tostring(err)
    end
    local parts = {}
    for _, r in ipairs(results) do
        table.insert(parts,
            tostring(r.text) .. "|" ..
            tostring(r.confidence) .. "|" ..
            tostring(r.x) .. "|" ..
            tostring(r.y) .. "|" ..
            tostring(r.w) .. "|" ..
            tostring(r.h) .. "|" ..
            tostring(r.center_x) .. "|" ..
            tostring(r.center_y)
        )
    end
    return table.concat(parts, ";")
end

function LocalOCR.FindTextStr(host_port, image_path, keyword)
    local r = LocalOCR.FindText(host_port, image_path, keyword)
    if not r.found then
        return "ERROR|" .. tostring(r.error)
    end
    return tostring(r.x) .. "|" .. tostring(r.y) .. "|" .. tostring(r.confidence) .. "|" .. tostring(r.text)
end

function LocalOCR.Ping(host_port)
    local server = host_port or _priv.default_server
    local body = ""
    local header = "Content-Type: application/json"
    local resp, err = _priv.http_post("http://" .. server .. "/ping", body, header, 10)
    if not resp then
        return "ERROR|" .. tostring(err)
    end
    if string.find(resp, "pong") then
        return "OK"
    end
    return "ERROR|unexpected response: " .. tostring(resp)
end
