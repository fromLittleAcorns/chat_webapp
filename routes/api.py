"""
Chat API Routes

API endpoints for sending messages and streaming responses.
"""

from fasthtml.common import *
from fasthtml.common import to_xml  # Import explicitly for debugging
from models import Conversation, Message, validate_conversation_access
from services.mcp_client import get_mcp_client
from templates.components import message_bubble, streaming_message_bubble
from templates.chat import conversation_list_item
from datetime import datetime
import asyncio

# ============================================
# Routes
# ============================================

def get_routes():
    """Return list of route registration functions"""
    return [
        register_send_route,
        register_stream_route
    ]

# ============================================
# Send Message
# ============================================

def register_send_route(app, auth):
    
    @app.post("/api/chat/send")
    async def send_message(req, session, message: str):
        """
        Handle sending a message and initiating streaming response
        NOTE: This route NO LONGER saves messages - that's done in WebSocket handler
        """
        import logging
        logger = logging.getLogger(__name__)
        
        user = req.scope['user']
        conv_id = session.get('current_conversation_id')
        
        logger.info(f"📨 SEND MESSAGE: user={user.username}, conv={conv_id}, msg_len={len(message)}")
        
        # Validate
        if not message or len(message.strip()) == 0:
            return Div("Please enter a message.", style="color: red;")
        
        if len(message) > 10000:
            return Div("Message too long (max 10,000 characters).", style="color: red;")
        
        try:
            validate_conversation_access(conv_id, user.id)
        except ValueError:
            return Div("Invalid conversation.", style="color: red;")
        
        # DO NOT save message here - WebSocket handler will do it
        # This route is deprecated and not used in current flow
        
        logger.warning(f"⚠️ /api/chat/send route called - this is deprecated!")
        
        # Return error indicating to use WebSocket
        return Div(
            "Please use the WebSocket connection for sending messages.",
            style="color: orange;"
        )

# ============================================
# WebSocket Stream Response
# ============================================

