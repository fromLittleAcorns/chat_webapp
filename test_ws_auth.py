"""
Test WebSocket + Authentication
Phase 2: Add auth to confirm it doesn't break WebSockets
"""

from fasthtml.common import *
from fasthtml_auth import AuthManager
from anthropic import AsyncAnthropic
import os

# Setup with authentication
tlink = Script(src="https://cdn.tailwindcss.com")
dlink = Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@4.11.1/dist/full.min.css")

# Initialize auth
auth = AuthManager(
    db_path="data/test_auth.db",
    config={
        'allow_registration': True,
        'public_paths': [],
        'login_path': '/auth/login',
    }
)
db = auth.initialize()
beforeware = auth.create_beforeware()

# Create app with auth and WebSocket
app = FastHTML(
    hdrs=(tlink, dlink, picolink), 
    exts='ws',
    before=beforeware,
    secret_key="test-secret-key"
)

# Register auth routes
auth.register_routes(app)

# In-memory message storage
messages = []

# System prompt
sp = """You are a helpful and concise assistant."""

# Anthropic client
client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Chat message component
def ChatMessage(msg_idx):
    msg = messages[msg_idx]
    bubble_class = "chat-bubble-primary" if msg['role']=='user' else 'chat-bubble-secondary'
    chat_class = "chat-end" if msg['role']=='user' else 'chat-start'
    return Div(
        Div(msg['role'], cls="chat-header"),
        Div(msg['content'], 
            id=f"chat-content-{msg_idx}",
            cls=f"chat-bubble {bubble_class}"),
        id=f"chat-message-{msg_idx}",
        cls=f"chat {chat_class}"
    )

# Input field
def ChatInput():
    return Input(
        type="text", 
        name='msg', 
        id='msg-input',
        placeholder="Type a message",
        cls="input input-bordered w-full", 
        hx_swap_oob='true'
    )

# Main screen (protected by auth)
@app.route("/")
def get(req):
    user = req.scope.get('user')
    if not user:
        return RedirectResponse("/auth/login")
    
    page = Body(
        H1('Test WebSocket + Auth'),
        P(f"Logged in as: {user.username}"),
        A("Logout", href="/auth/logout", cls="btn btn-sm"),
        Hr(),
        Div(
            *[ChatMessage(msg_idx) for msg_idx, msg in enumerate(messages)],
            id="chatlist", 
            cls="chat-box h-[73vh] overflow-y-auto"
        ),
        Form(
            Group(ChatInput(), Button("Send", cls="btn btn-primary")),
            ws_send=True, 
            hx_ext="ws", 
            ws_connect="/wscon",
            cls="flex space-x-2 mt-2"
        ),
        cls="p-4 max-w-lg mx-auto"
    )
    return Title('Test WS + Auth'), page

# WebSocket handler
@app.ws('/wscon')
async def ws(msg: str, send):
    print(f"📨 Received message: {msg}")
    
    # Add user message
    messages.append({"role": "user", "content": msg.rstrip()})
    swap = 'beforeend'
    
    print(f"👤 Sending user message bubble")
    await send(Div(ChatMessage(len(messages)-1), hx_swap_oob=swap, id="chatlist"))
    
    print(f"🧹 Sending clear input")
    await send(ChatInput())
    
    print(f"🤖 Calling Anthropic API...")
    async with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=messages,
        system=sp
    ) as stream:
        print(f"✓ Stream opened")
        
        # Send empty assistant message
        messages.append({"role": "assistant", "content": ""})
        await send(Div(ChatMessage(len(messages)-1), hx_swap_oob=swap, id="chatlist"))
        print(f"📤 Empty assistant bubble sent")
        
        # Stream chunks
        chunk_count = 0
        async for text in stream.text_stream:
            chunk_count += 1
            messages[-1]["content"] += text
            await send(Span(text, id=f"chat-content-{len(messages)-1}", hx_swap_oob=swap))
            
            if chunk_count <= 3:
                print(f"📤 Chunk {chunk_count}: {text[:20]}")
        
        print(f"✅ Stream complete: {chunk_count} chunks")

if __name__ == '__main__':
    import uvicorn
    print("🚀 Starting test WebSocket + Auth app...")
    print("📍 Visit: http://localhost:5002")
    print("🔐 Default login: username='admin', password='admin123'")
    uvicorn.run("test_ws_auth:app", host='0.0.0.0', port=5002, reload=True)
