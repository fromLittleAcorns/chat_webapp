"""
Test WebSocket + Auth + Database
Phase 3: Add database operations to see if they block WebSocket
"""

from fasthtml.common import *
from fasthtml_auth import AuthManager
from anthropic import AsyncAnthropic
from models import init_database, Conversation, Message
import os
import asyncio

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

# Initialize database
init_database()

# Create app with auth and WebSocket
app = FastHTML(
    hdrs=(tlink, dlink, picolink), 
    exts='ws',
    before=beforeware,
    secret_key="test-secret-key"
)

# Register auth routes
auth.register_routes(app)

# System prompt
sp = """You are a helpful and concise assistant."""

# Anthropic client
client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Chat message component
def ChatMessage(msg_idx, role, content):
    bubble_class = "chat-bubble-primary" if role=='user' else 'chat-bubble-secondary'
    chat_class = "chat-end" if role=='user' else 'chat-start'
    return Div(
        Div(role, cls="chat-header"),
        Div(content, 
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
def get(req, session):
    user = req.scope.get('user')
    if not user:
        return RedirectResponse("/auth/login")
    
    # Get or create conversation
    conv_id = session.get('test_conv_id')
    if not conv_id:
        conv = Conversation.create(user.id, "Test Chat")
        conv_id = conv.id
        session['test_conv_id'] = conv_id
    
    # Get messages from database
    messages = Message.get_by_conversation(conv_id)
    
    page = Body(
        H1('Test WebSocket + Auth + Database'),
        P(f"Logged in as: {user.username} | Conversation: {conv_id}"),
        A("Logout", href="/auth/logout", cls="btn btn-sm"),
        Hr(),
        Div(
            *[ChatMessage(idx, msg.role, msg.content) for idx, msg in enumerate(messages)],
            id="chatlist", 
            cls="chat-box h-[73vh] overflow-y-auto"
        ),
        Form(
            Group(ChatInput(), Button("Send", cls="btn btn-primary")),
            ws_send=True, 
            hx_ext="ws", 
            ws_connect="/wscon",  # No path parameter!
            cls="flex space-x-2 mt-2"
        ),
        cls="p-4 max-w-lg mx-auto"
    )
    return Title('Test WS + Auth + DB'), page

# WebSocket handler
@app.ws('/wscon')
async def ws(msg: str, send, session):  # Get session instead of path param
    print(f"📨 Received message: {msg}")
    
    # Get conversation_id from session
    conversation_id = session.get('test_conv_id')
    if not conversation_id:
        print("❌ No conversation ID in session!")
        await send(Div("Error: No conversation found", style="color: red;"))
        return
    
    print(f"📁 Conversation ID: {conversation_id}")
    
    # Get event loop for running sync DB operations
    loop = asyncio.get_event_loop()
    
    # Save user message to database (run in executor)
    print(f"💾 Saving user message to database...")
    await loop.run_in_executor(None, Message.create, conversation_id, 'user', msg.rstrip())
    print(f"✓ User message saved")
    
    # Get message count (run in executor)
    msg_count = await loop.run_in_executor(None, Message.count_by_conversation, conversation_id)
    user_msg_idx = msg_count - 1
    
    swap = 'beforeend'
    
    print(f"👤 Sending user message bubble (idx={user_msg_idx})")
    await send(Div(
        ChatMessage(user_msg_idx, 'user', msg.rstrip()),
        hx_swap_oob=swap, 
        id="chatlist"
    ))
    
    print(f"🧹 Sending clear input")
    await send(ChatInput())
    
    # Get conversation history from database (run in executor)
    print(f"📚 Loading conversation history from database...")
    history = await loop.run_in_executor(None, Message.get_history, conversation_id)
    print(f"✓ Loaded {len(history)} messages")
    
    print(f"🤖 Calling Anthropic API...")
    async with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=history,
        system=sp
    ) as stream:
        print(f"✓ Stream opened")
        
        assistant_msg_idx = msg_count  # Next index
        
        # Send empty assistant message
        print(f"📤 Sending empty assistant bubble (idx={assistant_msg_idx})")
        await send(Div(
            ChatMessage(assistant_msg_idx, 'assistant', ''),
            hx_swap_oob=swap, 
            id="chatlist"
        ))
        
        # Stream chunks
        chunk_count = 0
        full_response = ""
        async for text in stream.text_stream:
            chunk_count += 1
            full_response += text
            await send(Span(text, id=f"chat-content-{assistant_msg_idx}", hx_swap_oob=swap))
            
            if chunk_count <= 3:
                print(f"📤 Chunk {chunk_count}: {text[:20]}")
        
        print(f"✅ Stream complete: {chunk_count} chunks, {len(full_response)} chars")
        
        # Save assistant response to database (run in executor)
        print(f"💾 Saving assistant response to database...")
        await loop.run_in_executor(None, Message.create, conversation_id, 'assistant', full_response)
        print(f"✓ Assistant response saved")

if __name__ == '__main__':
    import uvicorn
    print("🚀 Starting test WebSocket + Auth + Database app...")
    print("📍 Visit: http://localhost:5003")
    print("🔐 Default login: username='admin', password='admin123'")
    print("💾 Using real database from models.py")
    uvicorn.run("test_ws_db:app", host='0.0.0.0', port=5003, reload=True)
