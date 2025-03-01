from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

class Database:
    client: AsyncIOMotorClient = None

async def connect_to_mongo():
    try:
        Database.client = AsyncIOMotorClient(settings.mongodb_url)
        # 測試連接
        await Database.client.admin.command('ping')
        print("Connected to MongoDB!")
    except Exception as e:
        print(f"Error connecting to MongoDB: {str(e)}")
        raise

async def close_mongo_connection():
    if Database.client is not None:
        Database.client.close()
        print("Closed MongoDB connection")

def get_database():
    if Database.client is None:
        print("Warning: Database client is None")
        return None
    return Database.client[settings.database_name]