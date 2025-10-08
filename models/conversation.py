# ============================================
# models/conversation.py
# ============================================
"""
Conversation Model

Manages conversation CRUD operations with proper OOP design.
"""

from datetime import datetime
from .database import db

# Define conversations table
conversations = db.t.conversations
if conversations not in db.t:
    conversations.create(
        id=int,
        user_id=int,
        title=str,
        created_at=str,
        updated_at=str,
        pk='id'
    )
    # Add indexes
    db.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at)")

class Conversation:
    """
    Conversation management with proper OOP design.
    
    Instances represent actual conversations loaded from the database.
    Class methods provide factory/query operations.
    Instance methods operate on the conversation instance.
    """
    
    def __init__(self, db_row):
        """
        Initialize conversation from database row.
        
        Args:
            db_row: Database row object from fastlite
        """
        self._data = db_row
    
    # Properties for clean data access
    @property
    def id(self) -> int:
        """Conversation ID"""
        return self._data.id
    
    @property
    def user_id(self) -> int:
        """ID of user who owns this conversation"""
        return self._data.user_id
    
    @property
    def title(self) -> str:
        """Conversation title"""
        return self._data.title
    
    @property
    def created_at(self) -> str:
        """ISO timestamp when conversation was created"""
        return self._data.created_at
    
    @property
    def updated_at(self) -> str:
        """ISO timestamp when conversation was last updated"""
        return self._data.updated_at
    
    # Class methods - factory/query operations
    @classmethod
    def create(cls, user_id: int, title: str = "New Chat") -> 'Conversation':
        """
        Create a new conversation and return its instance.
        
        Args:
            user_id: ID of user creating the conversation
            title: Conversation title
            
        Returns:
            New Conversation instance
        """
        now = datetime.now().isoformat()
        result = conversations.insert(
            user_id=user_id,
            title=title,
            created_at=now,
            updated_at=now
        )
        conv_id = result.id if hasattr(result, 'id') else result
        return cls.get_by_id(conv_id)
    
    @classmethod
    def get_by_id(cls, conversation_id: int) -> 'Conversation':
        """
        Load conversation by ID and return instance.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation instance or None if not found
        """
        row = conversations[conversation_id]
        return cls(row) if row else None
    
    @classmethod
    def get_by_user(cls, user_id: int, limit: int = 50) -> list['Conversation']:
        """
        Get all conversations for a user as instances.
        
        Args:
            user_id: User ID
            limit: Maximum conversations to return
            
        Returns:
            List of Conversation instances, newest first
        """
        rows = conversations(
            where=f"user_id = {user_id}",
            order_by="updated_at DESC",
            limit=limit
        )
        return [cls(row) for row in rows]
    
    # Instance methods - operate on self
    def update_title(self, title: str):
        """
        Update this conversation's title.
        
        Args:
            title: New title
        """
        conversations.update(
            self.id,
            title=title,
            updated_at=datetime.now().isoformat()
        )
        # Refresh internal data to reflect changes
        self._data = conversations[self.id]
    
    def touch(self):
        """Update this conversation's updated_at timestamp."""
        conversations.update(
            self.id,
            updated_at=datetime.now().isoformat()
        )
        # Refresh internal data to reflect changes
        self._data = conversations[self.id]
    
    def delete(self):
        """
        Delete this conversation and all its messages.
        
        Note: After calling this method, the instance should not be used further.
        """
        from .message import Message
        
        # Delete messages first
        Message.delete_by_conversation(self.id)
        
        # Delete conversation
        conversations.delete(self.id)
    
    def belongs_to_user(self, user_id: int) -> bool:
        """
        Check if this conversation belongs to the specified user.
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if conversation belongs to user, False otherwise
        """
        return self.user_id == user_id
    
    def get_messages(self) -> list:
        """
        Get all messages for this conversation.
        
        Returns:
            List of Message instances
        """
        from .message import Message
        return Message.get_by_conversation(self.id)
    
    def get_history(self) -> list[dict]:
        """
        Get conversation history in Anthropic API format.
        
        Returns:
            List of message dicts: [{"role": "user/assistant", "content": "..."}]
        """
        from .message import Message
        return Message.get_history(self.id)
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<Conversation id={self.id} user_id={self.user_id} title='{self.title}'>"
