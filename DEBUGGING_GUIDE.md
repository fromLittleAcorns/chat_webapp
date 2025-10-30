# SSE Debugging Guide

## How to Debug the Chat Streaming

### 1. Server Logs (Terminal)

When you send a message, you should see this sequence:

```
📨 SEND MESSAGE: user=admin, conv=1, msg_len=51
🆔 Generated response_id: abc-123-def-456
✅ Returning HTML with SSE placeholder for response_id=abc-123-def-456
🎨 Creating streaming bubble: id=stream-abc-123-def-456, url=/api/chat/stream?...
🌊 STREAM START: response_id=abc-123-def-456, conv=1, user=admin
📚 Loaded conversation history: 2 messages
🔄 Generator started for response_id=abc-123-def-456
📡 Getting MCP client...
✓ MCP client obtained
🤖 Calling Claude API...
✓ Claude stream opened, starting to receive chunks...
📤 Chunk 1: 'I' -> SSE: 'data: I\n\n'
📤 Chunk 2: ' can' -> SSE: 'data:  can\n\n'
📤 Chunk 3: ' help' -> SSE: 'data:  help\n\n'
... (more chunks)
📤 Chunk 20 (every 20th logged)
✅ Stream complete: 45 chunks, 234 chars
💾 Saving complete response to database...
✓ Response saved
🏁 Sending close event
✅ Stream finished successfully
```

### 2. Browser Console Logs (DevTools)

Open browser DevTools (F12) → Console tab. You should see:

```
🚀 Chat scripts loaded
✅ All event listeners registered
✅ Window loaded, focusing input
⏳ HTMX beforeRequest: messages
📨 HTMX afterRequest: {target: "messages", elt: "FORM", successful: true, xhr_status: 200}
✅ Form submitted successfully, clearing input
🔄 HTMX afterSwap: messages
🔗 SSE bubble created: stream-abc-123-def-456 {url: '/api/chat/stream?...', swap: 'message'}
🌊 SSE Connection Opened: {...}
📥 SSE Message Received: {data: 'I...', target: 'stream-abc-123-def-456'}
📥 SSE Message Received: {data: ' can...', target: 'stream-abc-123-def-456'}
... (more messages)
🏁 SSE Connection Closed: {...}
```

### 3. Browser Network Tab

Check DevTools → Network tab:

1. **First request**: POST to `/api/chat/send`
   - Status: 200
   - Response: HTML with user message + streaming placeholder

2. **Second request**: GET to `/api/chat/stream`
   - Type: `eventsource` (SSE)
   - Status: 200
   - Connection stays open
   - In Preview/Response: streaming text chunks

### What to Look For

#### ✅ SUCCESS Indicators:
- Input box clears after sending
- Server logs show all emojis from 📨 to ✅
- Browser console shows 🌊 (SSE opened) and 📥 (messages received)
- Text appears token-by-token in assistant bubble
- Network tab shows `eventsource` connection

#### ❌ FAILURE Indicators:

**If input doesn't clear:**
- Check browser console for afterRequest event
- Should see: `✅ Form submitted successfully, clearing input`

**If SSE never opens:**
- Check for `🌊 SSE Connection Opened` in browser console
- Check Network tab for `/api/chat/stream` request
- Look for `❌ SSE Error` in console

**If streaming hangs:**
- Check server logs - does it reach `🤖 Calling Claude API...`?
- Check if chunks are being received: `📤 Chunk N`
- Check browser console for `📥 SSE Message Received`

**If nothing appears but server completes:**
- SSE event name mismatch! 
- Server sends `data:` but should send `event: message\ndata:`
- Browser expects events named "message" (from `sse-swap="message"`)

### Common Issues

1. **Event Name Mismatch**: Server sends unnamed events, HTMX expects "message"
2. **URL Encoding**: Special characters in message break URL
3. **Buffering**: ASGI server buffers SSE responses
4. **CORS/Headers**: Missing SSE headers

### Quick Fixes to Try

If the logging shows the server is streaming but nothing appears in browser:

```python
# In api.py, line ~133, change:
yield f"data: {text}\n\n"

# To:
yield f"event: message\ndata: {text}\n\n"
```

This adds the event name that HTMX is listening for.
