"""
Migration: Add language and learning fields to children table
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """Add new columns to children table"""
    logger.info("🔄 Running migration: Add child language fields...")

    async with engine.begin() as conn:
        # Add preferred_language column
        try:
            await conn.execute(text(
                "ALTER TABLE children ADD COLUMN IF NOT EXISTS preferred_language VARCHAR DEFAULT 'en' NOT NULL"
            ))
            logger.info("✅ Added preferred_language column")
        except Exception as e:
            logger.warning(f"preferred_language: {e}")

        # Add reading_level column
        try:
            await conn.execute(text(
                "ALTER TABLE children ADD COLUMN IF NOT EXISTS reading_level VARCHAR DEFAULT 'at grade level'"
            ))
            logger.info("✅ Added reading_level column")
        except Exception as e:
            logger.warning(f"reading_level: {e}")

        # Add learning_accommodations column (using TEXT for compatibility)
        try:
            await conn.execute(text(
                "ALTER TABLE children ADD COLUMN IF NOT EXISTS learning_accommodations TEXT DEFAULT '[]'"
            ))
            logger.info("✅ Added learning_accommodations column")
        except Exception as e:
            logger.warning(f"learning_accommodations: {e}")

    logger.info("✅ Migration complete!")


if __name__ == "__main__":
    asyncio.run(migrate())
