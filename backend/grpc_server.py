import grpc
from concurrent import futures
import video_service_pb2
import video_service_pb2_grpc
import asyncio
from config import settings
import os

class VideoService(video_service_pb2_grpc.VideoServiceServicer):
    def __init__(self):
        self.upload_path = "uploads"
        os.makedirs(self.upload_path, exist_ok=True)

    async def UploadVideo(self, request_iterator, context):
        video_data = bytearray()
        video_id = None

        async for chunk in request_iterator:
            if not video_id:
                video_id = chunk.video_id
            video_data.extend(chunk.content)

        if video_id:
            file_path = os.path.join(self.upload_path, f"{video_id}.mp4")
            with open(file_path, "wb") as f:
                f.write(video_data)
            return video_service_pb2.UploadResponse(
                video_id=video_id,
                success=True,
                message="Video uploaded successfully"
            )
        return video_service_pb2.UploadResponse(
            success=False,
            message="Failed to upload video"
        )

    async def GetVideo(self, request, context):
        video_id = request.video_id
        file_path = os.path.join(self.upload_path, f"{video_id}.mp4")

        if not os.path.exists(file_path):
            context.abort(grpc.StatusCode.NOT_FOUND, "Video not found")

        chunk_size = 1024 * 1024  # 1MB chunks
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield video_service_pb2.VideoChunk(
                    content=chunk,
                    video_id=video_id
                )
