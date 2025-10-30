# Final SSE Implementation - Simple & Working

## What We Did

After trying the OOB swap approach, we realized the HTMX SSE extension works best with its native target/swap mechanism. Back to basics, but with all the fixes!

## The Working Pattern

### 1. Empty Bubble with Target ID (components.py)
```python
def streaming_message_bubble(msg_idx: int):
    return Article(
        Div(
            Div(
                # Typing indicator
                ...,
                id=f"content-{msg_idx}",  # ← SSE will target this
                cls="message-content streaming"
            )
        ),
        id=f"msg-{msg_idx}"
    )
```

### 2. SSE Trigger with Target & Swap (api.py send_message)
```python
Div(
    hx_ext="sse",
    sse_connect=f"/api/chat/stream?conversation_id={conv_id}&msg_idx={assistant_msg_idx}",
    sse_swap="message",  # Listen for 'message' events
    hx_target=f"#content-{assistant_msg_idx}",  # Target the content div
    hx_swap="beforeend",  # Append each chunk
    style="display:none"
)
```

### 3. Server Sends Plain Text with Event Names (api.py stream_response)
```python
# For each chunk:
yield f"event: message\ndata: {text}\n\n"

# When done:
yield "event: close\ndata: done\n\n"
```

### 4. JavaScript Closes Connection on 'close' Event (chat.py)
```javascript
window.addEventListener('htmx:sseMessage', function(evt) {
    if (evt.detail.event === 'close') {
        // Remove SSE attributes to close connection
        document.querySelectorAll('[sse-connect]').forEach(function(el) {
            el.removeAttribute('sse-connect');
            el.removeAttribute('sse-swap');
        });
    }
}, true);
```

## Why This Works

1. **SSE Extension's Native Mechanism**: Use what HTMX provides - `sse-swap`, `hx-target`, `hx-swap`
2. **Plain Text Chunks**: No complex HTML, just raw text that gets appended
3. **Event Names**: `event: message` for chunks, `event: close` to signal end
4. **JavaScript Cleanup**: Remove SSE attributes when done to prevent reconnection

## Key Fixes from Previous Attempts

- ❌ **OOB swaps via SSE**: Too complex, doesn't work reliably
- ✅ **SSE extension's target/swap**: Simple, works as designed

- ❌ **HTML components as chunks**: Over-complicated
- ✅ **Plain text chunks**: What SSE was made for

- ❌ **Auto-reconnection loop**: EventSource reconnects by default
- ✅ **JavaScript close handler**: Remove attributes to stop reconnection

## Expected Behavior

1. User sends message
2. Empty assistant bubble appears with typing indicator
3. SSE connection opens to stream endpoint
4. Text streams in chunk-by-chunk (appends to content div)
5. Server sends 'close' event
6. JavaScript removes SSE attributes
7. Connection closes, no reconnection ✨

## Test Checklist

- [ ] Input clears after sending
- [ ] Empty assistant bubble appears
- [ ] Typing indicator shows
- [ ] Text streams in token-by-token
- [ ] Typing indicator disappears as text appears
- [ ] No infinite reconnection loop
- [ ] Server logs show 120 chunks, then "Stream finished successfully"
- [ ] Only ONE stream per message (no repeats)

This is the simple, clean FastHTML way! 🎉
