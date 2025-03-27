# test_api.py (測試檔案)
import pytest
from aiohttp import web
import asyncio
from aiohttp.test_utils import TestClient, AioHTTPTestCase

import rest_api
import database

@pytest.fixture
async def client(aiohttp_client):
    """Fixture: 建立 aiohttp 應用程式並註冊路由"""
    app = web.Application()
    app.router.add_post("/api/register", rest_api.register)
    client = await aiohttp_client(app)
    return client

@pytest.mark.asyncio
async def test_registerAPI_database_failed(mocker, client):
    """測試 API /api/register 當資料庫查詢失敗時，應回傳 400"""
    # 使用 mock 來模擬 get_user_from_db 函式
    mocker.patch("database.get_database", return_value=None)

    # 假設這是你的測試用戶資料
    params = {
        "email": "existing@example.com",
        "password": "123456"
    }

    # 使用 aiohttp 測試客戶端傳送 POST request
    # client = await aiohttp_client(app)
    async with client.post("/api/register", json=params) as resp:
        # 斷言返回狀態碼是 400
        assert resp.status == 500
        assert "Database connection failed" in await resp.text()
