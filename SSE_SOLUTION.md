# SSE Streaming Solution (Adapted from ws_streaming.py)

## The Pattern from Working Example:

1. **Create empty assistant message first** with unique ID
2. **Stream chunks** as Span components with OOB swap to content div
3. **Use `hx_swap_oob='beforeend'`** to append each chunk

## Key Changes Needed:

### 1. components.py - streaming_message_bubble()
```python
def streaming_message_bubble(response_id: str, msg_idx: int):
    """Empty assistant bubble ready for streaming"""
    timestamp = datetime.now().strftime("%H:%M")
    
    return Article(
        Div(
            # Empty content div with unique ID for OOB targeting
            Div(
                # Typing indicator
                Div(
                    Span("●", cls="dot"),
                    Span("●", cls="dot"),
                    Span("●", cls="dot"),
                    cls="typing-indicator"
                ),
                id=f"stream-content-{msg_idx}",  # Target for chunks
                cls="message-content streaming"
            ),
            Small(f"Assistant • {timestamp}", cls="message-meta"),
        ),
        id=f"stream-message-{msg_idx}",  # Whole bubble ID
        cls="message assistant-message streaming-message"
    )
```

### 2. api.py - send_message()
```python
@app.post("/api/chat/send")
async def send_message(req, session, message: str):
    # ... validation ...
    
    # Save user message
    Message.create(conv_id, 'user', message)
    
    # Get message index for unique IDs
    msg_idx = Message.count_by_conversation(conv_id)
    
    # Return user message + empty assistant bubble
    return Div(
        message_bubble('user', message),
        streaming_message_bubble(str(uuid.uuid4()), msg_idx),
        
        # Trigger SSE connection via hidden div
        Div(
            hx_ext="sse",
            sse_connect=f"/api/chat/stream?conversation_id={conv_id}&message={message}&msg_idx={msg_idx}",
            style="display:none"
        )
    )
```

### 3. api.py - stream_response()
```python
@app.get("/api/chat/stream")
async def stream_response(req, session, conversation_id: int, message: str, msg_idx: int):
    """Stream using OOB swaps like WebSocket example"""
    
    async def generate():
        try:
            # Get MCP client and history
            mcp_client = get_mcp_client()
            history = Message.get_history(conversation_id)
            
            full_response = ""
            
            # Stream from Claude
            with mcp_client.send_message(history, stream=True) as stream:
                for chunk in stream.text_stream:
                    full_response += chunk
                    
                    # Send chunk as Span with OOB swap (like ws_streaming)
                    chunk_html = str(
                        Span(chunk, 
                             id=f"stream-content-{msg_idx}", 
                             hx_swap_oob="beforeend")
                    )
                    
                    # Wrap in SSE format
                    yield f"data: {chunk_html}\\n\\n"
                    await asyncio.sleep(0)
            
            # Save complete response
            Message.create(conversation_id, 'assistant', full_response)
            
            # Send close event
            yield "event: close\\ndata: \\n\\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            error_html = str(Div(f"Error: {e}", style="color: red;"))
            yield f"data: {error_html}\\n\\n"
            yield "event: close\\ndata: \\n\\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

## Why This Works:

1. **No SSE extension conflicts** - we're using SSE as a transport but OOB swaps for updates
2. **FastHTML pattern** - proven to work in the example
3. **Unique IDs** - each message content has its own target
4. **Components, not raw text** - sends HTML components with OOB swap attributes

## Implementation Steps:

1. Update `streaming_message_bubble()` to use message index
2. Update `send_message()` to pass msg_idx
3. Update `stream_response()` to send Span components with OOB swaps
4. Remove the SSE extension syntax (`sse-connect`, `sse-swap`) since we're using OOB
