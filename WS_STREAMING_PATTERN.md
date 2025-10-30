# Matching ws_streaming.py Pattern

## What We Changed

Restructured our app to **exactly match** the working ws_streaming.py example's architecture.

## Key Architectural Change

### Before (Our Old Approach):
```
POST /api/chat/send
├── Returns user bubble
├── Returns empty assistant bubble (with ws_connect on it)
└── WebSocket opens and streams into that bubble

Problem: Assistant bubble created in POST, WebSocket just fills it
```

### After (ws_streaming Pattern):
```
POST /api/chat/send
├── Returns user bubble
└── Returns hidden WebSocket trigger

WebSocket opens:
├── First: Sends empty assistant bubble to messages container
└── Then: Streams chunks into that bubble's content div

Success: Everything sent via WebSocket, like the example!
```

## Changes Made

### 1. api.py - POST handler
```python
# OLD:
return Div(
    message_bubble('user', message, user_msg_idx),
    streaming_message_bubble(assistant_msg_idx, conv_id)  # ← Bubble with ws_connect
)

# NEW:
return Div(
    message_bubble('user', message, user_msg_idx),
    Div(hx_ext="ws", ws_connect=f"...", style="display:none")  # ← Just trigger
)
```

### 2. api.py - WebSocket handler
```python
# OLD:
async with stream:
    async for text in stream.text_stream:
        await send(Span(text, ...))  # ← Only sent chunks

# NEW:
# First: Send empty bubble
await send(Div(
    message_bubble('assistant', '', msg_idx),
    hx_swap_oob='beforeend',
    id='messages'
))

# Then: Send chunks
async with stream:
    async for text in stream.text_stream:
        await send(Span(text, ...))
```

## Why This Matches The Example

| Aspect | ws_streaming.py | Our New Code |
|--------|----------------|--------------|
| **POST returns** | User bubble only | User bubble + trigger ✓ |
| **WS sends bubble** | Yes, first thing | Yes, first thing ✓ |
| **WS streams chunks** | Into `chat-content-{idx}` | Into `content-{idx}` ✓ |
| **Target container** | `#chatlist` | `#messages` ✓ |
| **OOB swap** | `beforeend` | `beforeend` ✓ |
| **Async streaming** | `async for` | `async for` ✓ |

## Expected Behavior

### Server Logs:
```
📨 SEND MESSAGE
✅ Returning user message bubble and WebSocket trigger
🌊 WS START: msg_idx=1
📚 Loaded conversation history: 2 messages
📡 Getting MCP client...
✓ MCP client obtained
🎨 Sending empty assistant bubble to UI
✓ Empty bubble sent
🤖 Calling Claude API (async)...
✓ Claude stream opened, starting to receive chunks...
📤 Chunk 1: "I'll search..."
📤 Chunk 2: " for..."
...
✅ Stream complete: 120 chunks
💾 Saving complete response
✅ WebSocket stream finished successfully
```

### Browser Console:
```
🌊 WebSocket Connection Opened
🔄 HTMX afterSwap (empty bubble added)
🔄 HTMX afterSwap (chunk 1)
🔄 HTMX afterSwap (chunk 2)
...
🏁 WebSocket Connection Closed
```

### Visual:
- User bubble appears immediately ✓
- Empty assistant bubble appears (via WebSocket) ✓
- Text streams in token-by-token ✓
- No freezing ✓
- No infinite loops ✓

## This Should Work! 🎉

We're now following the **exact same pattern** as the proven working example!
