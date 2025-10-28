"""
MCP Client Service - HTTP Transport

Handles communication with the MCP WooCommerce server via HTTP.
The MCP server must be running separately as an HTTP service.
"""

from anthropic import Anthropic, AsyncAnthropic
import os
import logging
import httpx
import json
import asyncio
import config

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
        
        # Initialize Anthropic client (simple setup)
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = Anthropic(api_key=api_key)
        self.async_client = AsyncAnthropic(api_key=api_key)
        
        # Verify MCP server is accessible
        self._verify_mcp_server()
        
        logger.info(f"MCP Client initialized: {mcp_server_url}")
        
        # Cache for MCP tools
        self._tools_cache = None
    
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
        Send message to Claude with MCP tools (HTTP-based, synchronous)
        
        NOTE: This method is currently UNUSED in the application.
        The active chat implementation uses get_message_stream() for WebSocket streaming.
        This method is retained for potential future HTTP-based endpoints or testing.
        
        Current usage:
        - ❌ NOT USED: The /api/chat/send route is deprecated
        - ✅ ACTIVE: get_message_stream() is used for WebSocket chat in ws_chat()
        
        Args:
            messages: List of message dicts [{"role": "user/assistant", "content": "..."}]
            stream: Whether to stream the response
            
        Returns:
            Streaming or non-streaming response from Claude (synchronous client)
        """
        
        # System instructions for Claude to use MCP tools effectively
        system_prompt = self._get_system_prompt()
        
        # Common parameters (will add local MCP tools later)
        params = {
            "model": "claude-sonnet-4-5-20250929",
            "max_tokens": 4096,
            "messages": messages,
            "system": system_prompt,
        }
        
        if stream:
            return self.client.messages.stream(**params)
        else:
            return self.client.messages.create(**params)
    
    async def get_message_stream_with_tools(self, messages: list):
        """
        Enhanced message streaming with local MCP tool calling
        
        This method:
        1. Gets available MCP tools
        2. Calls Claude with function calling enabled
        3. Handles tool calls by calling local MCP server
        4. Returns streaming response
        """
        system_prompt = self._get_system_prompt()
        
        # Get available MCP tools
        mcp_tools = await self.get_mcp_tools()
        
        # Convert MCP tools to Claude function calling format
        claude_tools = []
        for tool in mcp_tools:
            claude_tool = {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool.get("inputSchema", {})
            }
            claude_tools.append(claude_tool)
        
        logger.info(f"Using {len(claude_tools)} MCP tools with Claude")
        
        # Call Claude with tools enabled
        if claude_tools:
            return self.async_client.messages.stream(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096,
                messages=messages,
                system=system_prompt,
                tools=claude_tools,
            )
        else:
            # No tools available, use regular Claude
            return self.async_client.messages.stream(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096,
                messages=messages,
                system=system_prompt,
            )
    
    def get_message_stream(self, messages: list):
        """Get streaming message context manager with MCP tools"""
        system_prompt = self._get_system_prompt()
        
        # Get MCP tools for function calling
        mcp_tools = self.get_available_tools()
        
        if mcp_tools:
            logger.info(f"Using {len(mcp_tools)} MCP tools with Claude")
            return self.async_client.messages.stream(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096,
                messages=messages,
                system=system_prompt,
                tools=mcp_tools,
            )
        else:
            # No tools available, use regular Claude
            logger.warning("No MCP tools available, using regular Claude")
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
    # Local MCP Client Methods
    # ============================================
    
    def get_available_tools(self):
        """Get Claude function definitions for MCP tools (simplified approach)"""
        # Since the MCP server uses FastMCP with SSE, we'll define the tools manually
        # based on what we found in the MCP server code
        
        tools = [
            {
                "name": "llm_search_products",
                "description": "Direct FTS5 search with LLM-controlled terms. The LLM decides which terms to include based on query understanding.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "search_terms": {
                            "type": "string",
                            "description": "Space-separated search terms (LLM chooses what's important)"
                        },
                        "max_results": {
                            "type": "integer", 
                            "description": "Maximum results to return",
                            "default": 15
                        }
                    },
                    "required": ["search_terms"]
                }
            },
            {
                "name": "smart_search_products", 
                "description": "Intelligent multi-tier product search with automated term filtering",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "search_query": {
                            "type": "string",
                            "description": "Natural language search (e.g., 'gold door handles marine grade')"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum results to return", 
                            "default": 15
                        }
                    },
                    "required": ["search_query"]
                }
            },
            {
                "name": "get_product_by_sku",
                "description": "Get detailed product information by SKU (only published products)",
                "input_schema": {
                    "type": "object", 
                    "properties": {
                        "sku": {
                            "type": "string",
                            "description": "Product SKU to look up"
                        }
                    },
                    "required": ["sku"]
                }
            }
        ]
        
        logger.info(f"Providing {len(tools)} MCP tools to Claude")
        return tools
    
    async def call_mcp_tool(self, tool_name: str, arguments: dict):
        """Call a specific MCP tool via FastMCP SSE transport"""
        try:
            logger.info(f"Calling MCP tool {tool_name} with args: {arguments}")
            
            # For now, implement direct database calls to simulate MCP
            # This is a simplified approach until we get proper FastMCP client working
            
            if tool_name == "llm_search_products":
                # Import the MCP server directly for now
                import sys
                import importlib.util
                
                # Add path and import dynamically
                mcp_path = str(config.MCP_SERVER_PATH)
                if mcp_path not in sys.path:
                    sys.path.append(mcp_path)
                
                try:
                    from prod_find import WooCommerceMCPServer
                except ImportError as e:
                    logger.error(f"Failed to import WooCommerceMCPServer: {e}")
                    return f"Error: Could not import MCP server. Check MCP_SERVER_PATH: {config.MCP_SERVER_PATH}"
                
                # Create temporary server instance with correct database path
                db_path = "/Users/johnri/Library/Mobile Documents/com~apple~CloudDocs/Documents/james/james_data/database/db_for_prod_search.db"
                server = WooCommerceMCPServer(db_path)
                
                # Call the tool method directly
                search_terms = arguments.get("search_terms", "")
                max_results = arguments.get("max_results", 15)
                
                # Find the tool method in the server
                conn = server._get_connection()
                cursor = conn.cursor()
                
                # Minimal processing - only stopwords (copied from MCP server)
                stopwords = {'the', 'and', 'for', 'with', 'to', 'of', 'in', 'on', 'a', 'an', 'my', 'some', 'that', 'this'}
                terms = [term.lower().strip() for term in search_terms.split() 
                        if len(term) > 1 and term.lower() not in stopwords]
                
                if not terms:
                    return "Please provide search terms."
                
                # Use the server's search method
                results = server._search_with_fts5(cursor, terms, max_results)
                conn.close()
                
                if not results:
                    return f"No products found for '{search_terms}'."
                
                # Format results (copied from MCP server)
                response = f"Found {len(results)} products for '{search_terms}':\n\n"
                
                for i, product in enumerate(results, 1):
                    response += f"{i}. **{product['product_name']}** (SKU: {product['sku'] or 'N/A'})\n"
                    response += f"   Price: £{product.get('price', 'N/A')}\n"
                    
                    if product.get('category'):
                        response += f"   Category: {product['category']}\n"
                    
                    # Show relevant attributes
                    if product.get('finish'):
                        response += f"   Finish: {product['finish']}\n"
                    if product.get('size'):
                        response += f"   Size: {product['size']}\n"
                    elif product.get('dimensions'):
                        response += f"   Dimensions: {product['dimensions']}\n"
                    
                    response += "\n"
                
                logger.info(f"MCP tool {tool_name} executed successfully")
                return response
                
            elif tool_name == "get_product_by_sku":
                # Import the MCP server directly
                import sys
                
                # Add path and import dynamically  
                mcp_path = str(config.MCP_SERVER_PATH)
                if mcp_path not in sys.path:
                    sys.path.append(mcp_path)
                
                try:
                    from prod_find import WooCommerceMCPServer
                except ImportError as e:
                    logger.error(f"Failed to import WooCommerceMCPServer: {e}")
                    return f"Error: Could not import MCP server. Check MCP_SERVER_PATH: {config.MCP_SERVER_PATH}"
                
                # Create temporary server instance with correct database path
                db_path = "/Users/johnri/Library/Mobile Documents/com~apple~CloudDocs/Documents/james/james_data/database/db_for_prod_search.db"
                server = WooCommerceMCPServer(db_path)
                
                # Get the SKU argument
                sku = arguments.get("sku", "")
                if not sku:
                    return "Please provide a SKU to look up."
                
                # Call the database directly
                conn = server._get_connection()
                cursor = conn.cursor()
                
                # Query for the product by SKU (from published products only)
                cursor.execute("""
                    SELECT pa.*, pm_price.meta_value as price
                    FROM product_attributes pa
                    LEFT JOIN wp_postmeta pm_price ON pa.product_id = pm_price.post_id 
                        AND pm_price.meta_key = '_price'
                    LEFT JOIN wp_posts p ON pa.product_id = p.ID
                    WHERE pa.sku = ? AND p.post_status = 'publish'
                    LIMIT 1
                """, (sku,))
                
                result = cursor.fetchone()
                conn.close()
                
                if not result:
                    return f"No published product found with SKU: {sku}"
                
                # Convert to dict and format response
                product = dict(result)
                
                response = f"**{product['product_name']}** (SKU: {product['sku']})\n\n"
                response += f"**Price:** £{product.get('price', 'N/A')}\n"
                
                if product.get('category'):
                    response += f"**Category:** {product['category']}\n"
                
                # Show all available attributes
                for key, value in product.items():
                    if key not in ['product_id', 'sku', 'product_name', 'category', 'price'] and value:
                        formatted_key = key.replace('_', ' ').title()
                        response += f"**{formatted_key}:** {value}\n"
                
                logger.info(f"MCP tool {tool_name} executed successfully")
                return response
                
            elif tool_name == "smart_search_products":
                # Implement smart_search_products tool
                import sys
                
                # Add path and import dynamically
                mcp_path = str(config.MCP_SERVER_PATH)
                if mcp_path not in sys.path:
                    sys.path.append(mcp_path)
                
                try:
                    from prod_find import WooCommerceMCPServer
                except ImportError as e:
                    logger.error(f"Failed to import WooCommerceMCPServer: {e}")
                    return f"Error: Could not import MCP server. Check MCP_SERVER_PATH: {config.MCP_SERVER_PATH}"
                
                # Create temporary server instance with correct database path
                db_path = "/Users/johnri/Library/Mobile Documents/com~apple~CloudDocs/Documents/james/james_data/database/db_for_prod_search.db"
                server = WooCommerceMCPServer(db_path)
                
                # Get arguments
                search_query = arguments.get("search_query", "")
                max_results = arguments.get("max_results", 15)
                
                if not search_query:
                    return "Please provide a search query."
                
                # Use the server's query filter for smart searching
                filter_obj = server.__class__.__dict__.get('QueryTermFilter')
                if hasattr(server, 'filter'):
                    filtered_query, colors, dims = server.filter.filter_query(search_query)
                    terms = filtered_query.split() if filtered_query else search_query.split()
                else:
                    # Fallback - basic term splitting
                    terms = [term.lower().strip() for term in search_query.split() 
                            if len(term) > 1 and term.lower() not in {'the', 'and', 'for', 'with', 'to', 'of', 'in', 'on', 'a', 'an'}]
                
                # Call the search method
                conn = server._get_connection()
                cursor = conn.cursor()
                results = server._search_with_fts5(cursor, terms, max_results)
                conn.close()
                
                if not results:
                    return f"No products found for '{search_query}'."
                
                # Format results
                response = f"Found {len(results)} products for '{search_query}':\n\n"
                
                for i, product in enumerate(results, 1):
                    response += f"{i}. **{product['product_name']}** (SKU: {product['sku'] or 'N/A'})\n"
                    response += f"   Price: £{product.get('price', 'N/A')}\n"
                    
                    if product.get('category'):
                        response += f"   Category: {product['category']}\n"
                    
                    if product.get('finish'):
                        response += f"   Finish: {product['finish']}\n"
                    if product.get('size'):
                        response += f"   Size: {product['size']}\n"
                    elif product.get('dimensions'):
                        response += f"   Dimensions: {product['dimensions']}\n"
                    
                    response += "\n"
                
                logger.info(f"MCP tool {tool_name} executed successfully")
                return response
                
            else:
                return f"Tool {tool_name} not implemented yet"
                
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}", exc_info=True)
            return {"error": str(e)}

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