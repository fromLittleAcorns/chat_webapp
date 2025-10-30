# FastHTML OOB Swap Implementation - Complete Summary

## What We Changed

Implemented the **FastHTML pattern** from the working ws_streaming.py example, adapted for SSE instead of WebSockets.

## Key Changes

### 1. **Message Bubbles Now Have Unique IDs** (components.py)

```python
# Before: No IDs
def message_bubble(role: str, content: str):
    return Article(Div(Div(content, cls="message-content"), ...))

# After: Unique IDs for targeting
def message_bubble(role: str, content: str, msg_idx: int = None):
    return Article(
        Div(
            Div(content, id=f"content-{msg_idx}", ...),  # ← Target for OOB swaps
            ...
        ),
        id=f"msg-{msg_idx}",  # ← Whole message ID
        ...
    )
```

### 2. **Simplified Streaming Bubble** (components.py)

```python
# Before: Complex SSE extension attributes
def streaming_message_bubble(response_id, conversation_id, user_message):
    return Article(
        Div(
            Div(
                ...,
                hx_ext="sse",
                sse_connect=f"/api/chat/stream?...",
                sse_swap="message"  # ← Tried to use SSE extension's swap
            )
        )
    )

# After: Simple empty bubble with target ID
def streaming_message_bubble(msg_idx: int):
    return Article(
        Div(
            Div(
                # Typing indicator
                ...,
                id=f"content-{msg_idx}",  # ← Target for OOB swaps
                cls="message-content streaming"
            )
        ),
        id=f"msg-{msg_idx}"
    )
```

### 3. **Send Message Uses Message Indices** (api.py)

```python
# Before: Random UUID
response_id = str(uuid.uuid4())
streaming_message_bubble(response_id, conv_id, message)

# After: Message index from database
msg_count = Message.count_by_conversation(conv_id)
assistant_msg_idx = msg_count  # Next message will be this index
streaming_message_bubble(assistant_msg_idx)

# Hidden SSE trigger
Div(
    hx_ext="sse",
    sse_connect=f"/api/chat/stream?conversation_id={conv_id}&msg_idx={assistant_msg_idx}",
    style="display:none"
)
```

### 4. **Stream Response Sends HTML Components with OOB Swaps** (api.py)

```python
# Before: Raw text with SSE event names
yield f"event: message\ndata: {text}\n\n"

# After: HTML components with OOB swap attributes (FastHTML pattern!)
chunk_component = Span(
    text,
    id=f"content-{msg_idx}",
    hx_swap_oob="beforeend"  # ← HTMX appends to target
)
chunk_html = str(chunk_component)
yield f"data: {chunk_html}\n\n"
```

## Why This Works

### The FastHTML Way:
1. **Unique IDs**: Every message content div has `id="content-{idx}"`
2. **OOB Swaps**: Components sent via SSE include `hx_swap_oob="beforeend"`
3. **HTMX Magic**: HTMX sees the OOB attribute and appends content to the target ID
4. **No Extension Conflicts**: We're using SSE as a transport, OOB for updates

### From ws_streaming.py Pattern:
```python
# WebSocket version (from example):
async for chunk in r:
    messages[-1]["content"] += chunk
    await send(Span(chunk, id=f"chat-content-{len(messages)-1}", hx_swap_oob='beforeend'))

# Our SSE version (adapted):
for text in stream.text_stream:
    full_response += text
    chunk_component = Span(text, id=f"content-{msg_idx}", hx_swap_oob="beforeend")
    yield f"data: {str(chunk_component)}\n\n"
```

## What We Removed

- ❌ SSE extension's `sse-swap` mechanism (was causing `api.selectAndSwap` errors)
- ❌ Random UUIDs (using message indices instead)
- ❌ Complex SSE connection attributes on bubble (moved to hidden trigger)
- ❌ `event: message` prefixes (OOB swaps don't need them)

## What We Kept

- ✅ SSE extension for connection (`hx_ext="sse"`, `sse_connect`)
- ✅ Server-side streaming with Anthropic SDK
- ✅ All logging and debugging
- ✅ Database save after stream completes

## Expected Behavior

1. User sends message → saved with index N
2. Server returns:
   - User bubble with `id="msg-N"`
   - Empty assistant bubble with `id="msg-N+1"`, `content-N+1`
   - Hidden SSE trigger
3. SSE connection opens to `/api/chat/stream?msg_idx=N+1`
4. Server streams chunks as: `<span id="content-N+1" hx-swap-oob="beforeend">text</span>`
5. HTMX appends each chunk to `content-N+1` div
6. Text appears token-by-token in assistant bubble ✨
7. Stream closes, response saved to database

## Testing

Restart app and send a message. Check:
- ✅ Input clears immediately
- ✅ Empty assistant bubble appears
- ✅ Text streams in token-by-token
- ✅ No `api.selectAndSwap` error
- ✅ No infinite reconnection loop
- ✅ Server logs show OOB swap HTML
- ✅ Browser console shows no errors

## This is the FastHTML Way! 🎉

Simple, clean, following proven patterns from the official examples.
