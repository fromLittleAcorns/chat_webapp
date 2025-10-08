"""
FastHTML MCP Chat - Main Application with MonsterUI

Entry point for the web application that provides a chat interface
to the MCP WooCommerce server via HTTP.
"""

from fasthtml.common import *
from fasthtml_auth import AuthenticatedApp
import config
from models import init_database
from services.mcp_client import init_mcp_client

# ============================================
# Initialize Application with MonsterUI
# ============================================

# MonsterUI headers (same as fasthtml-auth for consistency)
monsterui_headers = (
    # MonsterUI CSS
    Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@4.4.19/dist/full.min.css"),
    Script(src="https://cdn.tailwindcss.com"),
    # HTMX for interactivity
    Script(src="https://unpkg.com/htmx.org@1.9.10"),
    Script(src="https://unpkg.com/htmx.org@1.9.10/dist/ext/sse.js"),  # SSE extension
    # Markdown and syntax highlighting
    Script(src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"),
    Script(src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js"),
    Link(rel="stylesheet", href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/styles/github-dark.min.css"),
    # Custom chat CSS (minimal)
    Link(rel="stylesheet", href="/static/css/chat.css"),
    # DaisyUI theme configuration
    Script("""
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {}
            }
        }
    """)
)

# Create FastHTML app with authentication
app = AuthenticatedApp(
    db_path=str(config.USERS_DB_PATH),
    secret_key=config.SECRET_KEY,
    session_expiry=config.SESSION_EXPIRY,
    hdrs=monsterui_headers
)

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
    route_func(app)

for route_func in api.get_routes():
    route_func(app)

# ============================================
# Static Files
# ============================================

@app.get("/static/{filepath:path}")
def serve_static(filepath: str):
    """Serve static files"""
    return FileResponse(config.BASE_DIR / "static" / filepath)

# ============================================
# Error Handlers
# ============================================

@app.exception_handler(404)
def not_found(request, exc):
    return (
        Title("Page Not Found"),
        Div(
            Div(
                H1("404 - Page Not Found", cls="text-4xl font-bold text-error"),
                P("The page you're looking for doesn't exist.", cls="text-lg mt-4"),
                A("Go to Chat", href="/chat", cls="btn btn-primary mt-6"),
                cls="text-center py-20"
            ),
            cls="container mx-auto px-4"
        )
    ), 404

@app.exception_handler(500)
def server_error(request, exc):
    import logging
    logging.error(f"Server error: {exc}")
    return (
        Title("Server Error"),
        Div(
            Div(
                H1("500 - Server Error", cls="text-4xl font-bold text-error"),
                P("Something went wrong. Please try again later.", cls="text-lg mt-4"),
                A("Go to Chat", href="/chat", cls="btn btn-primary mt-6"),
                cls="text-center py-20"
            ),
            cls="container mx-auto px-4"
        )
    ), 500

# ============================================
# Startup
# ============================================

@app.on_event("startup")
async def startup():
    """Run on application startup"""
    print("=" * 60)
    print("FastHTML MCP Chat Starting...")
    print(f"MCP Server URL: {config.MCP_SERVER_URL}")
    print(f"Conversations DB: {config.CONVERSATIONS_DB_PATH}")
    print("=" * 60)

# ============================================
# Main
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    # Development server
    if config.DEBUG:
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=5000,
            reload=True,
            log_level="info"
        )
    else:
        # Production
        serve()