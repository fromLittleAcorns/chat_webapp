# HTMX 2.x Upgrade

## What Changed

Upgraded from HTMX 1.9.x + SSE extension to HTMX 2.x with built-in SSE support.

### Reason for Upgrade

The HTMX 1.9.x SSE extension had a compatibility issue:
```
Uncaught TypeError: api.selectAndSwap is not a function
```

HTMX 2.x has native SSE support built-in, which is more stable and doesn't require an external extension.

## Changes Made

### 1. app.py - Updated Headers
```python
# OLD (HTMX 1.9.x)
Script(src="https://unpkg.com/htmx.org@1.9.10/dist/ext/sse.js"),

# NEW (HTMX 2.x - no extension needed!)
Script(src="https://unpkg.com/htmx.org@2.0.3"),
```

### 2. components.py - Updated SSE Syntax
```python
# OLD (HTMX 1.9.x extension syntax)
**{
    "hx-ext": "sse",
    "sse-connect": sse_url,
    "sse-swap": "message"
}

# NEW (HTMX 2.x built-in syntax)
**{
    "hx-sse": f"connect:{sse_url} swap:message"
}
```

### 3. chat.py - Added HTMX 2.x Event Logging
Added `htmx:sseBeforeMessage` event listener for HTMX 2.x compatibility.

## Server-Side (No Changes Needed)

The SSE format remains the same:
```python
yield f"event: message\ndata: {text}\n\n"
yield "event: close\ndata: \n\n"
```

HTMX 2.x understands the same SSE protocol as 1.9.x.

## Testing

After restart, you should see in browser console:
- No `api.selectAndSwap` errors
- SSE events being received
- Text streaming properly into the assistant bubble

## Rollback (if needed)

If HTMX 2.x causes issues, you can rollback by:

1. In `app.py`, change back to:
```python
Script(src="https://unpkg.com/htmx.org@1.9.10"),
Script(src="https://unpkg.com/htmx.org@1.9.10/dist/ext/sse.js"),
```

2. In `components.py`, change back to:
```python
**{
    "hx-ext": "sse",
    "sse-connect": sse_url,
    "sse-swap": "message"
}
```

But the version mismatch error will return.
