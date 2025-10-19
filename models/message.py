# ============================================
# models/message.py
# ============================================
"""
Message Model

Manages message CRUD operations and conversation history with proper OOP design.
"""

from datetime import datetime
from typing import List
from .database import db

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
    """
    Message management with proper OOP design.
    
    Instances represent actual messages loaded from the database.
    Class methods provide factory/query operations.
    Instance methods operate on the message instance.
    """
    
    def __init__(self, db_row):
        """
        Initialize message from database row.
        
        Args:
            db_row: Database row object from fastlite (can be dict or object)
        """
        # Handle both dict and object returns from fastlite
        if isinstance(db_row, dict):
            # Convert dict to object for consistent property access
            from types import SimpleNamespace
            self._data = SimpleNamespace(**db_row)
        else:
            self._data = db_row
    
    # Properties for clean data access
    @property
    def id(self) -> int:
        """Message ID"""
        return self._data.id
    
    @property
    def conversation_id(self) -> int:
        """ID of conversation this message belongs to"""
        return self._data.conversation_id
    
    @property
    def role(self) -> str:
        """Message role: 'user' or 'assistant'"""
        return self._data.role
    
    @property
    def content(self) -> str:
        """Message content/text"""
        return self._data.content
    
    @property
    def created_at(self) -> str:
        """ISO timestamp when message was created"""
        return self._data.created_at
    
    # Class methods - factory/query operations
    @classmethod
    def create(cls, conversation_id: int, role: str, content: str) -> 'Message':
        """
        Create a new message and return its instance.
        
        Args:
            conversation_id: ID of conversation
            role: Message role ('user' or 'assistant')
            content: Message text
            
        Returns:
            New Message instance
        """
        now = datetime.now().isoformat()
        result = messages.insert(
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=now
        )
        
        # Update conversation timestamp
        from .conversation import Conversation
        conv = Conversation.get_by_id(conversation_id)
        if conv:
            conv.touch()
        
        # Handle both dict and object returns from fastlite
        if isinstance(result, dict):
            msg_id = result['id']
        elif hasattr(result, 'id'):
            msg_id = result.id
        else:
            msg_id = result  # Assume it's already an int
            
        return cls.get_by_id(msg_id)
    
    @classmethod
    def get_by_id(cls, message_id: int) -> 'Message':
        """
        Load message by ID and return instance.
        
        Args:
            message_id: Message ID
            
        Returns:
            Message instance or None if not found
        """
        row = messages[message_id]
        return cls(row) if row else None
    
    @classmethod
    def get_by_conversation(cls, conversation_id: int) -> list['Message']:
        """
        Get all messages for a conversation as instances.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of Message instances, oldest first
        """
        rows = messages(
            where="conversation_id = ?",
            where_args=[conversation_id],
            order_by="created_at ASC"
        )
        return [cls(row) for row in rows]
    
    @classmethod
    def get_history(cls, conversation_id: int) -> List[dict]:
        """
        Get conversation history in Anthropic API format.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of message dicts: [{"role": "user/assistant", "content": "..."}]
        """
        msgs = cls.get_by_conversation(conversation_id)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in msgs
        ]
    
    @classmethod
    def delete_by_conversation(cls, conversation_id: int):
        """
        Delete all messages in a conversation.
        
        Args:
            conversation_id: Conversation ID
        """
        db.execute(
            "DELETE FROM messages WHERE conversation_id = ?",
            (conversation_id,)
        )
    
    @classmethod
    def count_by_conversation(cls, conversation_id: int) -> int:
        """
        Count messages in a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Number of messages
        """
        result = db.execute(
            "SELECT COUNT(*) FROM messages WHERE conversation_id = ?",
            (conversation_id,)
        ).fetchone()
        # Handle both tuple and dict returns
        if isinstance(result, dict):
            return result['count'] if result else 0
        elif isinstance(result, tuple):
            return result[0] if result else 0
        else:
            return result if result else 0
    
    # Instance methods - operate on self
    def to_dict(self) -> dict:
        """
        Convert message to dictionary format for API.
        
        Returns:
            Dict with role and content
        """
        return {
            "role": self.role,
            "content": self.content
        }
    
    def delete(self):
        """
        Delete this message.
        
        Note: After calling this method, the instance should not be used further.
        """
        messages.delete(self.id)
    
    def get_conversation(self):
        """
        Get the Conversation instance this message belongs to.
        
        Returns:
            Conversation instance or None
        """
        from .conversation import Conversation
        return Conversation.get_by_id(self.conversation_id)
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message id={self.id} conversation_id={self.conversation_id} role='{self.role}' content='{content_preview}'>"
