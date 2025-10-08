# ============================================
# models/message.py
# ============================================
"""
Message Model

Manages message CRUD operations and conversation history.
"""

from datetime import datetime
from typing import List
from .database import db
from .conversation import Conversation

# Define messages table
messages = db.t.messages
if messages not in db.t:
    messages.create(
        id=int,
        conversation_id=int,
        role=str,  # 'user' or 'assistant'
        content=str,
        created_at=str,
        pk='id'
    )
    # Add indexes
    db.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)")

class Message:
    """Message management"""
    
    @staticmethod
    def create(conversation_id: int, role: str, content: str) -> int:
        """
        Create a new message
        
        Args:
            conversation_id: ID of conversation
            role: Message role ('user' or 'assistant')
            content: Message text
            
        Returns:
            ID of newly created message
        """
        now = datetime.now().isoformat()
        result = messages.insert(
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=now
        )
        
        # Update conversation timestamp
        Conversation.touch(conversation_id)
        
        return result.id if hasattr(result, 'id') else result
    
    @staticmethod
    def get_by_conversation(conversation_id: int) -> list:
        """
        Get all messages for a conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of messages, oldest first
        """
        return messages(
            where=f"conversation_id = {conversation_id}",
            order_by="created_at ASC"
        )
    
    @staticmethod
    def get_history(conversation_id: int) -> List[dict]:
        """
        Get conversation history in Anthropic API format
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of message dicts: [{"role": "user/assistant", "content": "..."}]
        """
        msgs = Message.get_by_conversation(conversation_id)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in msgs
        ]
    
    @staticmethod
    def delete_by_conversation(conversation_id: int):
        """
        Delete all messages in a conversation
        
        Args:
            conversation_id: Conversation ID
        """
        db.execute(
            "DELETE FROM messages WHERE conversation_id = ?",
            (conversation_id,)
        )
    
    @staticmethod
    def count_by_conversation(conversation_id: int) -> int:
        """
        Count messages in a conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Number of messages
        """
        result = db.execute(
            "SELECT COUNT(*) as count FROM messages WHERE conversation_id = ?",
            (conversation_id,)
        ).fetchone()
        return result['count'] if result else 0