"""
Chat Interface Routes

Main chat UI and conversation management routes.
"""

from fasthtml.common import *
from models import Conversation, Message, validate_conversation_access
from templates.chat import chat_page, conversation_list_item
import config

# ============================================
# Routes
# ============================================

def get_routes():
    """Return list of route registration functions"""
    return [
        register_home_route,
        register_chat_route,
        register_conversation_routes
    ]

# ============================================
# Home/Landing
# ============================================

def register_home_route(app):
    @app.get("/")
    def home(session):
        """Landing page - redirect to chat if logged in"""
        if session.get('user'):
            return RedirectResponse("/chat", status_code=302)
        
        return Html(
            Head(
                Title("MCP Chat - WooCommerce Product Search"),
                Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            ),
            Body(
                Main(
                    H1("WooCommerce Product Search Chat"),
                    P("Intelligent product search powered by Claude and MCP."),
                    Div(
                        A("Login", href="/login", role="button"),
                        A("Register", href="/register", role="button", cls="secondary"),
                        style="display: flex; gap: 1rem;"
                    ),
                    cls="container"
                )
            )
        )

# ============================================
# Main Chat Interface
# ============================================

def register_chat_route(app):
    @app.get("/chat")
    @app.require_auth
    def chat_interface(session):
        """Main chat interface"""
        user = session.get('user')
        
        # Get user's conversations
        conversations = Conversation.get_by_user(user['id'])
        
        # Get or create current conversation
        current_conv_id = session.get('current_conversation_id')
        if not current_conv_id or not any(c.id == current_conv_id for c in conversations):
            # Create new conversation
            new_conv = Conversation.create(user['id'], "New Chat")
            current_conv_id = new_conv.id
            session['current_conversation_id'] = current_conv_id
        
        # Get messages for current conversation
        messages = Message.get_by_conversation(current_conv_id)
        
        return chat_page(user, conversations, current_conv_id, messages)

# ============================================
# Conversation Management
# ============================================

def register_conversation_routes(app):
    
    @app.get("/chat/{conversation_id}")
    @app.require_auth
    def load_conversation(session, conversation_id: int):
        """Load a specific conversation"""
        user = session.get('user')
        
        # Validate access
        try:
            validate_conversation_access(conversation_id, user['id'])
        except ValueError:
            return (
                Title("Access Denied"),
                Main(
                    H1("Access Denied"),
                    P("You don't have access to this conversation."),
                    A("Back to Chat", href="/chat"),
                    cls="container"
                )
            ), 403
        
        # Set as current conversation
        session['current_conversation_id'] = conversation_id
        
        # Redirect to main chat (which will load this conversation)
        return RedirectResponse("/chat", status_code=302)
    
    @app.post("/api/conversations/new")
    @app.require_auth
    def new_conversation(session):
        """Create a new conversation"""
        user = session.get('user')
        
        # Create new conversation
        new_conv = Conversation.create(user['id'], "New Chat")
        session['current_conversation_id'] = new_conv.id
        
        # Return empty messages area
        return Div(
            P("Start a new conversation by typing a message below.", 
              style="text-align: center; color: #666; padding: 2rem;"),
            id="messages"
        )
    
    @app.post("/api/conversations/{conversation_id}/rename")
    @app.require_auth
    def rename_conversation(session, conversation_id: int, title: str):
        """Rename a conversation"""
        user = session.get('user')
        
        try:
            validate_conversation_access(conversation_id, user['id'])
            
            # Load and update conversation
            conv = Conversation.get_by_id(conversation_id)
            if conv:
                conv.update_title(title)
                # Return updated conversation list item
                return conversation_list_item(conv, conversation_id == session.get('current_conversation_id'))
            else:
                return Div("Conversation not found", style="color: red;")
            
        except ValueError as e:
            return Div(str(e), style="color: red;")
    
    @app.delete("/api/conversations/{conversation_id}")
    @app.require_auth
    def delete_conversation(session, conversation_id: int):
        """Delete a conversation"""
        user = session.get('user')
        
        try:
            validate_conversation_access(conversation_id, user['id'])
            
            # Load and delete conversation
            conv = Conversation.get_by_id(conversation_id)
            if conv:
                conv.delete()
            
            # If this was the current conversation, create a new one
            if session.get('current_conversation_id') == conversation_id:
                new_conv = Conversation.create(user['id'], "New Chat")
                session['current_conversation_id'] = new_conv.id
            
            # Return success (HTMX will remove the element)
            return ""
            
        except ValueError as e:
            return Div(str(e), style="color: red;")
    
    @app.get("/api/conversations/list")
    @app.require_auth
    def list_conversations(session):
        """Get updated conversation list"""
        user = session.get('user')
        conversations = Conversation.get_by_user(user['id'])
        current_conv_id = session.get('current_conversation_id')
        
        return Div(
            *[conversation_list_item(conv, conv.id == current_conv_id) 
              for conv in conversations],
            id="conversation-list"
        )