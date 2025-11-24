"""
Content Management Service
Handles ingestion, storage, and retrieval of educational content
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
import hashlib
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from models import EducationalContent

logger = logging.getLogger(__name__)


class ContentManager:
    """Manages educational content ingestion and retrieval"""

    def __init__(self, content_dir: str = "educational_content"):
        self.content_dir = Path(content_dir)

    def parse_content_file(self, file_path: Path) -> Dict:
        """Parse a markdown content file and extract metadata"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract metadata from file path
            relative_path = file_path.relative_to(self.content_dir)
            parts = relative_path.parts

            # Subject is first directory
            subject = parts[0] if len(parts) > 0 else "general"

            # Grade level is second directory
            grade_level = parts[1] if len(parts) > 1 else "general"

            # Topic is filename without extension
            topic = file_path.stem.replace('_', ' ').title()

            # Extract title from first line if it's a heading
            lines = content.split('\n')
            title = topic
            for line in lines:
                if line.startswith('# '):
                    title = line.replace('# ', '').strip()
                    break

            # Calculate content hash for change detection
            content_hash = hashlib.md5(content.encode()).hexdigest()

            return {
                'title': title,
                'subject': subject,
                'grade_level': grade_level,
                'topic': topic,
                'content': content,
                'content_hash': content_hash,
                'file_path': str(relative_path),
                'word_count': len(content.split()),
            }
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return None

    def discover_content_files(self) -> List[Path]:
        """Discover all markdown files in content directory"""
        if not self.content_dir.exists():
            logger.warning(f"Content directory {self.content_dir} does not exist")
            return []

        md_files = list(self.content_dir.rglob("*.md"))
        logger.info(f"Found {len(md_files)} content files")
        return md_files

    async def ingest_content_file(
        self,
        file_path: Path,
        db: AsyncSession,
        force_update: bool = False
    ) -> Optional[EducationalContent]:
        """Ingest a single content file into database"""

        # Parse file
        metadata = self.parse_content_file(file_path)
        if not metadata:
            return None

        try:
            # Check if content already exists
            result = await db.execute(
                select(EducationalContent).where(
                    EducationalContent.file_path == metadata['file_path']
                )
            )
            existing_content = result.scalar_one_or_none()

            if existing_content:
                # Check if content has changed
                if existing_content.content_hash == metadata['content_hash'] and not force_update:
                    logger.info(f"Content unchanged, skipping: {metadata['title']}")
                    return existing_content

                # Update existing content
                logger.info(f"Updating content: {metadata['title']}")
                existing_content.title = metadata['title']
                existing_content.subject = metadata['subject']
                existing_content.grade_level = metadata['grade_level']
                existing_content.topic = metadata['topic']
                existing_content.content = metadata['content']
                existing_content.content_hash = metadata['content_hash']
                existing_content.word_count = metadata['word_count']
                existing_content.updated_at = datetime.utcnow()

                await db.commit()
                await db.refresh(existing_content)
                return existing_content

            else:
                # Create new content
                logger.info(f"Adding new content: {metadata['title']}")
                new_content = EducationalContent(
                    title=metadata['title'],
                    subject=metadata['subject'],
                    grade_level=metadata['grade_level'],
                    topic=metadata['topic'],
                    content=metadata['content'],
                    content_hash=metadata['content_hash'],
                    file_path=metadata['file_path'],
                    word_count=metadata['word_count'],
                )

                db.add(new_content)
                await db.commit()
                await db.refresh(new_content)
                return new_content

        except Exception as e:
            logger.error(f"Error ingesting content {metadata['title']}: {e}")
            await db.rollback()
            return None

    async def ingest_all_content(
        self,
        db: AsyncSession,
        force_update: bool = False
    ) -> Dict[str, int]:
        """Ingest all content files"""

        files = self.discover_content_files()
        stats = {
            'total': len(files),
            'added': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }

        for file_path in files:
            result = await self.ingest_content_file(file_path, db, force_update)

            if result:
                if result.created_at == result.updated_at:
                    stats['added'] += 1
                else:
                    stats['updated'] += 1
            else:
                stats['errors'] += 1

        stats['skipped'] = stats['total'] - stats['added'] - stats['updated'] - stats['errors']

        logger.info(f"Content ingestion complete: {stats}")
        return stats

    async def search_content(
        self,
        db: AsyncSession,
        query: str = None,
        subject: str = None,
        grade_level: str = None,
        topic: str = None,
        limit: int = 10
    ) -> List[EducationalContent]:
        """Search educational content with filters"""

        conditions = []

        if subject:
            conditions.append(EducationalContent.subject == subject)

        if grade_level:
            conditions.append(EducationalContent.grade_level == grade_level)

        if topic:
            conditions.append(EducationalContent.topic.ilike(f"%{topic}%"))

        # Only use query filter if no subject/grade filters
        # Otherwise the subject+grade is enough to find relevant content
        if query and not (subject or grade_level):
            conditions.append(
                EducationalContent.content.ilike(f"%{query}%")
            )

        stmt = select(EducationalContent)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # If we have subject but no results with filters, try subject only
        if not conditions and subject:
            stmt = stmt.where(EducationalContent.subject == subject)

        stmt = stmt.limit(limit)

        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_content_by_id(
        self,
        db: AsyncSession,
        content_id: int
    ) -> Optional[EducationalContent]:
        """Get specific content by ID"""

        result = await db.execute(
            select(EducationalContent).where(EducationalContent.id == content_id)
        )
        return result.scalar_one_or_none()

    async def get_subjects(self, db: AsyncSession) -> List[str]:
        """Get list of all subjects"""
        result = await db.execute(
            select(EducationalContent.subject).distinct()
        )
        return [row[0] for row in result.all()]

    async def get_topics_by_subject(
        self,
        db: AsyncSession,
        subject: str
    ) -> List[str]:
        """Get all topics for a subject"""
        result = await db.execute(
            select(EducationalContent.topic)
            .where(EducationalContent.subject == subject)
            .distinct()
        )
        return [row[0] for row in result.all()]

    async def get_content_stats(self, db: AsyncSession) -> Dict:
        """Get statistics about content library"""

        # Total content count
        total_result = await db.execute(
            select(EducationalContent)
        )
        total = len(total_result.scalars().all())

        # By subject
        subjects = await self.get_subjects(db)
        by_subject = {}

        for subject in subjects:
            result = await db.execute(
                select(EducationalContent)
                .where(EducationalContent.subject == subject)
            )
            by_subject[subject] = len(result.scalars().all())

        return {
            'total_documents': total,
            'subjects': subjects,
            'by_subject': by_subject,
        }


# Singleton instance
content_manager = ContentManager()
