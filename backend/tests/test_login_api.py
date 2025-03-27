from unittest import mock

import pytest
from aiohttp import web
from bson import ObjectId

from rest_api import login


@pytest.fixture
def user_id():
    return ObjectId()


@pytest.fixture
def test_user(user_id):
    return {
        "_id": user_id,
        "email": "example@gmail.com",
        "password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewTO.GA4eSJ3AqdO",  # hashed "password"
        "username": "testuser",
    }


@pytest.fixture
def mock_db():
    with mock.patch("rest_api.get_database") as mock_db:
        # 創建 users collection mock
        mock_users = mock.AsyncMock()

        # 設置數據庫結構
        mock_db.return_value = mock.MagicMock()
        mock_db.return_value.users = mock_users

        yield mock_db


@pytest.fixture
def url():
    return "/api/login"


@pytest.fixture
async def cli(aiohttp_client, url):
    app = web.Application()
    app.router.add_post(url, login)
    return await aiohttp_client(app)


@pytest.fixture
def mock_verify_password():
    with mock.patch("rest_api.verify_password") as mock_verify:
        yield mock_verify


@pytest.fixture
def mock_create_token():
    with mock.patch("rest_api.create_access_token") as mock_token:
        yield mock_token


async def test_login_success(
    cli, url, mock_db, test_user, mock_verify_password, mock_create_token
):
    """LG-001: 登錄成功"""

    # Arrange
    mock_db.return_value.users.find_one.return_value = test_user
    mock_verify_password.return_value = True
    mock_create_token.return_value = "valid-token"

    # Act
    res = await cli.post(
        url, json={"email": "example@gmail.com", "password": "password"}
    )

    # Assert
    assert res.status == 200
    json_resonse = await res.json()
    assert "access_token" in json_resonse
    assert json_resonse["access_token"] == "valid-token"

    mock_db.return_value.users.find_one.assert_called_once_with(
        {"email": "example@gmail.com"}
    )
    mock_verify_password.assert_called_once_with("password", test_user["password"])
    mock_create_token.assert_called_once_with({"sub": str(test_user["_id"])})


async def test_login_missing_fields_failure(cli, url):
    """LG-002: 登入失敗，參數缺少"""
    # Act
    res = await cli.post(
        url,
        json={"email": "example@gmail.com"},
    )

    # Assert
    assert res.status == 400
    text_resonse = await res.text()
    assert "Invalid credentials" in text_resonse


async def test_login_wrong_password_failure(
    cli, url, mock_db, test_user, mock_verify_password
):
    """LG-003: 登入失敗，密碼錯誤"""
    # Arrange
    mock_db.return_value.users.find_one.return_value = test_user
    mock_verify_password.return_value = False

    # Act
    res = await cli.post(
        url, json={"email": "example@gmail.com", "password": "invalid-password"}
    )

    # Assert
    assert res.status == 401
    text = await res.text()
    assert "Invalid credentials" in text


async def test_login_wrong_email_failure(cli, url, mock_db):
    """LG-003: 登入失敗，Email錯誤"""
    # Arrange
    mock_db.return_value.users.find_one.return_value = None

    # Act
    res = await cli.post(
        url, json={"email": "invalid-example@gmail.com", "password": "password"}
    )

    # Assert
    assert res.status == 401
    text = await res.text()
    assert "Invalid credentials" in text
