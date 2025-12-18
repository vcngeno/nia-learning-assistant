"""Run database migrations"""
import os
from database import sync_engine

def run_migrations():
    """Add hashed_pin column to children table"""
    with sync_engine.connect() as conn:
        # Check if column exists
        result = conn.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='children' AND column_name='hashed_pin'
        """)

        if not result.fetchone():
            print("Adding hashed_pin column...")
            conn.execute("""
                ALTER TABLE children ADD COLUMN hashed_pin VARCHAR(255);
            """)
            conn.commit()
            print("✅ Migration complete!")
        else:
            print("Column already exists")

if __name__ == "__main__":
    run_migrations()
