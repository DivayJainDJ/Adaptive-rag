"""
MongoDB client initialization.
"""

import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URL = os.getenv("MONGODB_URL", "mongodb://127.0.0.1:27017")
DB_NAME = os.getenv("MONGODB_DB_NAME", "adaptive_rag")

client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=2000)
db = client[DB_NAME]
