local api = {}
QMPlugin = api

function api.Scan()
    local result = ""
    for name, value in pairs(LuaAuxLib) do
        local lower = string.lower(tostring(name))
        if string.find(lower, "url") or string.find(lower, "http") or string.find(lower, "file") or string.find(lower, "base64") or string.find(lower, "encode") then
            result = result .. tostring(name) .. "=" .. type(value) .. "\n"
        end
    end
    return result
end
