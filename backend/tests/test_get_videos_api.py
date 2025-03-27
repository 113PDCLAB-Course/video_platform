from unittest import mock

import pytest
from aiohttp import web
from bson import ObjectId

from rest_api import get_videos


@pytest.fixture
def video_id():
    return ObjectId()


@pytest.fixture
def user_id():
    return ObjectId()


@pytest.fixture
def test_video(video_id, user_id):
    return {
        "_id": video_id,
        "title": "test.mp4",
        "description": "test video",
        "file_path": "/upload/test.mp4",
        "uploader_id": str(user_id),
        "views": 0,
    }


@pytest.fixture
def test_user(user_id):
    return {"_id": user_id, "username": "root", "email": "example@gmail.com"}


@pytest.fixture
def mock_db():
    with mock.patch("rest_api.get_database") as mock_db:
        mock_users = mock.AsyncMock()
        mock_videos = mock.AsyncMock()

        mock_db.return_value.videos.find.return_value.to_list = mock_videos
        mock_db.return_value.users = mock_users

        yield mock_db


@pytest.fixture
def url():
    return "/api/videos"


@pytest.fixture
async def cli(aiohttp_client, url):
    app = web.Application()
    app.router.add_get(url, get_videos)
    return await aiohttp_client(app)


async def test_get_videos_success(cli, url, mock_db, test_video, test_user):
    """GV-001: 成功獲取影片列表"""
    # Arrange
    video1 = test_video.copy()
    video2 = test_video.copy()
    video2["_id"] = ObjectId()
    video2["title"] = "test2.mp4"

    mock_db.return_value.videos.find.return_value.to_list.return_value = [
        video1,
        video2,
    ]

    mock_db.return_value.users.find_one.side_effect = [test_user, None]

    # Act
    res = await cli.get(url)

    # Assert
    assert res.status == 200
    videos = await res.json()

    # 驗證有兩個影片
    assert len(videos) == 2

    # 驗證影片資訊
    assert videos[0]["id"] == str(video1["_id"])
    assert videos[0]["title"] == video1["title"]
    assert videos[0]["uploader"] == test_user["username"]
    assert videos[1]["id"] == str(video2["_id"])
    assert videos[1]["title"] == video2["title"]
    assert videos[1]["uploader"] == "Unknown"

    # 驗證資料庫查詢次數
    assert mock_db.return_value.videos.find.call_count == 1
    assert mock_db.return_value.users.find_one.call_count == 2
    mock_db.return_value.users.find_one.assert_has_calls(
        [
            mock.call({"_id": ObjectId(test_video["uploader_id"])}),
            mock.call({"_id": ObjectId(test_video["uploader_id"])}),
        ]
    )


async def test_get_empty_videos_list_success(cli, url, mock_db):
    """GV-002: 獲取空影片列表"""
    # Arrange
    mock_db.return_value.videos.find.return_value.to_list.return_value = []

    # Act
    res = await cli.get(url)

    # Assert
    assert res.status == 200
    videos = await res.json()

    # 驗證沒有影片
    assert len(videos) == 0


@mock.patch("builtins.print")
async def test_get_videos_with_invalid_data_success(
    mock_print, cli, url, mock_db, test_video, test_user
):
    """GV-003: 影片資料欄位異常處理測試"""
    # Arrange
    valid_video = test_video.copy()
    invalid_video1 = {"description": "Missing required fields"}
    invalid_video2 = {"_id": ObjectId(), "description": "Missing title and file_path"}

    mock_db.return_value.videos.find.return_value.to_list.return_value = [
        valid_video,
        invalid_video1,
        invalid_video2,
    ]
    mock_db.return_value.users.find_one.return_value = test_user

    # Act
    res = await cli.get(url)

    # Assert
    assert res.status == 200
    videos = await res.json()

    # 驗證只有一個有效的影片
    assert len(videos) == 1
    assert videos[0]["id"] == str(valid_video["_id"])
    assert videos[0]["title"] == valid_video["title"]
    assert videos[0]["uploader"] == test_user["username"]

    # 驗證資料庫查詢次數
    assert mock_db.return_value.videos.find.call_count == 1
    assert mock_db.return_value.users.find_one.call_count == 1

    # 驗證錯誤日誌
    mock_print.assert_any_call(mock.ANY)  # 至少被呼叫一次
    # 確認錯誤訊息包含預期的文字
    error_calls = [
        call
        for call in mock_print.call_args_list
        if "Error processing video" in str(call)
    ]
    assert len(error_calls) == 2  # 應該有兩個錯誤影片的日誌
