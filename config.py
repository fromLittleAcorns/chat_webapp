"""
Configuration Management - HTTP MCP Version

Centralized configuration for the FastHTML MCP Chat application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================
# Paths
# ============================================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Database paths
USERS_DB_PATH = DATA_DIR / "users.db"
CONVERSATIONS_DB_PATH = DATA_DIR / "conversations.db"

# ============================================
# MCP Server Configuration (HTTP)
# ============================================

# MCP server runs as separate HTTP service
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")

# Optional: Path to MCP server directory (for loading system instructions)
MCP_SERVER_PATH = Path(os.getenv(
    "MCP_SERVER_PATH",
    "../pbt_prodfind"
)).resolve()

# ============================================
# Security
# ============================================

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-CHANGE-IN-PRODUCTION")

# Session configuration
SESSION_EXPIRY = int(os.getenv("SESSION_EXPIRY", "3600"))  # 1 hour default

# Password requirements
MIN_PASSWORD_LENGTH = 8
REQUIRE_PASSWORD_UPPERCASE = True
REQUIRE_PASSWORD_LOWERCASE = True
REQUIRE_PASSWORD_DIGIT = True

# ============================================
# Authentication Settings
# ============================================

ALLOW_REGISTRATION = os.getenv("ALLOW_REGISTRATION", "True").lower() == "true"

# Initial admin user (for setup_db.py only)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")

# ============================================
# Anthropic/MCP Settings
# ============================================

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    import warnings
    warnings.warn(
        "ANTHROPIC_API_KEY not set. Set it in .env file or environment variable."
    )

# Model configuration
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 4096
TEMPERATURE = 1.0

# ============================================
# Application Settings
# ============================================

# Development mode
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
RELOAD = DEBUG

# Message limits
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "10000"))
MAX_CONVERSATIONS_PER_USER = int(os.getenv("MAX_CONVERSATIONS_PER_USER", "100"))

# Streaming
STREAMING_ENABLED = os.getenv("STREAMING_ENABLED", "True").lower() == "true"

# ============================================
# Rate Limiting
# ============================================

ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "False").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))  # requests per minute
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

# ============================================
# Logging
# ============================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = BASE_DIR / "app.log"

# ============================================
# Validation
# ============================================

def validate_config():
    """Validate critical configuration settings"""
    
    errors = []
    
    # Check MCP server URL format
    if not MCP_SERVER_URL.startswith("http://") and not MCP_SERVER_URL.startswith("https://"):
        errors.append(f"MCP_SERVER_URL must start with http:// or https://: {MCP_SERVER_URL}")
    
    # Warn if MCP server is not localhost in production
    if not DEBUG and "localhost" not in MCP_SERVER_URL and "127.0.0.1" not in MCP_SERVER_URL:
        print(f"⚠️  WARNING: MCP server is not on localhost: {MCP_SERVER_URL}")
        print("   Make sure this is intentional and properly secured.")
    
    # Check API key
    if not ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY not set in environment")
    
    # Check secret key in production
    if not DEBUG and SECRET_KEY == "dev-secret-key-CHANGE-IN-PRODUCTION":
        errors.append("SECRET_KEY must be changed in production")
    
    if errors:
        error_msg = "\n".join(f"  - {err}" for err in errors)
        raise ValueError(f"Configuration errors:\n{error_msg}")
    
    return True

# ============================================
# Display Configuration (for debugging)
# ============================================

def print_config():
    """Print current configuration (for debugging)"""
    
    print("=" * 60)
    print("FastHTML MCP Chat Configuration")
    print("=" * 60)
    print(f"Base Directory: {BASE_DIR}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"MCP Server URL: {MCP_SERVER_URL}")
    print(f"MCP Server Path: {MCP_SERVER_PATH} (for system instructions)")
    print(f"Users DB: {USERS_DB_PATH}")
    print(f"Conversations DB: {CONVERSATIONS_DB_PATH}")
    print(f"Debug Mode: {DEBUG}")
    print(f"Host: {HOST}:{PORT}")
    print(f"API Key Set: {'Yes' if ANTHROPIC_API_KEY else 'No'}")
    print(f"Streaming: {'Enabled' if STREAMING_ENABLED else 'Disabled'}")
    print("=" * 60)
    print()
    print("⚠️  IMPORTANT: MCP Server must be running separately!")
    print(f"   Start it with: cd {MCP_SERVER_PATH} && python mcp_server_http.py")
    print("=" * 60)

# ============================================
# Initialize
# ============================================

if __name__ == "__main__":
    # Run validation
    try:
        validate_config()
        print("✓ Configuration is valid")
        print_config()
    except ValueError as e:
        print(f"✗ Configuration error: {e}")