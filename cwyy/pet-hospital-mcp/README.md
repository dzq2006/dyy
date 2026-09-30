# Pet Hospital MCP Server — 开发提示词（Python 版）

## 项目目标

将宠物医院 REST API 封装为 MCP Server，使其他 AI Agent 可以通过 MCP Client 消费宠物医院数据。

**第一版只实现 `list_pets` 功能**：列出宠物档案，支持各种参数筛选。

---

## 已完成验证的代码结构

```
pet-hospital-mcp/
├── pyproject.toml     # 依赖声明 (mcp>=2.0.0, httpx>=0.28.0)
├── client.py          # HTTP 客户端 (httpx.AsyncClient 封装 REST API 调用)
└── main.py            # MCPServer 创建、list_pets Tool 注册、Streamable HTTP 启动
```

---

## 技术栈（已验证可用）

- **Python** 3.13.7（3.10+ 即可）
- **MCP SDK**：`mcp` v2.2.0（支持 2026-07-28 协议）
  ```bash
  pip install "mcp[cli]" httpx
  ```
- **HTTP 客户端**：`httpx` 0.28.1（已安装）
- **传输**：Streamable HTTP，`stateless_http=True`，`json_response=True`

---

## 运行方式

```bash
# 前提：确保 pethospital.exe 已启动（REST API 在 :8080）
# 启动 MCP Server
python main.py

# MCP Server 监听 http://127.0.0.1:8081/mcp
```

---

## MCP 协议 2026-07-28 核心约束（已遵循）

1. **无状态**：无 `initialize`/`notifications/initialized` 握手
2. **`server/discover`**：SDK 自动实现，返回 `supportedVersions: ["2026-07-28"]`
3. **Streamable HTTP**：每个请求携带 `Mcp-Method`、`Mcp-Name`、`MCP-Protocol-Version` 头
4. **`stateless_http=True`**：每个请求创建全新传输，无 session 追踪
5. **`json_response=True`**：JSON 响应而非 SSE 流，客户端需 `Accept: application/json`
6. **`_meta` 信封**：请求 `params._meta` 必须包含 `io.modelcontextprotocol/protocolVersion` 和 `io.modelcontextprotocol/clientCapabilities`
7. **`resultType: "complete"`**：工具调用结果正确返回
8. **`_meta.serverInfo`**：每个响应包含服务器信息
9. **`ttlMs` / `cacheScope`**：`tools/list` 结果自动携带
10. **不要使用**：Roots、Sampling、Logging（已弃用）

---

## 客户端调用格式

MCP Client 调用时，请求体结构：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "list_pets",
    "arguments": {"species": "犬"},
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {},
      "io.modelcontextprotocol/clientInfo": {"name": "my-client", "version": "1.0.0"}
    }
  }
}
```

HTTP 头必须包含：
- `MCP-Protocol-Version: 2026-07-28`
- `Mcp-Method: tools/call`
- `Mcp-Name: list_pets`
- `Content-Type: application/json`
- `Accept: application/json`

---

## 代码实现

### `client.py`

```python
import httpx
import os
import logging

logger = logging.getLogger(__name__)

class PetHospitalClient:
    """HTTP 客户端，封装对宠物医院 REST API 的调用。"""

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.environ.get(
            "PET_HOSPITAL_API_URL", "http://127.0.0.1:8080"
        )
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def list_pets(self, params: dict) -> dict:
        """调用 GET /api/v1/pets，返回 REST API 原始响应。"""
        try:
            response = await self._client.get("/api/v1/pets", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"REST API call failed: {e}")
            return {"code": 500, "message": f"API 调用失败: {e}", "data": None}

    async def close(self):
        await self._client.aclose()
```

### `main.py`

```python
from mcp.server import MCPServer
from client import PetHospitalClient
import os
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = MCPServer("pet-hospital", version="1.0.0")

@mcp.tool()
async def list_pets(
    q: str | None = None,
    name: str | None = None,
    species: str | None = None,
    doctor: str | None = None,
    disease: str | None = None,
    status: str | None = None,
    ownerName: str | None = None,
    ownerPhone: str | None = None,
    min: float | None = None,
    max: float | None = None,
    sortBy: str | None = None,
    order: str | None = None,
    page: int | None = None,
    pageSize: int | None = None,
) -> dict:
    """列出宠物档案，支持多种筛选条件。所有参数均为可选，不传则返回全部宠物。

    支持的筛选维度：
    - q: 全文检索（跨字段，空格分词 AND，含病历全文）
    - name/species/doctor/disease/status: 按对应字段精确筛选
    - ownerName/ownerPhone: 按主人信息筛选
    - min/max: 按总花费区间筛选
    - sortBy/order: 排序（order 为 asc 或 desc）
    - page/pageSize: 分页
    """
    params = {}
    if q is not None: params["q"] = q
    if name is not None: params["name"] = name
    if species is not None: params["species"] = species
    if doctor is not None: params["doctor"] = doctor
    if disease is not None: params["disease"] = disease
    if status is not None: params["status"] = status
    if ownerName is not None: params["ownerName"] = ownerName
    if ownerPhone is not None: params["ownerPhone"] = ownerPhone
    if min is not None: params["min"] = min
    if max is not None: params["max"] = max
    if sortBy is not None: params["sortBy"] = sortBy
    if order is not None: params["order"] = order
    if page is not None: params["page"] = page
    if pageSize is not None: params["pageSize"] = pageSize

    client = PetHospitalClient()
    try:
        result = await client.list_pets(params)
        return result
    finally:
        await client.close()

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8081,
        stateless_http=True,
        json_response=True,
    )
```

### `pyproject.toml`

```toml
[project]
name = "pet-hospital-mcp"
version = "1.0.0"
description = "MCP Server for Pet Hospital REST API (2026-07-28 protocol)"
requires-python = ">=3.10"
dependencies = [
    "mcp[cli]>=2.0.0",
    "httpx>=0.28.0",
]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"
```

---

## 验证结果

已通过实际调用验证：

| 测试 | 结果 |
|------|------|
| `server/discover` | 返回 `supportedVersions: ["2026-07-28"]`, serverInfo `{name: "pet-hospital", version: "1.0.0"}` |
| `tools/list` | 返回 `list_pets` tool 及完整 `inputSchema`（14个参数），`ttlMs` 和 `cacheScope` 自动携带 |
| `list_pets` (无参数) | 返回全部宠物数据，`resultType: "complete"` |
| `list_pets` (species=犬) | 返回筛选后的犬类宠物 |
| `_meta.serverInfo` | 每个响应都包含 |

---

## 待扩展功能（后续开发）

- `get_pet` — 按 ID 查询
- `create_pet` / `update_pet` / `delete_pet` — CRUD
- `add_record` / `add_charge` — 病历和收费
- `get_stats` — 统计
- `search_pets` — 全文检索
- `batch_create_pets` / `batch_delete_pets` — 批量操作
- `export_data` — 导出
- `compact_db` / `seed_data` — 管理
- `get_meta` — 枚举字典
- 多 Tool 支持后优化 HTTP 客户端复用

---

## 说明

- 本 MCP Server 无鉴权，仅监听 `127.0.0.1`，适合本地/内网使用
- REST API 地址默认 `http://127.0.0.1:8080`，可通过环境变量 `PET_HOSPITAL_API_URL` 修改
- MCP Server 端口默认 `8081`，可通过命令行参数修改
- 中文数据存储在 `data/pet.db` 中，MCP 返回的 JSON 包含完整宠物信息
