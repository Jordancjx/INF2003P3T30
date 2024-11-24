from config.constants import DB_NAME, mongo_uri
from motor.motor_asyncio import AsyncIOMotorClient


async def get_db():
    try:
        client = AsyncIOMotorClient(mongo_uri)
        db = client[DB_NAME]
        return db

    except Exception as e:
        print('Error connecting to db')
        return None