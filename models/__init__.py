"""
Models Package - Minimal initialization and exports

This file should ONLY contain imports and exports.
All implementation belongs in separate modules.
"""

from .database import db, init_database, get_database, cleanup_old_conversations
from .conversation import Conversation
from .message import Message
from .validators import validate_conversation_access

# Public API
__all__ = [
    # Database
    'db',
    'init_database',
    'get_database',
    'cleanup_old_conversations',
    
    # Models
    'Conversation',
    'Message',
    
    # Validators
    'validate_conversation_access',
]
