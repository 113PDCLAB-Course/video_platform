import os
from typing import Any, Dict

import aiohttp_cors
from aiohttp import web
from bson import ObjectId

from auth import create_access_token, get_password_hash, verify_password
from database import get_database
from models import UserModel, VideoModel

routes = web.RouteTableDef()


@routes.post("/api/register")
async def register(request: web.Request) -> web.Response:
    try:
        # 檢查數據庫連接
        db = get_database()
        if db is None:  # 使用 is None 而不是直接檢查 db
            print("Database connection failed")
            raise web.HTTPInternalServerError(text="Database connection failed")

        # 解析請求數據
        try:
            data = await request.json()
            print(f"Received registration data: {data}")
        except Exception as e:
            print(f"Error parsing request data: {str(e)}")
            raise web.HTTPBadRequest(text="Invalid request data")

        # 驗證數據
        required_fields = ["username", "email", "password"]
        if not all(field in data for field in required_fields):
            missing_fields = [field for field in required_fields if field not in data]
            print(f"Missing fields: {missing_fields}")
            raise web.HTTPBadRequest(text=f"Missing required fields: {missing_fields}")

        # 檢查郵箱
        existing_user = await db.users.find_one({"email": data["email"]})
        if existing_user:
            print(f"Email already exists: {data['email']}")
            raise web.HTTPBadRequest(text="Email already registered")

        try:
            # 創建用戶模型
            user = UserModel(
                username=data["username"],
                email=data["email"],
                password=get_password_hash(data["password"]),
            )
            print(f"Created user model: {user}")
        except Exception as e:
            print(f"Error creating user model: {str(e)}")
            raise web.HTTPBadRequest(text=f"Invalid user data: {str(e)}")

        try:
            # 保存到數據庫
            result = await db.users.insert_one(user.dict(exclude={"id"}))
            print(f"User saved with ID: {result.inserted_id}")
        except Exception as e:
            print(f"Error saving to database: {str(e)}")
            raise web.HTTPInternalServerError(text=f"Database error: {str(e)}")

        # 返回結果
        return web.json_response(
            {
                "id": str(result.inserted_id),
                "username": user.username,
                "email": user.email,
            }
        )

    except web.HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in register: {str(e)}")
        raise web.HTTPInternalServerError(text=str(e))


@routes.post("/api/login")
async def login(request: web.Request) -> web.Response:
    db = get_database()
    data = await request.json()

    if "email" not in data or "password" not in data:
        raise web.HTTPBadRequest(text="Invalid credentials")

    user = await db.users.find_one({"email": data["email"]})
    if not user or not verify_password(data["password"], user["password"]):
        raise web.HTTPUnauthorized(text="Invalid credentials")

    access_token = create_access_token({"sub": str(user["_id"])})
    return web.json_response({"access_token": access_token})


@routes.get("/api/videos")
async def get_videos(request: web.Request) -> web.Response:
    db = get_database()
    videos = []

    video_list = await db.videos.find().to_list(length=None)

    for video in video_list:
        try:
            uploader = None
            uploader_id = video["uploader_id"]

            # 處理有效的 ObjectId
            if isinstance(uploader_id, str) and uploader_id != "default_user_id":
                try:
                    uploader = await db.users.find_one({"_id": ObjectId(uploader_id)})
                except:
                    pass

            videos.append(
                {
                    "id": str(video["_id"]),
                    "title": video["title"],
                    "description": video.get("description", ""),
                    "file_path": video["file_path"],
                    "uploader": uploader["username"] if uploader else "Unknown",
                    "views": video["views"],
                }
            )
        except Exception as e:
            print(f"Error processing video {video.get('_id')}: {str(e)}")
            continue

    return web.json_response(videos)


@routes.post("/api/videos")
async def create_video(request: web.Request) -> web.Response:
    try:
        # 從 authorization header 獲取 token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise web.HTTPUnauthorized(text="Missing or invalid token")

        token = auth_header.split(" ")[1]
        try:
            # 解析 token 獲取用戶 ID
            from jose import jwt

            from config import settings

            payload = jwt.decode(
                token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
            )
            user_id = payload.get("sub")
        except Exception as e:
            raise web.HTTPUnauthorized(text="Invalid token")

        reader = await request.multipart()

        # 獲取視頻標題
        field = await reader.next()
        title = ""
        if field.name == "title":
            title = await field.text()

        # 獲取視頻文件
        field = await reader.next()
        if field.name == "file":
            # 生成唯一的文件名
            filename = f"{str(ObjectId())}{os.path.splitext(field.filename)[1]}"

            # 確保 uploads 目錄存在
            os.makedirs("uploads", exist_ok=True)

            # 寫入文件
            file_path = os.path.join("uploads", filename)
            with open(file_path, "wb") as f:
                while True:
                    chunk = await field.read_chunk()
                    if not chunk:
                        break
                    f.write(chunk)

            # 創建視頻記錄
            video = VideoModel(
                title=title, file_path=filename, uploader_id=user_id  # 只儲存文件名
            )

            # 保存到數據庫
            result = await get_database().videos.insert_one(video.dict(exclude={"id"}))

            return web.json_response(
                {
                    "id": str(result.inserted_id),
                    "title": video.title,
                    "file_path": filename,
                }
            )

        raise web.HTTPBadRequest(text="No video file provided")

    except web.HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading video: {str(e)}")
        raise web.HTTPInternalServerError(text=str(e))


@routes.delete("/api/videos/{video_id}")
async def delete_video(request: web.Request) -> web.Response:
    try:
        # 1. 驗證用戶身份
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise web.HTTPUnauthorized(text="Missing or invalid token")

        # 2. 獲取視頻 ID 並驗證
        video_id = request.match_info["video_id"]
        if not ObjectId.is_valid(video_id):
            raise web.HTTPBadRequest(text="Invalid video ID format")

        db = get_database()

        # 3. 查找視頻
        video = await db.videos.find_one({"_id": ObjectId(video_id)})
        if not video:
            raise web.HTTPNotFound(text="Video not found")

        # 4. 刪除文件
        try:
            file_path = os.path.join("uploads", video["file_path"])
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            # 即使文件刪除失敗，仍繼續刪除數據庫記錄

        # 5. 從數據庫中刪除記錄
        delete_result = await db.videos.delete_one({"_id": ObjectId(video_id)})

        if delete_result.deleted_count == 0:
            raise web.HTTPNotFound(text="Video not found or already deleted")

        return web.json_response(
            {"message": "Video deleted successfully", "video_id": video_id}
        )

    except web.HTTPException as he:
        print(f"HTTP Exception in delete_video: {str(he)}")
        raise he
    except Exception as e:
        print(f"Error in delete_video: {str(e)}")
        return web.json_response(
            {"error": "Failed to delete video", "details": str(e)}, status=500
        )


@routes.post("/api/videos/{video_id}/view")
async def increment_views(request: web.Request) -> web.Response:
    try:
        video_id = request.match_info["video_id"]
        db = get_database()

        result = await db.videos.update_one(
            {"_id": ObjectId(video_id)}, {"$inc": {"views": 1}}
        )

        if result.modified_count == 0:
            raise web.HTTPNotFound(text="Video not found")

        return web.json_response({"message": "View count updated"})
    except Exception as e:
        raise web.HTTPInternalServerError(text=str(e))
