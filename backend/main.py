import asyncio
import logging
from aiohttp import web
import aiohttp_cors
import websockets  # 添加這行
from concurrent import futures
from database import connect_to_mongo, close_mongo_connection
from websocket_server import WebSocketServer
from grpc_server import VideoService
import video_service_pb2_grpc
from config import settings
import grpc
from pathlib import Path  # 添加這行


async def init_app() -> web.Application:
    # 初始化 logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # 創建 aiohttp 應用
    app = web.Application(
        client_max_size=1024 ** 3  # 設置為 1GB
    )

    # 添加靜態文件服務
    app.router.add_static('/uploads/', Path('uploads/'), show_index=True)

    # 設置 CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        )
    })

    # 添加路由
    from rest_api import routes
    app.add_routes(routes)

    # 為所有路由添加 CORS
    for route in list(app.router.routes()):
        cors.add(route)


    # 數據庫連接
    await connect_to_mongo()  # 修改這行
    return app


async def start_websocket_server():
    ws_server = WebSocketServer()
    await websockets.serve(
        ws_server.handler,
        "0.0.0.0",
        settings.websocket_port
    )


async def start_grpc_server():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    video_service_pb2_grpc.add_VideoServiceServicer_to_server(
        VideoService(), server
    )
    server.add_insecure_port(f'[::]:{settings.grpc_port}')
    await server.start()
    return server


async def cleanup_mongo(app):
    await close_mongo_connection()


async def main():
    # 初始化所有服務
    logging.info("Initializing all services...")

    app = await init_app()
    app.on_cleanup.append(cleanup_mongo)  # 添加清理函數

    # 啟動 WebSocket 服務器
    logging.info("Starting WebSocket server...")
    await start_websocket_server()

    # 啟動 gRPC 服務器
    logging.info("Starting gRPC server...")
    grpc_server = await start_grpc_server()

    # 啟動 REST API 服務器
    logging.info("Starting REST API server...")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", settings.api_port)
    await site.start()

    logging.info(f"REST API server started on port {settings.api_port}")
    logging.info(f"WebSocket server started on port {settings.websocket_port}")
    logging.info(f"gRPC server started on port {settings.grpc_port}")

    # 保持服務運行
    try:
        await asyncio.Future()  # run forever
    finally:
        logging.info("Cleaning up...")
        await runner.cleanup()
        await grpc_server.stop(grace=None)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())