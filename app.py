"""
FastHTML MCP Chat - Main Application

Entry point for the web application that provides a chat interface
to the MCP WooCommerce server via HTTP.
"""

from fasthtml.common import *
from monsterui.all import *
from fasthtml_auth import AuthManager
from starlette.responses import Response
import config
from models import init_database
from services.mcp_client import init_mcp_client

# ============================================
# Initialize Authentication
# ============================================

# Initialize auth system
auth = AuthManager(
    db_path=str(config.USERS_DB_PATH),
    config={
        'allow_registration': True,
        'public_paths': [],  # No public paths - all routes require auth except /auth/*
        'login_path': '/auth/login',
    }
)

# Initialize database
db = auth.initialize()

# Create beforeware for authentication
beforeware = auth.create_beforeware()

# ============================================
# Initialize Application
# ============================================

# Additional headers for chat functionality
# Note: FastHTML/Theme likely includes HTMX already, so we only add what's missing
chat_headers = [
    # No SSE extension - using WebSockets instead
    
    # Markdown and syntax highlighting
    Script(src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"),
    Script(src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js"),
    Link(rel="stylesheet", href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/styles/github-dark.min.css"),
    # Custom CSS
    Link(rel="stylesheet", href="/static/css/custom.css"),
]

# Create FastHTML app with authentication and WebSocket support
app = FastHTML(
    before=beforeware,
    secret_key=config.SECRET_KEY,
    hdrs=Theme.blue.headers() + chat_headers,
    exts='ws'  # Enable WebSocket support
)

# Register authentication routes
auth.register_routes(app, include_admin=True)

# Initialize databases
init_database()

# Initialize MCP client (connects to HTTP server)
try:
    init_mcp_client(mcp_server_url=config.MCP_SERVER_URL)
except RuntimeError as e:
    print("\n" + "=" * 60)
    print("⚠️  MCP SERVER NOT RUNNING")
    print("=" * 60)
    print(f"Error: {e}")
    print("\nThe MCP server must be running before starting the web app.")
    print(f"\nStart it with:")
    print(f"  cd {config.MCP_SERVER_PATH}")
    print(f"  python mcp_server_http.py")
    print("\nThen restart this web app.")
    print("=" * 60 + "\n")
    import sys
    sys.exit(1)

# ============================================
# Routes
# ============================================

# Import and register routes
from routes import chat, api

# Register route groups
for route_func in chat.get_routes():
    route_func(app, auth)

for route_func in api.get_routes():
    route_func(app, auth)

# ============================================
# Static Files
# ============================================

@app.get("/static/{filepath:path}")
def serve_static(filepath: str):
    """Serve static files"""
    return FileResponse(config.BASE_DIR / "static" / filepath)

@app.get("/favicon.ico")
def favicon():
    """Return 404 for favicon - prevents error logs"""
    return Response(status_code=404)

# ============================================
# Error Handlers
# ============================================

@app.exception_handler(404)
def not_found(request, exc):
    return Html(
        Head(Title("Page Not Found")),
        Body(
            Div(
                Div(
                    H1("404 - Page Not Found", cls="text-4xl font-bold text-error"),
                    P("The page you're looking for doesn't exist.", cls="text-lg mt-4"),
                    A("Go to Chat", href="/chat", cls="btn btn-primary mt-6"),
                    cls="text-center py-20"
                ),
                cls="container mx-auto px-4"
            )
        )
    )

@app.exception_handler(500)
def server_error(request, exc):
    import logging
    logging.error(f"Server error: {exc}")
    return Html(
        Head(Title("Server Error")),
        Body(
            Div(
                Div(
                    H1("500 - Server Error", cls="text-4xl font-bold text-error"),
                    P("Something went wrong. Please try again later.", cls="text-lg mt-4"),
                    A("Go to Chat", href="/chat", cls="btn btn-primary mt-6"),
                    cls="text-center py-20"
                ),
                cls="container mx-auto px-4"
            )
        )
    )

# ============================================
# Startup
# ============================================

@app.on_event("startup")
async def startup():
    """Run on application startup"""
    # Configure logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    print("=" * 60)
    print("FastHTML MCP Chat Starting...")
    print(f"MCP Server URL: {config.MCP_SERVER_URL}")
    print(f"Users DB: {config.USERS_DB_PATH}")
    print(f"Conversations DB: {config.CONVERSATIONS_DB_PATH}")
    print("Logging level: INFO")
    print("=" * 60)
    
    # Clean up orphaned messages from any previous crashes
    from models import Message, Conversation
    logger.info("Checking for orphaned messages...")
    
    # Get all unique conversation IDs from messages
    from models.database import db
    result = db.execute(
        "SELECT DISTINCT conversation_id FROM messages"
    ).fetchall()
    
    if result:
        message_conv_ids = set(row[0] for row in result)
        
        # Get all valid conversation IDs
        valid_convs = db.execute(
            "SELECT id FROM conversations"
        ).fetchall()
        valid_conv_ids = set(row[0] for row in valid_convs) if valid_convs else set()
        
        # Find orphaned conversation IDs (messages with no parent conversation)
        orphaned_conv_ids = message_conv_ids - valid_conv_ids
        
        if orphaned_conv_ids:
            logger.warning(f"Found orphaned messages for non-existent conversations: {orphaned_conv_ids}")
            for conv_id in orphaned_conv_ids:
                msg_count = Message.count_by_conversation(conv_id)
                logger.info(f"  Deleting {msg_count} orphaned messages for conversation {conv_id}")
                Message.delete_by_conversation(conv_id)
            logger.info(f"✅ Cleaned up orphaned messages from {len(orphaned_conv_ids)} conversations")
        else:
            logger.info("✅ No orphaned messages found")
    else:
        logger.info("✅ No messages in database")
    
    logger.info("Application startup complete")

# ============================================
# Main
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    # Development server
    if config.DEBUG:
        print("\n🚀 Starting FastHTML MCP Chat...")
        print("🔐 Default admin user: username='admin', password='admin123'")
        print(f"🌐 Visit: http://localhost:{config.PORT}")
        print("=" * 60)
        uvicorn.run(
            "app:app",
            host=config.HOST,
            port=config.PORT,
            reload=True,
            log_level="info"
        )
    else:
        # Production
        serve()
