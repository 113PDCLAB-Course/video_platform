import pytest
from aiohttp import web
from unittest.mock import AsyncMock, MagicMock, Mock
import rest_api

@pytest.fixture
async def client(aiohttp_client):
    """Fixture: 建立 aiohttp 應用程式並註冊路由"""
    app = web.Application()
    app.router.add_delete("/api/videos/{video_id}", rest_api.delete_video)
    client = await aiohttp_client(app)
    return client

@pytest.mark.asyncio
async def test_delete_video_invalid_id(client):
    """DV-001: 無效視頻ID格式測試"""
    headers = {"Authorization": "Bearer test_token"}
    async with client.delete("/api/videos/invalid_id", headers=headers) as resp:
        assert resp.status == 400
        assert "Invalid video ID format" in await resp.text()

@pytest.mark.asyncio
async def test_delete_video_not_found(mocker, client):
    """DV-002: 有效視頻ID但影片不存在資料庫測試"""
    mock_db = AsyncMock()
    mock_db.videos = AsyncMock()
    mock_db.videos.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
    mocker.patch("rest_api.get_database", return_value=mock_db)
    """測試 API /api/videos/{video_id} 當影片不存在時，應回傳 404"""
    headers = {"Authorization": "Bearer test_token"}  # 添加授權標頭
    async with client.delete("/api/videos/65d123456789abcd12345678", headers=headers) as resp:
        assert resp.status == 404
        assert "Video not found" in await resp.text()

@pytest.mark.asyncio
async def test_delete_video_database_error(mocker, client):
    """DV-003: 資料庫紀錄刪除錯誤測試"""
    mock_db = AsyncMock()
    mock_db.videos = AsyncMock()
    mock_db.videos.delete_one = AsyncMock(side_effect=Exception("Database error"))
    mocker.patch("rest_api.get_database", return_value=mock_db)
    """測試 API /api/videos/{video_id} 當資料庫錯誤時，應回傳 500"""
    async with client.delete("/api/videos/65d123456789abcd12345678", headers={"Authorization": "Bearer test_token"}) as resp:
        assert resp.status == 500
        assert "Database error" in await resp.text()
    

@pytest.mark.asyncio
async def test_delete_video_success(mocker, client):
    """DV-004: 視頻成功刪除測試"""
    mock_db = AsyncMock()
    mock_db.videos = AsyncMock()
    mock_db.videos.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    mocker.patch("rest_api.get_database", return_value=mock_db)
    """測試 API /api/videos/{video_id} 成功刪除影片時，應回傳 200"""
    headers = {"Authorization": "Bearer test_token"}
    async with client.delete("/api/videos/65d123456789abcd12345678", headers=headers) as resp:
        assert resp.status == 200
        assert "Video deleted successfully" in await resp.text()