def register_stream_route(app, auth):
    
    @app.ws('/wscon')
    async def ws_chat(msg: str, send, session):
        """
        Handle user message and stream Claude's response (SIMPLE PATTERN)
        
        Uses session to get conv_id (more reliable than query params in this setup)
        
        Args:
            msg: User's message text from form
            send: FastHTML send function  
            session: Session dict
        """
        import logging
        import asyncio
        logger = logging.getLogger(__name__)
        
        # Get conv_id from session (set by chat route)
        conv_id = session.get('current_conversation_id')
        if not conv_id:
            logger.error("❌ No conversation ID in session!")
            await send(Div("Error: No conversation found", style="color: red;"))
            return
    
        logger.info(f"🌊 WS START: conv_id={conv_id} (from session), msg_len={len(msg)}")
        
        if not msg or len(msg.strip()) == 0:
            logger.warning("⚠️ Empty message received")
            return
        
        # Get event loop for running sync DB operations
        loop = asyncio.get_event_loop()
        
        # Save user message to database (run in executor to avoid blocking)
        logger.info(f"💾 Saving user message to database...")
        try:
            await loop.run_in_executor(None, Message.create, conv_id, 'user', msg.rstrip())
            logger.info(f"✓ User message saved")
        except Exception as e:
            logger.error(f"❌ Failed to save message to conversation {conv_id}: {e}")
            logger.error(f"❌ This usually means conversation {conv_id} doesn't exist")
            
            # Try to create a new conversation as fallback
            try:
                logger.info(f"🔧 Creating new conversation as fallback...")
                new_conv = await loop.run_in_executor(None, Conversation.create, 1, "New Chat")  # Assuming user_id=1
                session['current_conversation_id'] = new_conv.id
                logger.info(f"✓ Created fallback conversation {new_conv.id}")
                
                # Now try to save the message again
                await loop.run_in_executor(None, Message.create, new_conv.id, 'user', msg.rstrip())
                logger.info(f"✓ User message saved to fallback conversation")
                conv_id = new_conv.id  # Update conv_id for rest of function
            except Exception as e2:
                logger.error(f"❌ Fallback also failed: {e2}")
                await send(Div("Error saving message. Please refresh the page.", style="color: red;"))
                return
        
        # Get message count (run in executor)
        msg_count = await loop.run_in_executor(None, Message.count_by_conversation, conv_id)
        user_msg_idx = msg_count - 1  # Just saved
        assistant_msg_idx = msg_count  # Will be next
        
        # Additional debugging for index calculation
        all_messages = await loop.run_in_executor(None, Message.get_by_conversation, conv_id)
        logger.info(f"🔍 Message IDs in DB: {[m.id for m in all_messages]}")
        logger.info(f"🔍 Message count: {len(all_messages)}, DB count: {msg_count}")
        logger.info(f"🆔 Message indices calculated: user={user_msg_idx}, assistant={assistant_msg_idx}")
        
        # Auto-generate title for first message and update sidebar
        if msg_count == 1:
            title = msg[:50] + ("..." if len(msg) > 50 else "")
            conv = await loop.run_in_executor(None, Conversation.get_by_id, conv_id)
            if conv:
                await loop.run_in_executor(None, conv.update_title, title)
                logger.info(f"📝 Updated conversation title to: {title}")
                
                # Send OOB update for the conversation list item
                updated_conv_item = conversation_list_item(conv, True)  # True = is_active
                updated_conv_item.attrs['hx-swap-oob'] = 'true'
                await send(updated_conv_item)
                logger.info("✓ Sent OOB update for conversation title")
        
        # Send user message bubble (use OOB with target selector)
        logger.info(f"👤 Sending user message bubble (conv={conv_id}, idx={user_msg_idx})")
        user_bubble = message_bubble('user', msg.rstrip(), user_msg_idx, conv_id)
        logger.info(f"🔍 User bubble type: {type(user_bubble)}, tag: {getattr(user_bubble, 'tag', 'no tag')}")
        user_bubble.attrs['hx-swap-oob'] = 'beforeend:#messages'
        
        # Debug: check what HTML is being sent
        html_output = to_xml(user_bubble)
        logger.info(f"📤 HTML being sent (first 300 chars): {html_output[:300]}")
        await send(user_bubble)
        
        # Clear input
        logger.info(f"🧹 Sending clear input")
        await send(
            Textarea(
                name="msg",
                id="message-input",
                placeholder="Ask about products...",
                rows="2",
                required=True,
                autocomplete="off",
                cls="textarea textarea-bordered w-full resize-none",
                hx_swap_oob="true"
            )
        )
        
        # Get conversation history from database (run in executor)
        logger.info(f"📚 Loading conversation history from database...")
        history = await loop.run_in_executor(None, Message.get_history, conv_id)
        logger.info(f"✓ Loaded {len(history)} messages")
        
        try:
            # Get MCP client
            logger.info("📡 Getting MCP client...")
            mcp_client = get_mcp_client()
            logger.info("✓ MCP client obtained")
            
            # Send empty assistant bubble (with content ID for streaming)
            logger.info(f"🎨 Sending empty assistant bubble (conv={conv_id}, idx={assistant_msg_idx})")
            assistant_bubble = message_bubble('assistant', '', assistant_msg_idx, conv_id, for_streaming=True)
            logger.info(f"🔍 Assistant bubble type: {type(assistant_bubble)}, tag: {getattr(assistant_bubble, 'tag', 'no tag')}")
            assistant_bubble.attrs['hx-swap-oob'] = 'beforeend:#messages'
            
            # Debug: check what HTML is being sent
            html_output = to_xml(assistant_bubble)
            logger.info(f"📤 Assistant HTML being sent (first 300 chars): {html_output[:300]}")
            await send(assistant_bubble)
            logger.info("✓ Empty bubble sent")
            
            full_response = ""
            chunk_count = 0
            
            logger.info("🤖 Calling Claude API (async)...")
            
            # Handle iterative tool calling - Claude can make multiple rounds of tool calls
            max_tool_rounds = 10  # Generous limit for complex search strategies
            tool_round = 0
            
            while tool_round < max_tool_rounds:
                tool_round += 1
                logger.info(f"🔄 Tool calling round {tool_round}")
                
                async with mcp_client.get_message_stream(history) as stream:
                    # First check if there are tool calls by peeking at stream without consuming it
                    # We'll do this by getting the final message first, then start a new stream for final response if needed
                    
                    # Check if we need to handle tool calls
                    message = await stream.get_final_message()
                    
                    # Check for tool calls in the message content
                    tool_calls = []
                    for content_block in message.content:
                        if hasattr(content_block, 'type') and content_block.type == 'tool_use':
                            tool_calls.append(content_block)
                    
                    if tool_calls:
                        logger.info(f"🔧 Claude wants to use {len(tool_calls)} tool(s) in round {tool_round}")
                        
                        # Send user feedback about what's happening
                        if tool_round == 1:
                            feedback_msg = "🔍 Searching database..."
                        elif tool_round == 2:
                            feedback_msg = "🔄 Trying broader search terms..."
                        elif tool_round == 3:
                            feedback_msg = "📊 Analyzing product details..."
                        elif tool_round == 4:
                            feedback_msg = "🔎 Verifying specifications..."
                        else:
                            feedback_msg = f"🔧 Processing search (step {tool_round})..."
                        
                        # Send feedback message to the content div
                        await send(
                            Div(
                                feedback_msg,
                                id=f"feedback-{conv_id}-{assistant_msg_idx}",
                                style="color: #666; font-style: italic; opacity: 0.8; margin: 8px 0;",
                                hx_swap_oob=f"innerHTML:#content-{conv_id}-{assistant_msg_idx}"
                            )
                        )
                        
                        # Process tool calls with periodic feedback
                        tool_results = []
                        import time
                        start_time = time.time()
                        thinking_count = 0
                        
                        for tool_use in tool_calls:
                            tool_name = tool_use.name
                            tool_args = tool_use.input
                            tool_id = tool_use.id
                            
                            logger.info(f"🔧 Calling tool: {tool_name} with args: {tool_args}")
                            
                            # Show detailed progress during longer operations
                            if tool_name in ['llm_search_products', 'smart_search_products']:
                                progress_msg = feedback_msg + " (searching)"
                            elif tool_name == 'get_product_by_sku':
                                progress_msg = feedback_msg + " (fetching details)"
                            else:
                                progress_msg = feedback_msg + " (processing)"
                            
                            await send(
                                Div(
                                    progress_msg,
                                    style="color: #666; font-style: italic; opacity: 0.8; margin: 8px 0;",
                                    hx_swap_oob=f"innerHTML:#content-{conv_id}-{assistant_msg_idx}"
                                )
                            )
                            
                            # Call the MCP tool
                            result = await mcp_client.call_mcp_tool(tool_name, tool_args)
                            
                            # Add to history for next Claude call
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": str(result)
                            })
                        
                        # Add tool use message and results to history
                        history.append({
                            "role": "assistant", 
                            "content": message.content
                        })
                        
                        history.append({
                            "role": "user",
                            "content": tool_results
                        })
                        
                        # Continue loop to see if Claude wants to use more tools
                        continue
                    
                    else:
                        # No more tool calls - start fresh stream for final response
                        logger.info(f"✅ Claude finished with tool calling after {tool_round} rounds, starting fresh stream for final response")
                        
                        # Show thinking indicator while waiting for final response
                        await send(
                            Div(
                                "🤔 Preparing response...",
                                style="color: #666; font-style: italic; opacity: 0.8; margin: 8px 0;",
                                hx_swap_oob=f"innerHTML:#content-{conv_id}-{assistant_msg_idx}"
                            )
                        )
                        
                        # Create a background task to show periodic thinking updates
                        import asyncio
                        import time
                        
                        thinking_task = None
                        async def show_thinking_dots():
                            """Show animated thinking indicator every 3 seconds"""
                            await asyncio.sleep(3)  # Wait 3 seconds before first update
                            dots_count = 1
                            while True:
                                dots = "." * (dots_count % 4)  # Cycle through ., .., ..., then back to .
                                thinking_msg = f"🤔 Preparing response{dots}"
                                try:
                                    await send(
                                        Div(
                                            thinking_msg,
                                            style="color: #666; font-style: italic; opacity: 0.8; margin: 8px 0;",
                                            hx_swap_oob=f"innerHTML:#content-{conv_id}-{assistant_msg_idx}"
                                        )
                                    )
                                except:
                                    break  # Stop if sending fails (connection closed)
                                dots_count += 1
                                await asyncio.sleep(3)
                        
                        # Start thinking animation
                        thinking_task = asyncio.create_task(show_thinking_dots())
                        
                        try:
                            # Start a new stream for the final response to get proper streaming
                            async with mcp_client.get_message_stream(history) as final_stream:
                                # Cancel the thinking animation once we start streaming
                                if thinking_task:
                                    thinking_task.cancel()
                                
                                # Don't clear the content div - let the first chunk replace the thinking indicator
                                first_chunk = True
                            
                                async for text in final_stream.text_stream:
                                    chunk_count += 1
                                    full_response += text
                                    
                                    if first_chunk:
                                        # First chunk replaces the thinking indicator
                                        await send(
                                            Span(
                                                text,
                                                hx_swap_oob=f"innerHTML:#content-{conv_id}-{assistant_msg_idx}"
                                            )
                                        )
                                        first_chunk = False
                                    else:
                                        # Subsequent chunks append
                                        await send(
                                            Span(
                                                text,
                                                hx_swap_oob=f"beforeend:#content-{conv_id}-{assistant_msg_idx}"
                                            )
                                        )
                                    
                                    if chunk_count <= 3:
                                        logger.info(f"📤 Final chunk {chunk_count}: {repr(text[:30])}")
                                    elif chunk_count % 20 == 0:
                                        logger.info(f"📤 Final chunk {chunk_count} (every 20th logged)")
                        finally:
                            # Always cancel the thinking task when done
                            if thinking_task:
                                thinking_task.cancel()
                        
                        # Exit the tool calling loop
                        break
            
            if tool_round >= max_tool_rounds:
                logger.warning(f"⚠️ Hit maximum tool rounds ({max_tool_rounds}), stopping")
            
            logger.info(f"✅ Stream complete: {chunk_count} chunks, {len(full_response)} chars")
            
            # Render markdown on server using MonsterUI
            logger.info("🎨 Rendering markdown on server...")
            from monsterui.franken import render_md
            rendered_html = render_md(full_response)
            logger.info(f"✓ Markdown rendered: {len(rendered_html)} chars of HTML")
            
            # Send final rendered content to replace the streamed text
            await send(
                Div(
                    NotStr(rendered_html),  # Use NotStr to prevent escaping
                    id=f"content-{conv_id}-{assistant_msg_idx}",
                    cls="message-content",
                    hx_swap_oob="true"
                )
            )
            logger.info("✓ Final rendered content sent")
            
            # Save complete assistant response (run in executor to avoid blocking)
            logger.info(f"💾 Saving complete response to database...")
            await loop.run_in_executor(None, Message.create, conv_id, 'assistant', full_response)
            logger.info("✓ Response saved")
            
            logger.info("✅ WebSocket stream finished successfully")
            
        except Exception as e:
            logger.error(f"❌ STREAMING ERROR: {e}", exc_info=True)
            await send(Div(f"Error: {str(e)}", style="color: red;"))
