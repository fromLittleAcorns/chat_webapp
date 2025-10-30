# Systematic Debugging Plan

## Goal
Start with a **proven working pattern** and incrementally add complexity until we find what breaks.

## Phase 1: Validate WebSocket Works

### Test 1: Run test_ws.py
```bash
cd /Users/johnri/projects/chat_webapp
python test_ws.py
```

Visit: http://localhost:5001

**Expected:**
- ✅ Input clears after sending
- ✅ User bubble appears
- ✅ Assistant bubble appears  
- ✅ Text streams in
- ✅ Server logs show all emoji markers

**If it works:** WebSockets are working! Problem is in our main app.  
**If it fails:** WebSocket issue or environment issue.

---

## Phase 2: Add Authentication (If Test 1 Works)

### Test 2: Add auth to test_ws.py

Modify test_ws.py to use our auth system:
```python
from fasthtml_auth import AuthManager

auth = AuthManager(db_path="data/test_auth.db", config={'allow_registration': True})
db = auth.initialize()
beforeware = auth.create_beforeware()

app = FastHTML(hdrs=(...), exts='ws', before=beforeware)
auth.register_routes(app)
```

**Test:** Does it still work with authentication?

**If it works:** Auth isn't the problem.  
**If it fails:** Auth interferes with WebSockets.

---

## Phase 3: Add Database Storage (If Test 2 Works)

### Test 3: Replace in-memory list with database

Keep AsyncAnthropic but save messages to our database:
```python
# Replace:
messages = []
messages.append(...)

# With:
Message.create(conv_id, 'user', msg)
history = Message.get_history(conv_id)
```

Use `run_in_executor()` for DB calls.

**Test:** Does streaming still work?

**If it works:** Database isn't the problem.  
**If it fails:** DB operations block WebSocket.

---

## Phase 4: Add MCP Client (If Test 3 Works)

### Test 4: Use our MCP client

```python
mcp_client = get_mcp_client()
async with mcp_client.send_message_async(history, stream=True) as stream:
    ...
```

**Test:** Does streaming still work?

**If it works:** MCP client isn't the problem.  
**If it fails:** Something in MCP client blocks.

---

## Phase 5: Integrate into Main App (If Test 4 Works)

### Test 5: Replace our WebSocket handler with working code

Copy the working handler from test_ws.py into our main app's api.py.

**Test:** Does it work in the main app?

**If it works:** SUCCESS! Use this pattern.  
**If it fails:** Something else in main app interferes.

---

## Diagnostic Checklist

At each failing test, check:

### Server Logs
- Does WebSocket handler execute at all?
- Where does it stop?
- Any exceptions?

### Browser Console  
- Does WebSocket open?
- Any JavaScript errors?
- HTMX events firing?

### Network Tab → WS
- Connection established?
- Messages being sent/received?
- What's the content?

### HTML Inspection
- Is the `hx-ext="ws"` attribute present?
- Is `ws_connect` URL correct?
- Does target element exist?

---

## Expected Outcome

By following this plan, we'll identify **exactly** which component causes the failure:
1. ✅ Basic WebSocket
2. ✅ + Authentication
3. ✅ + Database
4. ✅ + MCP Client
5. ❌ Integration → **This is where it breaks**

Then we fix that specific issue!

---

## Start Here

**Run test_ws.py now:**
```bash
python test_ws.py
```

Send a message and report back:
1. Does it work?
2. What do server logs show?
3. What does browser show?

This will tell us if WebSockets work at all in your environment! 🎯
