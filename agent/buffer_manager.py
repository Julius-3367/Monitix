"""Local buffer manager for offline resilience."""
import sqlite3
import json
import os
from typing import List, Dict, Any
from datetime import datetime


class BufferManager:
    """Manage local SQLite buffer for metrics when backend is unavailable."""
    
    def __init__(self, db_path: str, max_records: int = 1000):
        self.db_path = db_path
        self.max_records = max_records
        self._ensure_directory()
        self._init_db()
    
    def _ensure_directory(self):
        """Ensure buffer directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics_buffer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                retry_count INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON metrics_buffer(timestamp)
        ''')
        
        conn.commit()
        conn.close()
    
    def add(self, metrics: Dict[str, Any]) -> bool:
        """Add metrics to buffer."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if buffer is full
            cursor.execute('SELECT COUNT(*) FROM metrics_buffer')
            count = cursor.fetchone()[0]
            
            if count >= self.max_records:
                # Delete oldest records
                delete_count = count - self.max_records + 1
                cursor.execute('''
                    DELETE FROM metrics_buffer 
                    WHERE id IN (
                        SELECT id FROM metrics_buffer 
                        ORDER BY created_at ASC 
                        LIMIT ?
                    )
                ''', (delete_count,))
            
            # Insert new record
            cursor.execute('''
                INSERT INTO metrics_buffer (timestamp, payload, created_at)
                VALUES (?, ?, ?)
            ''', (
                metrics.get('timestamp', datetime.utcnow().isoformat()),
                json.dumps(metrics),
                datetime.utcnow().isoformat()
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding to buffer: {e}")
            return False
    
    def get_batch(self, batch_size: int = 50) -> List[Dict[str, Any]]:
        """Get a batch of metrics from buffer."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, payload 
                FROM metrics_buffer 
                ORDER BY created_at ASC 
                LIMIT ?
            ''', (batch_size,))
            
            rows = cursor.fetchall()
            conn.close()
            
            batch = []
            for row in rows:
                batch.append({
                    'id': row[0],
                    'metrics': json.loads(row[1])
                })
            
            return batch
        except Exception as e:
            print(f"Error getting batch from buffer: {e}")
            return []
    
    def remove_batch(self, ids: List[int]) -> bool:
        """Remove successfully sent records from buffer."""
        if not ids:
            return True
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            placeholders = ','.join('?' * len(ids))
            cursor.execute(f'''
                DELETE FROM metrics_buffer 
                WHERE id IN ({placeholders})
            ''', ids)
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error removing batch from buffer: {e}")
            return False
    
    def increment_retry(self, ids: List[int]) -> bool:
        """Increment retry count for failed records."""
        if not ids:
            return True
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            placeholders = ','.join('?' * len(ids))
            cursor.execute(f'''
                UPDATE metrics_buffer 
                SET retry_count = retry_count + 1
                WHERE id IN ({placeholders})
            ''', ids)
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error incrementing retry count: {e}")
            return False
    
    def get_count(self) -> int:
        """Get total number of buffered records."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM metrics_buffer')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0
    
    def clear_old_records(self, days: int = 7) -> int:
        """Clear records older than specified days."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            from datetime import timedelta
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            cursor.execute('''
                DELETE FROM metrics_buffer 
                WHERE created_at < ?
            ''', (cutoff,))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted
        except Exception as e:
            print(f"Error clearing old records: {e}")
            return 0
