"""
Reusable UI Components

Building blocks for the chat interface.
"""

from fasthtml.common import *
from datetime import datetime

# ============================================
# Message Bubbles (DaisyUI)
# ============================================

def message_bubble(role: str, content: str, msg_idx: int = None, conv_id: int = None, for_streaming: bool = False):
    """
    DaisyUI chat bubble with unique ID
    
    Args:
        role: 'user' or 'assistant'
        content: Message text (will be rendered as markdown for assistant)
        msg_idx: Message index for unique ID (optional)
        conv_id: Conversation ID for globally unique IDs (optional)
        for_streaming: If True, add id to content div for streaming chunks
    """
    
    is_user = role == 'user'
    timestamp = datetime.now().strftime("%H:%M")
    
    # Include conv_id in IDs for global uniqueness
    if msg_idx is not None and conv_id is not None:
        bubble_id = f"msg-{conv_id}-{msg_idx}"
        content_id = f"content-{conv_id}-{msg_idx}" if for_streaming else None
    elif msg_idx is not None:
        # Fallback for compatibility
        bubble_id = f"msg-{msg_idx}"
        content_id = f"content-{msg_idx}" if for_streaming else None
    else:
        bubble_id = None
        content_id = None
    
    # DaisyUI chat classes
    chat_class = "chat-end" if is_user else "chat-start"
    bubble_class = "chat-bubble-primary" if is_user else "chat-bubble-secondary"
    
    # Render markdown for assistant messages (when loading from database)
    if role == 'assistant' and not for_streaming and content:
        from monsterui.franken import render_md
        rendered_content = NotStr(render_md(content))
    else:
        rendered_content = content
    
    return Div(
        # Chat header (role label)
        Div(role.capitalize(), cls="chat-header"),
        
        # Chat bubble with content
        Div(
            rendered_content,
            id=content_id,
            cls=f"chat-bubble {bubble_class}"
        ),
        
        # Chat footer (timestamp)
        Div(timestamp, cls="chat-footer opacity-50"),
        
        id=bubble_id,
        cls=f"chat {chat_class}",
        data_role=role,
        data_msg_idx=str(msg_idx) if msg_idx is not None else None,
        data_conv_id=str(conv_id) if conv_id is not None else None
    )

def streaming_message_bubble(msg_idx: int, conv_id: int):
    """
    Empty assistant bubble ready for streaming via WebSocket (DaisyUI)
    
    Args:
        msg_idx: Message index for unique ID targeting
        conv_id: Conversation ID for WebSocket connection
    """
    import logging
    logger = logging.getLogger(__name__)
    
    timestamp = datetime.now().strftime("%H:%M")
    
    logger.info(f"🎨 Creating empty streaming bubble: msg-{conv_id}-{msg_idx}, content-{conv_id}-{msg_idx}")
    
    return Div(
        # Chat header
        Div("Assistant", cls="chat-header"),
        
        # Chat bubble with streaming content
        Div(
            # Empty content that will be filled
            Span("", id=f"content-{conv_id}-{msg_idx}"),
            
            # Typing indicator
            Span(
                Span(cls="loading loading-dots loading-sm"),
                id=f"typing-{conv_id}-{msg_idx}",
                cls="ml-2"
            ),
            
            cls="chat-bubble chat-bubble-secondary",
            # WebSocket connection
            hx_ext="ws",
            ws_connect=f"/ws/chat/{conv_id}/{msg_idx}"
        ),
        
        # Chat footer
        Div(timestamp, cls="chat-footer opacity-50"),
        
        id=f"msg-{conv_id}-{msg_idx}",
        cls="chat chat-start",
        data_role="assistant",
        data_msg_idx=str(msg_idx),
        data_conv_id=str(conv_id)
    )

# ============================================
# Loading States
# ============================================

def loading_indicator():
    """DaisyUI loading spinner"""
    return Div(
        Span(cls="loading loading-spinner loading-lg text-primary"),
        P("Thinking...", cls="mt-4"),
        cls="flex flex-col items-center justify-center p-8"
    )

def typing_indicator():
    """DaisyUI typing dots animation"""
    return Span(cls="loading loading-dots loading-sm")

# ============================================
# Error Messages
# ============================================

def error_message(message: str):
    """Error message component using DaisyUI alert"""
    return Div(
        Div(
            Svg(
                Path(stroke_linecap="round", stroke_linejoin="round", stroke_width="2", 
                     d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"),
                xmlns="http://www.w3.org/2000/svg",
                cls="stroke-current shrink-0 h-6 w-6",
                fill="none",
                viewBox="0 0 24 24"
            ),
            Span(message),
            cls="flex items-center gap-2"
        ),
        cls="alert alert-error",
        role="alert"
    )

def warning_message(message: str):
    """Warning message component using DaisyUI alert"""
    return Div(
        Div(
            Svg(
                Path(stroke_linecap="round", stroke_linejoin="round", stroke_width="2",
                     d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"),
                xmlns="http://www.w3.org/2000/svg",
                cls="stroke-current shrink-0 h-6 w-6",
                fill="none",
                viewBox="0 0 24 24"
            ),
            Span(message),
            cls="flex items-center gap-2"
        ),
        cls="alert alert-warning"
    )

# ============================================
# Empty States
# ============================================

def empty_conversations():
    """Empty state when no conversations exist"""
    return Div(
        P("No conversations yet.", cls="text-base-content/70"),
        P("Click 'New Chat' to start.", cls="text-sm text-base-content/50"),
        cls="text-center p-4"
    )

def empty_messages():
    """Empty state when conversation has no messages"""
    return Div(
        H3("Start a conversation", cls="text-xl font-bold"),
        P("Type your message below to begin.", cls="text-base-content/70 mt-2"),
        cls="text-center p-8"
    )

# ============================================
# Conversation Components
# ============================================

def conversation_header(title: str, conversation_id: int):
    """Header for conversation"""
    return Div(
        H2(title, cls="text-2xl font-bold"),
        Button(
            "✏️",
            onclick=f"renameConversation({conversation_id})",
            title="Rename conversation",
            cls="btn btn-ghost btn-sm"
        ),
        cls="flex items-center justify-between p-4 border-b"
    )

# ============================================
# Modal Dialogs
# ============================================

def confirmation_modal(title: str, message: str, confirm_action: str):
    """Confirmation dialog using DaisyUI modal"""
    return Div(
        Div(
            H3(title, cls="font-bold text-lg"),
            P(message, cls="py-4"),
            Div(
                Button(
                    "Cancel",
                    cls="btn",
                    onclick="closeModal()"
                ),
                Button(
                    "Confirm",
                    cls="btn btn-primary",
                    onclick=confirm_action
                ),
                cls="modal-action"
            ),
            cls="modal-box"
        ),
        id="modal",
        cls="modal"
    )
