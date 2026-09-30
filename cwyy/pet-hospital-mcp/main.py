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
    if q is not None:
        params["q"] = q
    if name is not None:
        params["name"] = name
    if species is not None:
        params["species"] = species
    if doctor is not None:
        params["doctor"] = doctor
    if disease is not None:
        params["disease"] = disease
    if status is not None:
        params["status"] = status
    if ownerName is not None:
        params["ownerName"] = ownerName
    if ownerPhone is not None:
        params["ownerPhone"] = ownerPhone
    if min is not None:
        params["min"] = min
    if max is not None:
        params["max"] = max
    if sortBy is not None:
        params["sortBy"] = sortBy
    if order is not None:
        params["order"] = order
    if page is not None:
        params["page"] = page
    if pageSize is not None:
        params["pageSize"] = pageSize

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
