"""
Reusable UI Components

Building blocks for the chat interface.
"""

from fasthtml.common import *
from datetime import datetime

# ============================================
# Message Bubbles
# ============================================

def message_bubble(role: str, content: str):
    """
    Standard message bubble
    
    Args:
        role: 'user' or 'assistant'
        content: Message text (will be rendered as markdown)
    """
    
    is_user = role == 'user'
    timestamp = datetime.now().strftime("%H:%M")
    
    return Article(
        Div(
            # Message content (will be converted to markdown by JS)
            Div(
                content,
                cls="message-content"
            ),
            
            # Metadata
            Small(
                f"{'You' if is_user else 'Assistant'} • {timestamp}",
                cls="message-meta"
            ),
        ),
        cls=f"message {'user-message' if is_user else 'assistant-message'}"
    )

def streaming_message_bubble(response_id: str, conversation_id: int, user_message: str):
    """
    Streaming message bubble with SSE connection
    
    This creates a placeholder that will be filled with streaming content.
    
    Args:
        response_id: Unique ID for this response
        conversation_id: ID of conversation
        user_message: The user's message (for context)
    """
    
    timestamp = datetime.now().strftime("%H:%M")
    
    return Article(
        Div(
            # Streaming content container
            Div(
                # Typing indicator while waiting for first chunk
                Div(
                    Span("●", cls="dot"),
                    Span("●", cls="dot"),
                    Span("●", cls="dot"),
                    cls="typing-indicator"
                ),
                
                id=f"stream-{response_id}",
                cls="message-content streaming",
                
                # HTMX SSE extension attributes
                **{
                    "hx-ext": "sse",
                    "sse-connect": f"/api/chat/stream?response_id={response_id}&conversation_id={conversation_id}&message={user_message}",
                    "sse-swap": "message"
                }
            ),
            
            # Metadata
            Small(
                f"Assistant • {timestamp}",
                cls="message-meta"
            ),
        ),
        cls="message assistant-message streaming-message"
    )

# ============================================
# Loading States
# ============================================

def loading_indicator():
    """Loading spinner"""
    return Div(
        Div(cls="spinner"),
        P("Thinking..."),
        cls="loading-indicator"
    )

def typing_indicator():
    """Typing dots animation"""
    return Div(
        Span("●", cls="dot"),
        Span("●", cls="dot"),
        Span("●", cls="dot"),
        cls="typing-indicator"
    )

# ============================================
# Error Messages
# ============================================

def error_message(message: str):
    """Error message component"""
    return Article(
        Div(
            Strong("⚠️ Error"),
            P(message),
        ),
        cls="message error-message",
        role="alert"
    )

def warning_message(message: str):
    """Warning message component"""
    return Article(
        Div(
            Strong("⚠️ Warning"),
            P(message),
        ),
        cls="message warning-message"
    )

# ============================================
# Empty States
# ============================================

def empty_conversations():
    """Empty state when no conversations exist"""
    return Div(
        P("No conversations yet."),
        P("Click 'New Chat' to start."),
        cls="empty-state"
    )

def empty_messages():
    """Empty state when conversation has no messages"""
    return Div(
        H3("Start a conversation"),
        P("Type your message below to begin."),
        cls="empty-state"
    )

# ============================================
# Conversation Components
# ============================================

def conversation_header(title: str, conversation_id: int):
    """Header for conversation"""
    return Header(
        H2(title),
        Button(
            "✏️",
            onclick=f"renameConversation({conversation_id})",
            title="Rename conversation",
            cls="icon-btn"
        ),
        cls="conversation-header"
    )

# ============================================
# Modal Dialogs
# ============================================

def confirmation_modal(title: str, message: str, confirm_action: str):
    """Confirmation dialog"""
    return Dialog(
        Article(
            Header(
                H3(title),
                Button(
                    "×",
                    cls="close",
                    onclick="closeModal()"
                )
            ),
            P(message),
            Footer(
                Button(
                    "Cancel",
                    cls="secondary",
                    onclick="closeModal()"
                ),
                Button(
                    "Confirm",
                    onclick=confirm_action
                )
            )
        ),
        id="modal"
    )