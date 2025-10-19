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

def register_home_route(app, auth):
    @app.get("/")
    def home(req):
        """Landing page - redirect to chat (unauthenticated users redirected to login by beforeware)"""
        return RedirectResponse("/chat", status_code=302)

# ============================================
# Main Chat Interface
# ============================================

def register_chat_route(app, auth):
    @app.get("/chat")
    def chat_interface(req, session):
        """Main chat interface - automatically protected by auth beforeware"""
        user = req.scope['user']
        
        # Get user's conversations
        conversations = Conversation.get_by_user(user.id)
        
        # Get or create current conversation
        current_conv_id = session.get('current_conversation_id')
        if not current_conv_id or not any(c.id == current_conv_id for c in conversations):
            # Create new conversation
            new_conv = Conversation.create(user.id, "New Chat")
            current_conv_id = new_conv.id
            session['current_conversation_id'] = current_conv_id
        
        # Get messages for current conversation
        messages = Message.get_by_conversation(current_conv_id)
        
        return chat_page(user, conversations, current_conv_id, messages)

# ============================================
# Conversation Management
# ============================================

def register_conversation_routes(app, auth):
    
    @app.get("/chat/{conversation_id}")
    def load_conversation(req, session, conversation_id: int):
        """Load a specific conversation"""
        user = req.scope['user']
        
        # Validate access
        try:
            validate_conversation_access(conversation_id, user.id)
        except ValueError:
            return (
                Title("Access Denied"),
                Div(
                    Div(
                        H1("Access Denied", cls="text-4xl font-bold text-error"),
                        P("You don't have access to this conversation.", cls="text-lg mt-4"),
                        A("Back to Chat", href="/chat", cls="btn btn-primary mt-6"),
                        cls="text-center py-20"
                    ),
                    cls="container mx-auto"
                )
            )
        
        # Set as current conversation
        session['current_conversation_id'] = conversation_id
        
        # Get user's conversations
        conversations = Conversation.get_by_user(user.id)
        
        # Get messages for selected conversation
        messages = Message.get_by_conversation(conversation_id)
        
        # Render chat page with selected conversation
        return chat_page(user, conversations, conversation_id, messages)
    
    @app.post("/api/conversations/new")
    def new_conversation(req, session):
        """Create a new conversation"""
        import logging
        logger = logging.getLogger(__name__)
        
        user = req.scope['user']
        
        # Create new conversation
        new_conv = Conversation.create(user.id, "New Chat")
        old_conv_id = session.get('current_conversation_id')
        session['current_conversation_id'] = new_conv.id
        logger.info(f"🆕 Created new conversation {new_conv.id} (replacing {old_conv_id})")
        
        # CRITICAL: Force cleanup of any orphaned messages (SQLite ID reuse issue)
        orphan_count = Message.count_by_conversation(new_conv.id)
        if orphan_count > 0:
            logger.error(f"❌❌❌ ORPHANED MESSAGES DETECTED! Conv {new_conv.id} has {orphan_count} messages. Cleaning up...")
            Message.delete_by_conversation(new_conv.id)
            # Verify cleanup
            verify_count = Message.count_by_conversation(new_conv.id)
            if verify_count == 0:
                logger.info(f"✅ Orphaned messages cleaned up")
            else:
                logger.error(f"❌❌❌ CLEANUP FAILED! Still have {verify_count} messages!")
        
        # Return welcome message using DaisyUI hero
        return Div(
            Div(
                H2("👋 Welcome to MCP Chat", cls="text-3xl font-bold mb-4"),
                P("Ask questions about WooCommerce products. I'll search the database and provide detailed, evidence-based answers.", 
                  cls="text-lg mb-2"),
                P("Try asking about specific products, materials, finishes, or certifications.", 
                  cls="text-base-content/70"),
                cls="hero-content text-center"
            ),
            cls="hero min-h-[60vh]"
        )
    
    @app.post("/api/conversations/{conversation_id}/rename")
    def rename_conversation(req, session, conversation_id: int, title: str):
        """Rename a conversation"""
        user = req.scope['user']
        
        try:
            validate_conversation_access(conversation_id, user.id)
            
            # Load and update conversation
            conv = Conversation.get_by_id(conversation_id)
            if conv:
                conv.update_title(title)
                # Return updated conversation list item
                return conversation_list_item(conv, conversation_id == session.get('current_conversation_id'))
            else:
                return Div(
                    "Conversation not found",
                    cls="alert alert-error"
                )
            
        except ValueError as e:
            return Div(
                str(e),
                cls="alert alert-error"
            )
    
    @app.delete("/api/conversations/{conversation_id}")
    def delete_conversation(req, session, conversation_id: int):
        """Delete a conversation"""
        import logging
        logger = logging.getLogger(__name__)
        
        user = req.scope['user']
        
        try:
            validate_conversation_access(conversation_id, user.id)
            
            # DIAGNOSTIC: Check messages before delete
            msg_count_before = Message.count_by_conversation(conversation_id)
            logger.info(f"🗑️ Deleting conversation {conversation_id} with {msg_count_before} messages")
            
            # Load and delete conversation
            conv = Conversation.get_by_id(conversation_id)
            if conv:
                conv.delete()
                logger.info(f"✅ Conversation {conversation_id} deleted")
                
                # DIAGNOSTIC: Verify messages were deleted
                msg_count_after = Message.count_by_conversation(conversation_id)
                if msg_count_after > 0:
                    logger.error(f"❌ Messages NOT deleted! Conv {conversation_id} still has {msg_count_after} messages!")
                else:
                    logger.info(f"✅ All messages deleted for conversation {conversation_id}")
            
            # If this was the current conversation, create a new one
            if session.get('current_conversation_id') == conversation_id:
                new_conv = Conversation.create(user.id, "New Chat")
                session['current_conversation_id'] = new_conv.id
                logger.info(f"🆕 Created new conversation {new_conv.id} to replace deleted one")
            
            # Return: remove list item + clear messages with OOB
            return (
                "",  # Remove the conversation list item
                # Clear messages area with welcome message
                Div(
                    Div(
                        H2("👋 Welcome to MCP Chat", cls="text-3xl font-bold mb-4"),
                        P("Ask questions about WooCommerce products. I'll search the database and provide detailed, evidence-based answers.", 
                          cls="text-lg mb-2"),
                        P("Try asking about specific products, materials, finishes, or certifications.", 
                          cls="text-base-content/70"),
                        cls="hero-content text-center"
                    ),
                    cls="hero min-h-[60vh]",
                    hx_swap_oob="innerHTML:#messages"
                )
            )
            
        except ValueError as e:
            return Div(
                str(e),
                cls="alert alert-error"
            )
    
    @app.get("/api/conversations/list")
    def list_conversations(req, session):
        """Get updated conversation list"""
        user = req.scope['user']
        conversations = Conversation.get_by_user(user.id)
        current_conv_id = session.get('current_conversation_id')
        
        return Ul(
            *[conversation_list_item(conv, conv.id == current_conv_id) 
              for conv in conversations],
            id="conversation-list",
            cls="menu p-4 gap-2"
        )
