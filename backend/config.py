# config.py
from pydantic_settings import BaseSettings  # 修改這行
from pydantic import EmailStr
import os

class Settings(BaseSettings):
    mongodb_url: str = "mongodb://{host}:{port}".format(
        host=os.getenv("MONGODB_HOST", "localhost"),
        port=os.getenv("MONGODB_PORT", "27017")
    )
    database_name: str = "video_platform"
    jwt_secret: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    websocket_port: int = 8765
    grpc_port: int = 50051
    api_port: int = 8080

settings = Settings()