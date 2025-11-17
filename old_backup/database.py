from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os
from datetime import datetime

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL")
if not MONGODB_URL:
    raise ValueError("MONGODB_URL not set in environment variables")

DATABASE_NAME = "nia_learning"

# Async client for FastAPI
async_client = AsyncIOMotorClient(MONGODB_URL)
async_db = async_client[DATABASE_NAME]

# Collections
parents_collection = async_db["parents"]
students_collection = async_db["students"]
activity_logs_collection = async_db["activity_logs"]
sessions_collection = async_db["sessions"]

# Sync client for non-async operations
sync_client = MongoClient(MONGODB_URL)
sync_db = sync_client[DATABASE_NAME]

async def init_db():
    """Initialize database with indexes"""
    try:
        # Parent indexes
        await parents_collection.create_index("email", unique=True)
        await parents_collection.create_index("parent_id", unique=True)
        
        # Student indexes
        await students_collection.create_index("student_id", unique=True)
        await students_collection.create_index("parent_id")
        
        # Activity log indexes
        await activity_logs_collection.create_index("student_id")
        await activity_logs_collection.create_index("timestamp")
        await activity_logs_collection.create_index([("student_id", 1), ("timestamp", -1)])
        
        print("✅ Database initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

async def close_db():
    """Close database connections"""
    async_client.close()
    sync_client.close()

def get_db():
    """Get database instance"""
    return async_db
