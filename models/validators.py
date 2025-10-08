# ============================================
# models/validators.py
# ============================================
"""
Validation Functions

Business logic for validating access and permissions.
"""

from .conversation import Conversation

def validate_conversation_access(conversation_id: int, user_id: int) -> bool:
    """
    Validate that a user has access to a conversation
    
    Args:
        conversation_id: Conversation ID
        user_id: User ID
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If user doesn't have access
    """
    if not Conversation.belongs_to_user(conversation_id, user_id):
        raise ValueError("Unauthorized access to conversation")
    return True