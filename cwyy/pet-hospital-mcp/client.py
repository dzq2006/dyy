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
