import pytest
from aiohttp import web
from unittest.mock import AsyncMock, MagicMock, Mock
import rest_api

@pytest.fixture
async def client(aiohttp_client):
    """Fixture: 建立 aiohttp 應用程式並註冊路由"""
    # Arrange
    app = web.Application()
    app.router.add_post("/api/register", rest_api.register)
    client = await aiohttp_client(app)
    return client

@pytest.mark.asyncio
async def test_registerAPI_database_failed(mocker, client):
    """測試 API /api/register 當資料庫壞掉時，應回傳 500"""
    # Arrange
    # 使用 mock 來模擬 get_user_from_db 函式
    mocker.patch("rest_api.get_database", return_value=None)

    # 假設這是你的測試用戶資料
    params = {
        "email": "existing@example.com",
        "password": "123456"
    }

    # Act 
    # Assert
    # 使用 aiohttp 測試客戶端傳送 POST request
    async with client.post("/api/register", json=params) as resp:
        # 斷言返回狀態碼是 400
        assert resp.status == 500
        assert "Database connection failed" in await resp.text()

@pytest.mark.asyncio
async def test_registerAPI_invalid_parameter(mocker, client):
    """測試 API /api/register 當給不合法參數，應回傳 400"""
    # Arrange
    # 使用 mock 來模擬 get_user_from_db 函式
    mock_db = MagicMock()
    mocker.patch("rest_api.get_database", return_value=mock_db)

    # 假設這是你的測試用戶資料
    params = None

    # Act 
    # Assert
    # 使用 aiohttp 測試客戶端傳送 POST request
    async with client.post("/api/register", json=params) as resp:
        # 斷言返回狀態碼是 400
        assert resp.status == 400
        assert "Invalid request data" in await resp.text()

@pytest.mark.asyncio
async def test_registerAPI_parameter_failed(mocker, client):
    """測試 API /api/register 提供的參數缺少時，應回傳 400"""
    # Arrange
    # 使用 mock 來模擬 get_user_from_db 函式
    mock_db = MagicMock()
    mocker.patch("rest_api.get_database", return_value=mock_db)

    # 假設這是你的測試用戶資料
    params = {
        "email": "existing@example.com",
        "password": "123456"
    }

    # Act 
    # Arrange
    # 使用 aiohttp 測試客戶端傳送 POST request
    async with client.post("/api/register", json=params) as resp:
        # 斷言返回狀態碼是 400
        assert resp.status == 400
        assert "Missing required fields:" in await resp.text()

@pytest.mark.asyncio
async def test_registerAPI_email_registered(mocker, client):
    """測試 API /api/register email 被註冊，應回傳 400"""

    # Arrange 
    # 使用 mock 來模擬 get_user_from_db 函式
    # 假設這是你的測試用戶資料
    params = {
        "username":"example",
        "email": "existing@example.com",
        "password": "123456"
    }

    # 有用到 async 函式的時候必須要用 Asyncmock 
    mock_db = AsyncMock()
    mock_db.users = AsyncMock()
    mock_db.users.find_one = AsyncMock(return_value={
        "username":"example",
        "password":"123456",
        "email":"existing@example.com"
    })
    mocker.patch("rest_api.get_database", return_value=mock_db)

    # 使用 aiohttp 測試客戶端傳送 POST request
    async with client.post("/api/register", json=params) as resp:
        # 斷言返回狀態碼是 400
        assert resp.status == 400
        assert "Email already registered" in await resp.text()

@pytest.mark.asyncio
async def test_registerAPI_createUser_Failed(mocker, client):
    """測試 API /api/register 在新增使用者時回傳錯誤，應回傳 400"""

    # Arrange 
    # 使用 mock 來模擬 get_user_from_db 函式
    # 假設這是你的測試用戶資料
    params = {
        "username":"example",
        "email": "existing@example.com",
        "password": "123456"
    }

    # 有用到 async 函式的時候必須要用 Asyncmock 
    mock_db = AsyncMock()
    mock_db.users = AsyncMock()
    mock_db.users.find_one = AsyncMock(return_value = None)
    
    mocker.patch("rest_api.get_database", return_value=mock_db)
    mocker.patch("rest_api.get_password_hash", side_effect=Exception("Error"))

    # Act
    # 使用 aiohttp 測試客戶端傳送 POST request
    async with client.post("/api/register", json=params) as resp:
        # 斷言返回狀態碼是 400
        assert resp.status == 400
        assert "Invalid user data" in await resp.text()

@pytest.mark.asyncio
async def test_registerAPI_InsertDatabase_Failed(mocker, client):
    """測試 API /api/register 在插入資料庫時發生錯誤，應回傳 400"""

    # Arrange 
    # 使用 mock 來模擬 get_user_from_db 函式
    # 假設這是你的測試用戶資料
    params = {
        "username":"example",
        "email": "existing@example.com",
        "password": "123456"
    }

    # 有用到 async 函式的時候必須要用 Asyncmock 
    mock_db = AsyncMock()
    mock_db.users = AsyncMock()
    mock_db.users.find_one = AsyncMock(return_value = None)
    mock_db.users.insert_one = AsyncMock(side_effect=Exception("Error"))
    
    mocker.patch("rest_api.get_database", return_value=mock_db)
    mocker.patch("rest_api.get_password_hash", return_value="123456")

    # Act 
    # 使用 aiohttp 測試客戶端傳送 POST request
    async with client.post("/api/register", json=params) as resp:
        # 斷言返回狀態碼是 400
        assert resp.status == 500
        assert "Database error:" in await resp.text()


@pytest.mark.asyncio
async def test_registerAPI_Success(mocker, client):
    """測試 API /api/register 在新增使用者時成功，應回傳 200"""

    # Arrange 
    # 使用 mock 來模擬 get_user_from_db 函式
    # 假設這是你的測試用戶資料
    params = {
        "username":"example",
        "email": "existing@example.com",
        "password": "123456"
    }
    results = {
        "id": '67d427d6a754205dd6ab92fb',
        "username": "example",
        "email": "existing@example.com"
    }

    # 有用到 async 函式的時候必須要用 Asyncmock 
    mock_db = AsyncMock()
    mock_db.users = AsyncMock()
    mock_db.users.find_one = AsyncMock(return_value = None)
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = "67d427d6a754205dd6ab92fb"
    mock_db.users.insert_one = AsyncMock(return_value=mock_insert_result)
    
    mocker.patch("rest_api.get_database", return_value=mock_db)
    mocker.patch("rest_api.get_password_hash", return_value="123456")

    # Act 
    # 使用 aiohttp 測試客戶端傳送 POST request
    async with client.post("/api/register", json=params) as resp:
        # 斷言返回狀態碼是 400
        assert resp.status == 200
        assert results == await resp.json()