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
    Complete chat interface
    
    Args:
        user: User dict from session
        conversations: List of conversation objects
        current_conv_id: Currently active conversation ID
        messages: List of messages in current conversation
    """
    
    return Html(
        Head(
            Title("MCP Chat - WooCommerce Search"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        ),
        Body(
            # Main container with sidebar and chat area
            Div(
                # Sidebar
                sidebar(user, conversations, current_conv_id),
                
                # Main chat area
                chat_area(current_conv_id, messages),
                
                cls="chat-container"
            ),
            
            # JavaScript for markdown rendering and auto-scroll
            chat_scripts()
        )
    )

# ============================================
# Sidebar
# ============================================

def sidebar(user, conversations, current_conv_id):
    """Conversation list sidebar"""
    
    return Aside(
        # Header with user info
        Div(
            H3("MCP Chat"),
            Small(f"👤 {user['username']}"),
            A("Logout", href="/logout", role="button", cls="outline secondary"),
            cls="sidebar-header"
        ),
        
        # New conversation button
        Button(
            "➕ New Chat",
            hx_post="/api/conversations/new",
            hx_target="#messages",
            hx_swap="innerHTML",
            cls="new-chat-btn"
        ),
        
        # Conversation list
        Div(
            *[conversation_list_item(conv, conv.id == current_conv_id) 
              for conv in conversations],
            id="conversation-list",
            cls="conversation-list"
        ),
        
        cls="sidebar"
    )

def conversation_list_item(conversation, is_active: bool = False):
    """Single conversation item in sidebar"""
    
    # Format timestamp
    try:
        updated = datetime.fromisoformat(conversation.updated_at)
        time_str = updated.strftime("%b %d, %H:%M")
    except:
        time_str = ""
    
    active_class = "active" if is_active else ""
    
    return Div(
        A(
            Div(
                Strong(conversation.title),
                Small(time_str, cls="timestamp"),
                cls="conv-info"
            ),
            href=f"/chat/{conversation.id}",
            cls=f"conversation-item {active_class}"
        ),
        
        # Delete button (only show on hover)
        Button(
            "🗑",
            hx_delete=f"/api/conversations/{conversation.id}",
            hx_target="closest div",
            hx_swap="outerHTML",
            hx_confirm="Delete this conversation?",
            cls="delete-btn",
            title="Delete conversation"
        ),
        
        id=f"conv-{conversation.id}",
        cls="conversation-wrapper"
    )

# ============================================
# Chat Area
# ============================================

def chat_area(current_conv_id, messages):
    """Main chat area with messages and input"""
    
    return Main(
        # Messages container
        Div(
            # Render existing messages
            *[message_bubble(msg.role, msg.content) for msg in messages],
            
            # If no messages, show welcome
            Div(
                H2("👋 Welcome to MCP Chat"),
                P("Ask questions about WooCommerce products. I'll search the database and provide detailed, evidence-based answers."),
                P("Try asking about specific products, materials, finishes, or certifications."),
                cls="welcome-message"
            ) if len(messages) == 0 else None,
            
            id="messages",
            cls="messages"
        ),
        
        # Spacer to prevent last message being hidden by input
        Div(style="height: 120px;"),
        
        # Input form
        input_form(),
        
        cls="chat-area"
    )

def input_form():
    """Message input form"""
    
    return Form(
        Div(
            Textarea(
                name="message",
                id="message-input",
                placeholder="Ask about products...",
                rows="2",
                required=True,
                autocomplete="off"
            ),
            Button(
                "Send",
                type="submit",
                id="send-btn"
            ),
            cls="input-container"
        ),
        
        hx_post="/api/chat/send",
        hx_target="#messages",
        hx_swap="beforeend",
        hx_indicator="#send-btn",
        
        cls="input-area"
    )

# ============================================
# Scripts
# ============================================

def chat_scripts():
    """JavaScript for chat functionality"""
    
    return Script("""
        // Clear input after sending
        document.body.addEventListener('htmx:afterRequest', function(evt) {
            if (evt.detail.successful && evt.detail.elt.id === 'message-input') {
                document.getElementById('message-input').value = '';
            }
        });
        
        // Render markdown after messages are added
        document.body.addEventListener('htmx:afterSwap', function(evt) {
            // Only render unrendered message content
            document.querySelectorAll('.message-content:not(.rendered)').forEach(function(el) {
                try {
                    el.innerHTML = marked.parse(el.textContent);
                    el.classList.add('rendered');
                    
                    // Syntax highlighting for code blocks
                    el.querySelectorAll('pre code').forEach(function(block) {
                        hljs.highlightElement(block);
                    });
                } catch (e) {
                    console.error('Markdown rendering error:', e);
                }
            });
        });
        
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
        
        // Scroll during streaming (SSE updates)
        const observer = new MutationObserver(function() {
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
    """)