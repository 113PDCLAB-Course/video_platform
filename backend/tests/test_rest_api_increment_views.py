import pytest
from unittest import mock
from aiohttp import web
from bson import ObjectId
from rest_api import increment_views


@pytest.fixture
async def cli(aiohttp_client):
    """建立 aiohttp app 並註冊 view route"""
    app = web.Application()
    app.router.add_post("/api/videos/{video_id}/view", increment_views)
    return await aiohttp_client(app)


@pytest.fixture
def mock_db():
    """模擬資料庫"""
    with mock.patch("rest_api.get_database") as mock_db:
        mock_videos = mock.AsyncMock()
        mock_db.return_value = mock.MagicMock()
        mock_db.return_value.videos = mock_videos
        yield mock_db


@pytest.mark.asyncio
async def test_increment_views_invalid_objectid(cli, mock_db):
    """IV-001: 無效影片ID格式 (ObjectId 格式錯誤)"""
    res = await cli.post("/api/videos/123456/view")

    assert res.status == 500  # 因為目前程式碼是 except Exception: → 回傳 500
    text = await res.text()
    assert "is not a valid ObjectId" in text


@pytest.mark.asyncio
async def test_increment_views_success(cli, mock_db):
    """IV-002: 影片存在時，成功更新"""
    video_id = "507f1f77bcf86cd799439012"
    mock_result = mock.MagicMock()
    mock_result.modified_count = 1
    mock_db.return_value.videos.update_one.return_value = mock_result

    res = await cli.post(f"/api/videos/{video_id}/view")

    assert res.status == 200
    json_response = await res.json()
    assert json_response == {"message": "View count updated"}

    # 確認 update_one 被呼叫
    mock_db.return_value.videos.update_one.assert_awaited_once_with(
        {"_id": ObjectId(video_id)},
        {"$inc": {"views": 1}}
    )


@pytest.mark.asyncio
async def test_increment_views_video_not_found(cli, mock_db):
    """IV-003: 影片不存在 (modified_count = 0)"""
    video_id = "507f1f77bcf86cd799439011"
    mock_result = mock.MagicMock()
    mock_result.modified_count = 0
    mock_db.return_value.videos.update_one.return_value = mock_result

    res = await cli.post(f"/api/videos/{video_id}/view")

    assert res.status == 404
    text = await res.text()
    assert "Video not found" in text

    # 確認 update_one 被呼叫
    mock_db.return_value.videos.update_one.assert_awaited_once_with(
        {"_id": ObjectId(video_id)},
        {"$inc": {"views": 1}}
    )


@pytest.mark.asyncio
async def test_increment_views_database_error(cli, mock_db):
    """IV-004: 資料庫錯誤 (update_one 時拋出 Exception)"""
    video_id = "507f1f77bcf86cd799439013"
    mock_db.return_value.videos.update_one.side_effect = Exception("DB error")

    res = await cli.post(f"/api/videos/{video_id}/view")

    assert res.status == 500
    text = await res.text()
    assert "DB error" in text


@pytest.mark.asyncio
async def test_increment_views_invalid_but_valid_format(cli, mock_db):
    """IV-005: 格式合法但資料庫執行時發生 InvalidId 例外"""
    video_id = "507f1f77bcf86cd799439014"
    mock_db.return_value.videos.update_one.side_effect = Exception("InvalidId")

    res = await cli.post(f"/api/videos/{video_id}/view")

    assert res.status == 500
    text = await res.text()
    assert "InvalidId" in text
