"""
MCP Client Service - HTTP Transport

Handles communication with the MCP WooCommerce server via HTTP.
The MCP server must be running separately as an HTTP service.
"""

from anthropic import Anthropic, AsyncAnthropic
import os
import logging
import httpx

logger = logging.getLogger(__name__)

# ============================================
# MCP Client Class
# ============================================

class MCPClient:
    """
    Client for communicating with MCP server via Anthropic SDK
    
    The MCP server runs as a separate HTTP service that Anthropic's API connects to.
    """
    
    def __init__(self, mcp_server_url: str):
        """
        Initialize MCP client
        
        Args:
            mcp_server_url: URL of MCP server (e.g., "http://localhost:8000")
        """
        self.mcp_server_url = mcp_server_url.rstrip('/')
        
        # Initialize Anthropic client with beta header for MCP support
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        # Add beta header for MCP features
        self.client = Anthropic(
            api_key=api_key,
            default_headers={
                "anthropic-beta": "mcp-client-2025-04-04"  # Beta header for MCP support
            }
        )
        
        # Also create async client for WebSocket streaming
        self.async_client = AsyncAnthropic(
            api_key=api_key,
            default_headers={
                "anthropic-beta": "mcp-client-2025-04-04"
            }
        )
        
        # Verify MCP server is accessible
        self._verify_mcp_server()
        
        logger.info(f"MCP Client initialized: {mcp_server_url}")
    
    def _verify_mcp_server(self):
        """Verify MCP server is running and accessible"""
        try:
            # Try to connect to SSE endpoint (404 on root is expected for MCP servers)
            response = httpx.get(f"{self.mcp_server_url}/sse", timeout=5.0)
            # SSE endpoint might return 200, 400, or hang - any response means server is up
            logger.info(f"MCP server accessible at {self.mcp_server_url}")
        except httpx.ConnectError as e:
            # Connection refused - server not running
            logger.error(f"Cannot connect to MCP server at {self.mcp_server_url}: {e}")
            raise RuntimeError(
                f"MCP server not accessible at {self.mcp_server_url}. "
                f"Make sure it's running with: python mcp_server_http.py"
            )
        except (httpx.TimeoutException, httpx.ReadTimeout):
            # Timeout is actually OK for SSE endpoint (it's designed to keep connections open)
            logger.info(f"MCP server accessible at {self.mcp_server_url} (SSE endpoint responding)")
        except Exception as e:
            # Other errors - log but don't fail (server might still work)
            logger.warning(f"MCP server health check returned unexpected response: {e}")
            logger.info(f"Proceeding anyway - MCP server may still be functional")
    
    def send_message(self, messages: list, stream: bool = True):
        """
        Send message to Claude (without MCP tools for now)
        
        Args:
            messages: List of message dicts [{"role": "user/assistant", "content": "..."}]
            stream: Whether to stream the response
            
        Returns:
            Streaming or non-streaming response from Claude
        """
        
        # System instructions for Claude
        system_prompt = self._get_system_prompt()
        
        # Common parameters (no MCP tools for now - HTTP MCP not supported by Anthropic API)
        params = {
            "model": "claude-sonnet-4-5-20250929",
            "max_tokens": 4096,
            "messages": messages,
            "system": system_prompt,
            # TODO: Implement MCP tool calling differently
            # The Anthropic API doesn't support HTTP MCP servers directly
        }
        
        if stream:
            return self.client.messages.stream(**params)
        else:
            return self.client.messages.create(**params)
    
    def get_message_stream(self, messages: list):
        """Get streaming message context manager (not async - returns the stream directly)"""
        system_prompt = self._get_system_prompt()
        
        return self.async_client.messages.stream(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=messages,
            system=system_prompt,
        )
    
    def _get_system_prompt(self) -> str:
        """
        Get system prompt with instructions for using MCP tools
        
        This prompt is loaded from the system_instructions.md file
        which contains the evidence-based search methodology.
        """
        try:
            # Import MCP_SERVER_PATH from config
            from pathlib import Path
            from config import MCP_SERVER_PATH
            
            # Look for system instructions in the configured MCP server path
            possible_paths = [
                MCP_SERVER_PATH / "updated_system_instructions.md",
                MCP_SERVER_PATH / "system_instructions.md",
                Path("./system_instructions.md"),  # Fallback to local
            ]
            
            for path in possible_paths:
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        logger.info(f"Loaded system instructions from {path}")
                        return f.read()
            
            logger.warning(f"System instructions not found in {MCP_SERVER_PATH}, using default")
            return self._get_default_system_prompt()
                
        except Exception as e:
            logger.error(f"Error loading system instructions: {e}")
            return self._get_default_system_prompt()
    
    def _get_default_system_prompt(self) -> str:
        """Default system prompt if file not found"""
        return """You are a helpful assistant with access to a WooCommerce product database via MCP tools.

CRITICAL INSTRUCTIONS:

1. **Evidence-Based Claims**: Never make assumptions about product specifications.
   - ✓ CONFIRMED: Only use when data is in attributes or quoted from descriptions
   - ✗ NOT FOUND: State clearly when specifications aren't in database
   - ? REQUIRES VERIFICATION: Mark what needs supplier confirmation
   
2. **Search Strategy**: Use llm_search_products as your primary tool.
   - Extract core product type + critical specs (size, finish, material)
   - Start with 3-5 focused terms
   - Remove noise (stopwords, certifications, accessories)
   
3. **Verification Protocol**: For critical specs (certifications, standards, ratings):
   - Fetch product with get_product_by_sku
   - Check certification field
   - Search descriptions if empty: search_product_descriptions("[sku] [spec]")
   - Quote exact text if found
   - State "NOT FOUND" if absent
   - NEVER infer from similar products

4. **Response Structure**:
   - ✓ CONFIRMED: List verified specifications
   - ✗ NOT FOUND: List missing specifications
   - ? REQUIRES VERIFICATION: List what needs checking
   - Honest recommendation based on confirmed data

Your goal is to find the right products efficiently while maintaining absolute honesty about what's confirmed vs. what requires verification.
"""

# ============================================
# Global Instance
# ============================================

_mcp_client = None

def init_mcp_client(mcp_server_url: str):
    """
    Initialize global MCP client instance
    
    Args:
        mcp_server_url: URL of MCP HTTP server (e.g., "http://localhost:8000")
    """
    global _mcp_client
    _mcp_client = MCPClient(mcp_server_url)
    logger.info("MCP client initialized successfully")

def get_mcp_client() -> MCPClient:
    """Get global MCP client instance"""
    if _mcp_client is None:
        raise RuntimeError(
            "MCP client not initialized. Call init_mcp_client() first. "
            "Make sure MCP server is running."
        )
    return _mcp_client