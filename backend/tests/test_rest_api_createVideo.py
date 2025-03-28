import io
import os
import pytest
from aiohttp import web, FormData
from unittest.mock import AsyncMock, MagicMock, Mock
import rest_api
from config import settings
from jose import jwt
@pytest.fixture
async def client(aiohttp_client):
    """建立 aiohttp 應用並註冊 API 路由"""
    app = web.Application()
    app.router.add_post("/api/register", rest_api.register)
    # 加入 create_video API 路由
    app.router.add_post("/api/videos", rest_api.create_video)
    client = await aiohttp_client(app)
    return client




# 測試 API /api/videos - 當缺少授權標頭時，應回傳 401
@pytest.mark.asyncio
async def test_create_video_missing_authorization(mocker, client):
    """測試 API /api/videos - 缺少授權標頭時的回應"""
    # Arrange: 準備包含 title 與 file 欄位的 multipart form-data
    data = FormData()
    data.add_field("title", "test.mp4")
    data.add_field("file", io.BytesIO(b"fake content"),
                   filename="test.mp4", content_type="video/mp4")
    # Act: 發送不包含授權標頭的請求
    async with client.post("/api/videos", data=data) as resp:
        # Assert: 應回傳 401 且提示 "Missing or invalid token"
        assert resp.status == 401
        text = await resp.text()
        assert "Missing or invalid token" in text

# 測試 API /api/videos - 當授權標頭格式不正確(非 Bearer 格式)時，應回傳 401
@pytest.mark.asyncio
async def test_create_video_invalid_auth_header_format(mocker, client):
    """測試 API /api/videos - 授權標頭格式不正確時的錯誤處理"""
    # Arrange
    data = FormData()
    data.add_field("title", "test.mp4")
    data.add_field("file", io.BytesIO(b"fake content"),
                   filename="test.mp4", content_type="video/mp4")
    headers = {"Authorization": "Token sometoken"}  # 非 Bearer 格式
    # Act
    async with client.post("/api/videos", data=data, headers=headers) as resp:
        # Assert
        assert resp.status == 401
        text = await resp.text()
        assert "Missing or invalid token" in text

# 測試 API /api/videos - 當提供無效的 Token 時，應回傳 401
@pytest.mark.asyncio
async def test_create_video_invalid_token(mocker, client):
    """測試 API /api/videos - 提供無效 Token 時的回應"""
    # Arrange
    data = FormData()
    data.add_field("title", "test.mp4")
    data.add_field("file", io.BytesIO(b"fake content"),
                   filename="test.mp4", content_type="video/mp4")
    headers = {"Authorization": "Bearer invalidtoken"}
    # 將 jose.jwt.decode 模擬為拋出例外
    mocker.patch("jose.jwt.decode", side_effect=Exception("Invalid token"))
    # Act
    async with client.post("/api/videos", data=data, headers=headers) as resp:
        # Assert
        assert resp.status == 401
        text = await resp.text()
        assert "Invalid token" in text

# 測試 API /api/videos - 當僅上傳 title 而未上傳 file 時，應回傳 500 (目前行為)
@pytest.mark.asyncio
async def test_create_video_no_video_file(mocker, client):
    """測試 API /api/videos - 未上傳影片檔時的回應狀態"""
    # Arrange: 僅提供 title 欄位，不含 file 欄位
    from aiohttp import FormData
    import io
    data = FormData()
    data.add_field("title", "test.mp4")
    # 模擬 jwt.decode 回傳有效 payload
    valid_payload = {"sub": "507f1f77bcf86cd799439012"}
    mocker.patch("jose.jwt.decode", return_value=valid_payload)
    headers = {"Authorization": "Bearer validtoken"}
    # Act
    async with client.post("/api/videos", data=data, headers=headers) as resp:
        # Assert: 目前 API 回傳 500，訊息包含 "multipart/* content type expected"
        assert resp.status == 500
        text = await resp.text()
        assert "multipart/* content type expected" in text

# 測試 API /api/videos - 正常上傳影片時，應回傳正確的 JSON 結果
@pytest.mark.asyncio
async def test_create_video_success(mocker, client, tmp_path):
    """測試 API /api/videos - 上傳影片成功時的正確回應"""
    # Arrange: 模擬 jwt.decode 返回有效使用者資訊
    valid_payload = {"sub": "507f1f77bcf86cd799439012"}
    mocker.patch("jose.jwt.decode", return_value=valid_payload)
    # 建立包含 title 與 file 欄位的 multipart form-data
    file_content = b"fake video data"
    data = FormData()
    data.add_field("title", "test.mp4")
    data.add_field("file", io.BytesIO(file_content),
                   filename="test.mp4", content_type="video/mp4")
    # 模擬資料庫操作，並模擬插入結果
    mock_db = AsyncMock()
    mock_db.videos = AsyncMock()
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = "67d42da7c69a91285466b1db"
    mock_db.videos.insert_one = AsyncMock(return_value=mock_insert_result)
    mocker.patch("rest_api.get_database", return_value=mock_db)
    # 為避免實際檔案寫入，模擬 os.makedirs 與 open
    mocker.patch("rest_api.os.makedirs")
    m_open = mocker.patch("rest_api.open", mocker.mock_open())
    headers = {"Authorization": "Bearer validtoken"}
    # Act
    async with client.post("/api/videos", data=data, headers=headers) as resp:
        # Assert
        assert resp.status == 200
        json_response = await resp.json()
        expected = {
            "id": "67d42da7c69a91285466b1db",
            "title": "test.mp4",
            # 注意: 回傳的 file_path 為檔案名稱，故只取最後一節
            "file_path": m_open.call_args[0][0].split(os.sep)[-1]
        }
        assert json_response == expected