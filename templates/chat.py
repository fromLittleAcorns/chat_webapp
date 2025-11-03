"""
Chat Interface Templates

FastHTML components for the chat interface.
"""

from fasthtml.common import *
from datetime import datetime
from templates.components import message_bubble

# ============================================
# Main Chat Page
# ============================================

def chat_page(user, conversations, current_conv_id, messages):
    """
    Complete chat interface with DaisyUI layout
    
    Args:
        user: User object from req.scope['user']
        conversations: List of conversation objects
        current_conv_id: Currently active conversation ID
        messages: List of messages in current conversation
    """
    
    return (
        Title("PBT Chat - Product Search"),
        # Main container - using DaisyUI drawer for sidebar
        Div(
            # Hidden checkbox required for drawer functionality
            Input(type="checkbox", id="my-drawer", cls="drawer-toggle", checked=True),
            
            # Main chat area (drawer content) - MUST come before drawer-side for proper layout
            chat_area(current_conv_id, messages),
            
            # Sidebar (drawer side)
            sidebar(user, conversations, current_conv_id),
            
            cls="drawer lg:drawer-open"
        ),
        
        # JavaScript for markdown rendering and auto-scroll
        chat_scripts()
    )

# ============================================
# Sidebar
# ============================================

def sidebar(user, conversations, current_conv_id):
    """Conversation list sidebar using DaisyUI menu"""
    
    return Div(
        Label(fr="my-drawer", cls="drawer-overlay"),
        Div(
            # Header with user info
            Div(
                H3("PBT Chat", cls="text-xl font-bold"),
                Div(
                    Div("👤", cls="text-2xl"),
                    Div(
                        Div(user.username, cls="font-semibold"),
                        Div(user.role.upper(), cls="text-xs opacity-70") if user.role == 'admin' else None,
                        cls="ml-2"
                    ),
                    cls="flex items-center mt-2"            
                ),
                # Admin link (only show for admins)
                 A("⚙️ Admin Panel" if user.role == 'admin' else "👤 My Profile", 
                  href="/auth/admin" if user.role == 'admin' else "/auth/profile",
                  cls="btn btn-secondary btn-sm mt-2 w-full"),
                A("Logout", 
                  href="/auth/logout", 
                  cls="btn btn-outline btn-sm mt-3 w-full"),
                cls="p-4 border-b"
            ),
            
            # New conversation button
            Button(
                "➕ New Chat",
                hx_post="/api/conversations/new",
                hx_target="#messages",
                hx_swap="innerHTML",
                cls="btn btn-primary m-4 w-[calc(100%-2rem)]"
            ),
            
            # Conversation list - NOT using menu class to avoid DaisyUI conflicts
            Div(
                *[conversation_list_item(conv, conv.id == current_conv_id) 
                  for conv in conversations],
                id="conversation-list",
                cls="flex flex-col gap-2 p-4"
            ),
            
            cls="h-full bg-base-200 w-80 overflow-y-auto border-r border-base-300"
        ),
        cls="drawer-side z-20"
    )

def conversation_list_item(conversation, is_active: bool = False):
    """Single conversation item in sidebar - custom styling instead of DaisyUI menu"""
    
    # Format timestamp
    try:
        updated = datetime.fromisoformat(conversation.updated_at)
        time_str = updated.strftime("%b %d, %H:%M")
    except:
        time_str = ""
    
    # Active styling
    bg_class = "bg-primary/20" if is_active else "bg-base-100"
    text_class = "text-primary font-semibold" if is_active else ""
    
    return Div(
        # Conversation link (takes most space)
        A(
            Div(
                Strong(conversation.title, cls=f"block text-sm {text_class}"),
                Small(time_str, cls="text-xs opacity-70"),
                cls="flex flex-col"
            ),
            href=f"/chat/{conversation.id}",
            cls="flex-1 min-w-0"  # min-w-0 allows text truncation to work
        ),
        
        # Delete button (fixed width, always visible on hover)
        Button(
            "🗑",
            hx_delete=f"/api/conversations/{conversation.id}",
            hx_target=f"#conv-{conversation.id}",
            hx_swap="outerHTML",
            hx_confirm="Delete this conversation?",
            cls="btn btn-ghost btn-xs btn-square shrink-0 opacity-0 group-hover:opacity-100 transition-opacity",
            title="Delete conversation"
        ),
        
        id=f"conv-{conversation.id}",
        cls=f"group flex items-center gap-2 p-3 rounded-lg hover:bg-base-300 {bg_class} transition-colors cursor-pointer"
    )

# ============================================
# Chat Area
# ============================================

