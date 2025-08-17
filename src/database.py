"""Database operations for container tracking."""

import sqlite3
import logging
from datetime import datetime
from typing import List, Optional
from contextlib import contextmanager

from .models import ContainerInfo, DigestChange
import config


logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations for container tracking."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create containers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS containers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    container_id TEXT NOT NULL,
                    container_name TEXT NOT NULL,
                    service_name TEXT,
                    image_name TEXT NOT NULL,
                    image_tag TEXT NOT NULL,
                    digest TEXT NOT NULL,
                    project_name TEXT,
                    scan_timestamp DATETIME NOT NULL,
                    created_at DATETIME NOT NULL,
                    UNIQUE(container_name, scan_timestamp)
                )
            ''')
            
            # Create digest history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS digest_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    container_name TEXT NOT NULL,
                    old_digest TEXT NOT NULL,
                    new_digest TEXT NOT NULL,
                    change_timestamp DATETIME NOT NULL
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_containers_name 
                ON containers(container_name)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_containers_timestamp 
                ON containers(scan_timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_history_name 
                ON digest_history(container_name)
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def store_container_info(self, container_info: ContainerInfo, scan_timestamp: datetime = None):
        """Store container information in database."""
        if scan_timestamp is None:
            scan_timestamp = datetime.now()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if we have a previous record for this container
            cursor.execute('''
                SELECT digest FROM containers 
                WHERE container_name = ? 
                ORDER BY scan_timestamp DESC 
                LIMIT 1
            ''', (container_info.container_name,))
            
            previous_record = cursor.fetchone()
            
            # If digest changed, record the change
            if previous_record and previous_record['digest'] != container_info.digest:
                self._record_digest_change(
                    cursor,
                    container_info.container_name,
                    previous_record['digest'],
                    container_info.digest,
                    scan_timestamp
                )
            
            # Insert new container record
            cursor.execute('''
                INSERT INTO containers (
                    container_id, container_name, service_name, image_name, 
                    image_tag, digest, project_name, scan_timestamp, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                container_info.container_id,
                container_info.container_name,
                container_info.service_name,
                container_info.image_name,
                container_info.image_tag,
                container_info.digest,
                container_info.project_name,
                scan_timestamp,
                container_info.created_at
            ))
            
            conn.commit()
            logger.debug(f"Stored container info: {container_info.container_name}")
    
    def _record_digest_change(self, cursor, container_name: str, old_digest: str, 
                            new_digest: str, timestamp: datetime):
        """Record a digest change in the history table."""
        cursor.execute('''
            INSERT INTO digest_history (
                container_name, old_digest, new_digest, change_timestamp
            ) VALUES (?, ?, ?, ?)
        ''', (container_name, old_digest, new_digest, timestamp))
        
        logger.info(f"Digest change recorded for {container_name}")
    
    def get_latest_containers(self) -> List[ContainerInfo]:
        """Get the latest scan results for all containers."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT c1.* FROM containers c1
                INNER JOIN (
                    SELECT container_name, MAX(scan_timestamp) as max_timestamp
                    FROM containers
                    GROUP BY container_name
                ) c2 ON c1.container_name = c2.container_name 
                AND c1.scan_timestamp = c2.max_timestamp
                ORDER BY c1.container_name
            ''')
            
            containers = []
            for row in cursor.fetchall():
                containers.append(ContainerInfo(
                    container_id=row['container_id'],
                    container_name=row['container_name'],
                    service_name=row['service_name'],
                    image_name=row['image_name'],
                    image_tag=row['image_tag'],
                    digest=row['digest'],
                    project_name=row['project_name'],
                    created_at=datetime.fromisoformat(row['created_at'])
                ))
            
            return containers
    
    def get_digest_history(self, container_name: str) -> List[DigestChange]:
        """Get digest change history for a specific container."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM digest_history 
                WHERE container_name = ? 
                ORDER BY change_timestamp DESC
            ''', (container_name,))
            
            changes = []
            for row in cursor.fetchall():
                changes.append(DigestChange(
                    container_name=row['container_name'],
                    old_digest=row['old_digest'],
                    new_digest=row['new_digest'],
                    change_timestamp=datetime.fromisoformat(row['change_timestamp'])
                ))
            
            return changes
    
    def get_recent_changes(self, hours: int = 24) -> List[DigestChange]:
        """Get recent digest changes within specified hours."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM digest_history 
                WHERE change_timestamp > datetime('now', '-{} hours')
                ORDER BY change_timestamp DESC
            '''.format(hours))
            
            changes = []
            for row in cursor.fetchall():
                changes.append(DigestChange(
                    container_name=row['container_name'],
                    old_digest=row['old_digest'],
                    new_digest=row['new_digest'],
                    change_timestamp=datetime.fromisoformat(row['change_timestamp'])
                ))
            
            return changes