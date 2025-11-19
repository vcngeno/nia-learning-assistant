"""
Script to ingest educational content into database
Run this after adding new content files
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database import async_session
from services.content_manager import content_manager
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(name)s] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Ingest all educational content"""
    logger.info("🚀 Starting content ingestion...")

    async with async_session() as db:
        stats = await content_manager.ingest_all_content(db, force_update=False)

        logger.info("\n" + "="*60)
        logger.info("📊 CONTENT INGESTION COMPLETE")
        logger.info("="*60)
        logger.info(f"Total files found: {stats['total']}")
        logger.info(f"✅ Added: {stats['added']}")
        logger.info(f"🔄 Updated: {stats['updated']}")
        logger.info(f"⏭️  Skipped (unchanged): {stats['skipped']}")
        logger.info(f"❌ Errors: {stats['errors']}")
        logger.info("="*60)

        # Get content stats
        content_stats = await content_manager.get_content_stats(db)
        logger.info(f"\n📚 Content Library Stats:")
        logger.info(f"Total documents: {content_stats['total_documents']}")
        logger.info(f"Subjects: {', '.join(content_stats['subjects'])}")
        logger.info(f"\nBy Subject:")
        for subject, count in content_stats['by_subject'].items():
            logger.info(f"  - {subject}: {count} documents")


if __name__ == "__main__":
    asyncio.run(main())
