# ============================================
# models/database.py
# ============================================
"""
Database Management

Handles database connection, initialization, and utilities.
"""

from fastlite import Database
from pathlib import Path
from datetime import datetime, timedelta
import config

# Initialize database connection
db = Database(str(config.CONVERSATIONS_DB_PATH))

def init_database():
    """
    Initialize database and create tables if needed
    
    This is called once on application startup.
    """
    from .conversation import conversations
    from .message import messages
    
    # Tables are created when first accessed in their respective modules
    # This function exists for explicit initialization
    
    print(f"Database initialized: {config.CONVERSATIONS_DB_PATH}")
    print(f"- Conversations table: {len(conversations())} records")
    print(f"- Messages table: {len(messages())} records")

def get_database():
    """Get database instance"""
    return db

def cleanup_old_conversations(days: int = 90):
    """
    Delete conversations older than X days with no activity
    
    Args:
        days: Number of days of inactivity before deletion
        
    Returns:
        Number of conversations deleted
    """
    from .conversation import Conversation
    
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    
    # Get old conversations
    old_convs = db.execute(
        "SELECT id FROM conversations WHERE updated_at < ?",
        (cutoff,)
    ).fetchall()
    
    # Delete them
    for conv_row in old_convs:
        conv = Conversation.get_by_id(conv_row['id'])
        if conv:
            conv.delete()
    
    return len(old_convs)