def chat_area(current_conv_id, messages):
    """Main chat area with messages and input using DaisyUI"""
    
    return Div(
        # Messages container
        Div(
            # Render existing messages with indices and conv_id
            *[message_bubble(msg.role, msg.content, idx, current_conv_id) 
              for idx, msg in enumerate(messages)],
            
            # If no messages, show welcome
            Div(
                Div(
                    H2("👋 Welcome to PBT Chat", cls="text-3xl font-bold mb-4"),
                    P("Define requirements for PoweredByTrade products. I'll search the database and provide detailed, evidence-based answers.", 
                      cls="text-lg mb-2"),
                    P("Try asking about specific products, materials, finishes, or certifications.", 
                      cls="text-base-content/70"),
                    cls="hero-content text-center"
                ),
                cls="hero min-h-[60vh]"
            ) if len(messages) == 0 else None,
            
            id="messages",
            cls="flex flex-col gap-4 p-4 pb-32 max-w-4xl mx-auto w-full"
        ),
        
        # Input form
        input_form(current_conv_id),
        
        cls="drawer-content flex flex-col h-screen overflow-y-auto"
    )

def input_form(current_conv_id):
    """Message input form - submits directly to WebSocket (simple pattern!)"""
    
    return Div(
        Form(
            Div(
                Textarea(
                    name="msg",  # WebSocket expects 'msg'
                    id="message-input",
                    placeholder="Ask about products...",
                    rows="2",
                    required=True,
                    autocomplete="off",
                    cls="textarea textarea-bordered w-full resize-none"
                ),
                Button(
                    "Send",
                    type="submit",
                    id="send-btn",
                    cls="btn btn-primary"
                ),
                cls="flex gap-2 items-end"
            ),
            
            id="chat-form",
            ws_send=True,  # Send through WebSocket!
            hx_ext="ws",
            ws_connect="/wscon",  # Uses session for conv_id
            
            cls="w-full max-w-4xl"
        ),
        cls="fixed bottom-0 left-0 lg:left-80 right-0 bg-base-100 border-t p-4 z-10"
    )

# ============================================
# Scripts
# ============================================

def chat_scripts():
    """JavaScript for chat functionality"""
    
    return Script("""
        console.log('🚀 Chat scripts loaded');
        
        // DIAGNOSTIC: Check initial DOM structure
        console.log('📋 Initial messages HTML:', document.getElementById('messages')?.innerHTML.substring(0, 500));
        const messageBubbles = document.querySelectorAll('.chat');
        console.log('💬 Message bubbles found:', messageBubbles.length);
        messageBubbles.forEach((b, i) => console.log(`  Bubble ${i}:`, b.id, b.dataset.role, b.dataset.msgIdx));
        
        // Log ALL HTMX events for debugging
        document.body.addEventListener('htmx:afterSwap', function(evt) {
            console.log('🔄 HTMX afterSwap:', {
                target: evt.detail.target,
                target_id: evt.detail.target.id,
                swap: evt.detail.xhr?.getResponseHeader('HX-Reswap') || 'default'
            });
        });
        
        document.body.addEventListener('htmx:oobBeforeSwap', function(evt) {
            console.log('📦 HTMX oobBeforeSwap:', {
                target: evt.detail.target,
                target_id: evt.detail.target?.id,
                fragment: evt.detail.fragment
            });
        });
        
        document.body.addEventListener('htmx:oobAfterSwap', function(evt) {
            console.log('✅ HTMX oobAfterSwap:', {
                target: evt.detail.target,
                target_id: evt.detail.target?.id
            });
        });
        
        // WebSocket events logging
        document.body.addEventListener('htmx:wsOpen', function(evt) {
            console.log('🌊 WebSocket Connection Opened:', evt.detail);
        });
        
        document.body.addEventListener('htmx:wsClose', function(evt) {
            console.log('🏁 WebSocket Connection Closed:', evt.detail);
        });
        
        document.body.addEventListener('htmx:wsError', function(evt) {
            console.error('❌ WebSocket Error:', evt.detail);
        });
        
        // Server-side markdown rendering is now used
        
        // Auto-scroll to bottom when new messages arrive
        function scrollToBottom() {
            window.scrollTo({ 
                top: document.body.scrollHeight, 
                behavior: 'smooth' 
            });
        }
        
        // Scroll after swap
        document.body.addEventListener('htmx:afterSwap', function(evt) {
            if (evt.detail.target.id === 'messages') {
                setTimeout(scrollToBottom, 100);
            }
        });
        
        // Scroll during streaming (observe DOM changes)
        const observer = new MutationObserver(function(mutations) {
            scrollToBottom();
        });
        
        // Observe messages container for changes
        const messagesDiv = document.getElementById('messages');
        if (messagesDiv) {
            observer.observe(messagesDiv, { 
                childList: true, 
                subtree: true,
                characterData: true
            });
        }
        
        // Submit on Ctrl/Cmd + Enter
        document.getElementById('message-input').addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                this.form.dispatchEvent(new Event('submit', { bubbles: true }));
            }
        });
        
        // Focus input on load
        window.addEventListener('load', function() {
            document.getElementById('message-input').focus();
        });
        
        console.log('✅ All event listeners registered');
    """)
