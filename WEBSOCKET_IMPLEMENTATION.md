# WebSocket Implementation - Simple & Clean

## What We Changed

Converted from SSE (Server-Sent Events) to **WebSockets** following the proven FastHTML ws_streaming.py pattern.

## Key Changes

### 1. app.py - Enable WebSocket Extension
```python
# OLD: SSE extension
Script(src="https://unpkg.com/htmx.org@1.9.10/dist/ext/sse.js"),

# NEW: WebSocket support
app = FastHTML(
    ...
    exts='ws'  # Enable WebSocket support
)
```

### 2. components.py - WebSocket Connection
```python
# OLD: SSE with complex attributes
def streaming_message_bubble(msg_idx):
    ...
    hx_ext="sse",
    sse_connect=f"/api/chat/stream?...",
    sse_swap="message"

# NEW: Simple WebSocket connection
def streaming_message_bubble(msg_idx, conv_id):
    ...
    hx_ext="ws",
    ws_connect=f"/ws/chat/{conv_id}/{msg_idx}"
```

### 3. api.py - WebSocket Endpoint
```python
# OLD: SSE with StreamingResponse
@app.get("/api/chat/stream")
async def stream_response(...):
    async def generate():
        yield f"event: message\ndata: {text}\n\n"
    return StreamingResponse(generate(), ...)

# NEW: WebSocket with async send
@app.ws('/ws/chat/{conversation_id}/{msg_idx}')
async def ws_chat(conversation_id, msg_idx, send):
    for text in stream.text_stream:
        await send(Span(text, id=f"content-{msg_idx}", hx_swap_oob="beforeend"))
```

### 4. chat.py - WebSocket Events
```python
# OLD: SSE events
htmx:sseOpen
htmx:sseMessage
htmx:sseClose
htmx:sseError

# NEW: WebSocket events
htmx:wsOpen
htmx:wsClose
htmx:wsError
```

## Why This Works

1. **No Version Conflicts**: FastHTML's built-in WebSocket support, no external extensions
2. **Proven Pattern**: Copied directly from working ws_streaming.py example
3. **OOB Swaps**: Same pattern - send Span components with `hx_swap_oob="beforeend"`
4. **Simpler**: No SSE event names, no connection management, no close events needed

## Differences from SSE

| Feature | SSE | WebSocket |
|---------|-----|-----------|
| Extension | External (sse.js) | Built-in (`exts='ws'`) |
| Transport | HTTP | WebSocket |
| Direction | Server → Client | Bidirectional |
| Format | Text events | HTML components |
| Reconnect | Automatic (need to prevent) | Managed by HTMX |
| Complexity | Medium | Low |

## Expected Behavior

1. User sends message ✓
2. Empty assistant bubble appears ✓
3. WebSocket connection opens ✓
4. Text streams in chunk-by-chunk ✓
5. No `api.selectAndSwap` error ✓
6. No infinite reconnection ✓
7. Connection closes cleanly ✓

## Test This First!

If WebSockets work perfectly, then we know:
- ✅ Message indices work
- ✅ OOB swaps work  
- ✅ Streaming works
- ✅ Database saves work
- ✅ UI updates work

Then the SSE issue is specifically the version conflict between HTMX and the SSE extension.

## If We Need SSE Later

We can troubleshoot by:
1. Finding the exact HTMX version FastHTML uses
2. Using a compatible SSE extension version
3. Or using HTMX 2.x which has built-in SSE support

But let's validate WebSockets work first! 🚀
