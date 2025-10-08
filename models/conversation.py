# ============================================
# models/conversation.py
# ============================================
"""
Conversation Model

Manages conversation CRUD operations.
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
    """Conversation management"""
    
    @staticmethod
    def create(user_id: int, title: str = "New Chat") -> int:
        """
        Create a new conversation
        
        Args:
            user_id: ID of user creating the conversation
            title: Conversation title
            
        Returns:
            ID of newly created conversation
        """
        now = datetime.now().isoformat()
        result = conversations.insert(
            user_id=user_id,
            title=title,
            created_at=now,
            updated_at=now
        )
        return result.id if hasattr(result, 'id') else result
    
    @staticmethod
    def get_by_id(conversation_id: int):
        """Get conversation by ID"""
        return conversations[conversation_id]
    
    @staticmethod
    def get_by_user(user_id: int, limit: int = 50) -> list:
        """
        Get all conversations for a user
        
        Args:
            user_id: User ID
            limit: Maximum conversations to return
            
        Returns:
            List of conversations, newest first
        """
        return conversations(
            where=f"user_id = {user_id}",
            order_by="updated_at DESC",
            limit=limit
        )
    
    @staticmethod
    def update_title(conversation_id: int, title: str):
        """Update conversation title"""
        conversations.update(
            conversation_id,
            title=title,
            updated_at=datetime.now().isoformat()
        )
    
    @staticmethod
    def touch(conversation_id: int):
        """Update the updated_at timestamp"""
        conversations.update(
            conversation_id,
            updated_at=datetime.now().isoformat()
        )
    
    @staticmethod
    def delete(conversation_id: int):
        """
        Delete a conversation and all its messages
        
        Args:
            conversation_id: ID of conversation to delete
        """
        from .message import Message
        
        # Delete messages first
        Message.delete_by_conversation(conversation_id)
        
        # Delete conversation
        conversations.delete(conversation_id)
    
    @staticmethod
    def belongs_to_user(conversation_id: int, user_id: int) -> bool:
        """
        Check if conversation belongs to user
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID
            
        Returns:
            True if conversation belongs to user, False otherwise
        """
        conv = conversations[conversation_id]
        return conv and conv.user_id == user_id