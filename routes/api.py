"""
Chat API Routes

API endpoints for sending messages and streaming responses.
"""

from fasthtml.common import *
from starlette.responses import StreamingResponse
from models import Conversation, Message, validate_conversation_access
from services.mcp_client import get_mcp_client
from templates.components import message_bubble, streaming_message_bubble
from datetime import datetime
import asyncio
import uuid

# ============================================
# Routes
# ============================================

def get_routes():
    """Return list of route registration functions"""
    return [
        register_send_route,
        register_stream_route
    ]

# ============================================
# Send Message
# ============================================

def register_send_route(app):
    
    @app.post("/api/chat/send")
    @app.require_auth
    async def send_message(session, message: str):
        """
        Handle sending a message and initiating streaming response
        """
        user = session.get('user')
        conv_id = session.get('current_conversation_id')
        
        # Validate
        if not message or len(message.strip()) == 0:
            return Div("Please enter a message.", style="color: red;")
        
        if len(message) > 10000:
            return Div("Message too long (max 10,000 characters).", style="color: red;")
        
        try:
            validate_conversation_access(conv_id, user['id'])
        except ValueError:
            return Div("Invalid conversation.", style="color: red;")
        
        # Save user message
        Message.create(conv_id, 'user', message)
        
        # Generate unique ID for streaming response
        response_id = str(uuid.uuid4())
        
        # Auto-generate title for first message
        msg_count = Message.count_by_conversation(conv_id)
        if msg_count == 1:  # First message
            # Use first few words as title
            title = message[:50] + ("..." if len(message) > 50 else "")
            Conversation.update_title(conv_id, title)
        
        # Return user message + streaming placeholder
        return Div(
            # User message bubble
            message_bubble('user', message),
            
            # Assistant message placeholder with SSE connection
            streaming_message_bubble(response_id, conv_id, message)
        )

# ============================================
# Stream Response
# ============================================

def register_stream_route(app):
    
    @app.get("/api/chat/stream")
    @app.require_auth
    async def stream_response(session, response_id: str, conversation_id: int, message: str):
        """
        Stream Claude's response using Server-Sent Events (SSE)
        """
        user = session.get('user')
        
        # Validate access
        try:
            validate_conversation_access(conversation_id, user['id'])
        except ValueError:
            async def error_stream():
                yield "data: Error: Unauthorized access\n\n"
                yield "event: close\ndata: \n\n"
            return StreamingResponse(error_stream(), media_type="text/event-stream")
        
        # Get conversation history
        history = Message.get_history(conversation_id)
        
        async def generate():
            """Generate streaming response"""
            try:
                # Get MCP client
                mcp_client = get_mcp_client()
                
                # Stream response from Claude
                full_response = ""
                
                async with mcp_client.send_message(history, stream=True) as stream:
                    async for text in stream.text_stream:
                        full_response += text
                        # Send chunk to client
                        yield f"data: {text}\n\n"
                        await asyncio.sleep(0)  # Allow other tasks to run
                
                # Save complete assistant response
                Message.create(conversation_id, 'assistant', full_response)
                
                # Signal completion
                yield "event: close\ndata: \n\n"
                
            except Exception as e:
                import logging
                logging.error(f"Streaming error: {e}")
                yield f"data: [Error: {str(e)}]\n\n"
                yield "event: close\ndata: \n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )