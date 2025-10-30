# AsyncAnthropic Implementation

## Problem

WebSocket was freezing because we were using a **synchronous** Anthropic client (`with mcp_client.send_message()`) inside an **async** WebSocket handler, which **blocked the event loop**.

## Solution

Use Anthropic's `AsyncAnthropic` client with `async with` and `async for`.

## Changes Made

### 1. mcp_client.py - Added AsyncAnthropic Client

```python
# Added import
from anthropic import Anthropic, AsyncAnthropic

# In __init__:
self.async_client = AsyncAnthropic(
    api_key=api_key,
    default_headers={
        "anthropic-beta": "mcp-client-2025-04-04"
    }
)

# New async method:
async def send_message_async(self, messages: list, stream: bool = True):
    """Async version for WebSocket streaming"""
    ...
    if stream:
        return self.async_client.messages.stream(**params)
    else:
        return await self.async_client.messages.create(**params)
```

### 2. api.py - Use Async Streaming

```python
# OLD (blocking):
with mcp_client.send_message(history, stream=True) as stream:
    for text in stream.text_stream:
        await send(...)

# NEW (non-blocking):
async with mcp_client.send_message_async(history, stream=True) as stream:
    async for text in stream.text_stream:
        await send(...)
```

## Why This Works

1. **No Event Loop Blocking**: `async for` yields control between chunks
2. **Native Async**: AsyncAnthropic is designed for async/await
3. **Like the Working Example**: Same pattern as ws_streaming.py
4. **No Threading Needed**: Pure async, no ThreadPoolExecutor hacks

## What to Test

**Restart your app** and send a message:

### Expected Behavior:
- ✅ No freezing!
- ✅ Text streams in token-by-token  
- ✅ WebSocket stays responsive
- ✅ Clean connection close

### Server Logs:
```
🌊 WS START: msg_idx=1
📚 Loaded conversation history: 2 messages
📡 Getting MCP client...
✓ MCP client obtained
🤖 Calling Claude API (async)...
✓ Claude stream opened, starting to receive chunks...
📤 Chunk 1: "I'll search..."
📤 Chunk 2: " for..."
...
✅ Stream complete: 120 chunks, 3491 chars
💾 Saving complete response to database...
✓ Response saved
✅ WebSocket stream finished successfully
```

### Browser Console:
```
🌊 WebSocket Connection Opened
🔄 HTMX afterSwap (multiple times as chunks arrive)
📜 Scrolled to bottom (updates as text appears)
🏁 WebSocket Connection Closed
```

## No New Libraries Needed! 🎉

`AsyncAnthropic` is part of the same `anthropic` package you already have installed.

This is the **proper FastHTML + AsyncAnthropic pattern** - clean, simple, and non-blocking!
