"""Debug RAG search"""
import asyncio
from database import async_session
from services.content_manager import content_manager
from models import EducationalContent
from sqlalchemy import select

async def test_search():
    async with async_session() as db:
        print("🔍 Testing content search...")

        # Test 1: Search for fractions
        print("\n1. Searching for 'fractions' in math/elementary:")
        results = await content_manager.search_content(
            db=db,
            query="fractions",
            subject="math",
            grade_level="elementary",
            limit=3
        )
        print(f"   Found {len(results)} results")

        # Test 2: List all content
        print("\n2. All content in database:")
        result = await db.execute(select(EducationalContent))
        all_content = result.scalars().all()
        print(f"   Total: {len(all_content)} documents")
        for c in all_content:
            print(f"   - {c.title} ({c.subject}/{c.grade_level})")

asyncio.run(test_search())
