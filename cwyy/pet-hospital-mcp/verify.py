import json, urllib.request

BASE = "http://127.0.0.1:8081/mcp"

def call(method, params=None, id_val=1):
    payload = {"jsonrpc": "2.0", "id": id_val, "method": method}
    tool_name = None
    if params and "name" in params:
        tool_name = params["name"]
    name_header = tool_name or method
    full_params = dict(params) if params else {}
    full_params["_meta"] = {
        "io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientCapabilities": {},
        "io.modelcontextprotocol/clientInfo": {"name": "claude-desktop", "version": "1.0.0"}
    }
    payload["params"] = full_params
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        BASE, data=data,
        headers={
            "MCP-Protocol-Version": "2026-07-28",
            "Mcp-Method": method,
            "Mcp-Name": name_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode()}"}
    except Exception as e:
        return {"error": str(e)}

# Verify server/discover
print("=== server/discover ===")
r = call("server/discover", id_val=1)
print(json.dumps(r, indent=2, ensure_ascii=False))

# Verify tools/list
print("\n=== tools/list ===")
r = call("tools/list", id_val=2)
tools = r["result"]["tools"]
print(f"Tools found: {[t['name'] for t in tools]}")
print(f"ttlMs: {r['result'].get('ttlMs')}, cacheScope: {r['result'].get('cacheScope')}")

# Verify list_pets works
print("\n=== list_pets ===")
r = call("tools/call", {"name": "list_pets", "arguments": {"pageSize": 2}}, id_val=3)
text = r["result"]["content"][0]["text"]
data = json.loads(text)
print(f"Total pets: {len(data['data']['items'])}")
print(f"First pet: {data['data']['items'][0]['name']} ({data['data']['items'][0]['species']})")
