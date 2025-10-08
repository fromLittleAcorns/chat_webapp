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
        ValueError: If user doesn't have access or conversation not found
    """
    conv = Conversation.get_by_id(conversation_id)
    
    if not conv:
        raise ValueError("Conversation not found")
    
    if not conv.belongs_to_user(user_id):
        raise ValueError("Unauthorized access to conversation")
    
    return True
