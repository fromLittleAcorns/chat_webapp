# Fixing Async Blocking Issue

## The Problem

WebSocket connection opened but handler never executed - no logs appeared!

```
INFO: WebSocket /ws/chat/15/1" [accepted]
INFO: connection open
(nothing happens - hung!)
```

## Root Cause

**Synchronous DB operations in async function block the event loop:**

```python
# ❌ BLOCKING - sync call in async function
async def ws_chat(...):
    history = Message.get_history(conversation_id)  # ← Blocks entire event loop!
    ...
    Message.create(conversation_id, 'assistant', full_response)  # ← Also blocks!
```

## The Fix

Wrap sync operations in executor:

```python
# ✅ NON-BLOCKING - run sync code in thread pool
async def ws_chat(...):
    loop = asyncio.get_event_loop()
    
    # Run sync DB call without blocking
    history = await loop.run_in_executor(None, Message.get_history, conversation_id)
    ...
    await loop.run_in_executor(None, Message.create, conversation_id, 'assistant', full_response)
```

## Changes Made

### api.py - WebSocket Handler

1. **Import asyncio**
2. **Get event loop** at start
3. **Wrap Message.get_history()** in executor
4. **Wrap Message.create()** in executor

## Why The Example Works

The ws_streaming.py example uses a **global list** for messages - no database calls!

```python
messages = []  # In-memory, no blocking

async def ws(...):
    messages.append(...)  # Instant, no I/O
    async for chunk in r:
        messages[-1]["content"] += chunk  # Instant, no I/O
```

Our app uses **SQLite database** - I/O operations that block if not handled properly.

## Test With Uvicorn

Run with uvicorn (better async support than serve()):

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 5000
```

## Expected Behavior Now

**Server Logs:**
```
🌊 WS START: msg_idx=1
📚 Loaded conversation history: 2 messages
📡 Getting MCP client...
✓ MCP client obtained
🎨 Sending empty assistant bubble to UI
✓ Empty bubble sent
🤖 Calling Claude API (async)...
✓ Claude stream opened
📤 Chunk 1, 2, 3...
✅ Stream complete
💾 Saving complete response
✓ Response saved
✅ WebSocket stream finished successfully
```

**Browser:**
- User bubble appears
- Assistant bubble appears (via WebSocket)
- Text streams in
- No hanging! ✨

## Key Lesson

**In async functions, all I/O operations must be non-blocking:**
- Use `await` for async operations
- Use `run_in_executor()` for sync operations
- Otherwise you block the entire event loop!

This is why the example worked - no blocking I/O operations!
