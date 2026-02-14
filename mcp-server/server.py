#!/usr/bin/env python3
"""
Postmortem Intelligence Engine MCP Server

This MCP server provides tools for ingesting postmortems, storing failure patterns,
and querying similar incidents to help prevent repeat failures.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    GetPromptRequest,
    GetPromptResult,
    ListPromptsRequest,
    ListPromptsResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    Prompt,
    Resource,
    TextContent,
    Tool,
)

# Import our modules
from agents.ingestion_agent import EnhancedIngestionAgent
from memory.failure_memory import FailureMemory
from schemas.postmortem_schema import ExtractedPostmortem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostmortemMCPServer:
    """MCP Server for Postmortem Intelligence Engine"""
    
    def __init__(self):
        self.server = Server("postmortem-intelligence-engine")
        self.ingestion_agent = None
        self.failure_memory = None
        self.tools_registry = {}
        
        # Initialize components
        self._initialize_components()
        self._register_tools()
        self._setup_handlers()
    
    def _initialize_components(self):
        """Initialize ingestion and memory components"""
        try:
            self.ingestion_agent = EnhancedIngestionAgent()
            self.failure_memory = FailureMemory()
            logger.info("✅ Components initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            # Continue without components for testing
            self.ingestion_agent = None
            self.failure_memory = None
    
    def _register_tools(self):
        """Register all available tools"""
        self.tools_registry = {
            "ingest_postmortem": {
                "name": "ingest_postmortem",
                "description": "Extract structured failure data from raw postmortem text",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "raw_text": {
                            "type": "string",
                            "description": "Raw postmortem text to analyze"
                        },
                        "organization": {
                            "type": "string",
                            "description": "Organization name (optional)"
                        },
                        "source_url": {
                            "type": "string",
                            "description": "Source URL of postmortem (optional)"
                        }
                    },
                    "required": ["raw_text"]
                }
            },
            "store_failure_memory": {
                "name": "store_failure_memory",
                "description": "Store extracted postmortem data in memory system",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "postmortem_data": {
                            "type": "object",
                            "description": "Extracted postmortem data from ingestion tool"
                        }
                    },
                    "required": ["postmortem_data"]
                }
            },
            "query_similar_failures": {
                "name": "query_similar_failures",
                "description": "Find postmortems with similar failure patterns",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for similar failures"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            "search_failures": {
                "name": "search_failures",
                "description": "Search failures with structured filters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "organization": {
                            "type": "string",
                            "description": "Filter by organization"
                        },
                        "severity": {
                            "type": "string",
                            "description": "Filter by severity (low, medium, high, critical)"
                        },
                        "failure_type": {
                            "type": "string",
                            "description": "Filter by failure type"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 10)",
                            "default": 10
                        }
                    }
                }
            },
            "get_memory_stats": {
                "name": "get_memory_stats",
                "description": "Get statistics about stored postmortems",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    
    def _setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            tools = []
            for tool_info in self.tools_registry.values():
                tools.append(Tool(
                    name=tool_info["name"],
                    description=tool_info["description"],
                    inputSchema=tool_info["inputSchema"]
                ))
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                logger.info(f"🔧 Tool called: {name} with args: {list(arguments.keys())}")
                
                if name == "ingest_postmortem":
                    return await self._handle_ingest_postmortem(arguments)
                elif name == "store_failure_memory":
                    return await self._handle_store_failure_memory(arguments)
                elif name == "query_similar_failures":
                    return await self._handle_query_similar_failures(arguments)
                elif name == "search_failures":
                    return await self._handle_search_failures(arguments)
                elif name == "get_memory_stats":
                    return await self._handle_get_memory_stats(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                    
            except Exception as e:
                logger.error(f"❌ Tool execution failed: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error executing tool {name}: {str(e)}"
                )]
    
    async def _handle_ingest_postmortem(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle postmortem ingestion"""
        if not self.ingestion_agent:
            return [TextContent(
                type="text",
                text="❌ Ingestion agent not available"
            )]
        
        raw_text = arguments.get("raw_text")
        organization = arguments.get("organization")
        source_url = arguments.get("source_url")
        
        try:
            logger.info(f"🔍 Starting ingestion for organization: {organization}")
            
            # Call the real ingestion agent
            response = self.ingestion_agent.process_postmortem(
                raw_text=raw_text,
                organization=organization,
                source_url=source_url
            )
            
            if response.success:
                # Log extracted data for debugging
                logger.info(f"✅ Ingestion successful for: {response.extracted_data.title}")
                logger.info(f"   Severity: {response.extracted_data.severity}")
                logger.info(f"   Failure Type: {response.extracted_data.root_cause.failure_type}")
                logger.info(f"   Affected Services: {', '.join(response.extracted_data.impact.affected_services)}")
                logger.info(f"   Processing Time: {response.processing_time_seconds:.2f}s")
                
                # Return structured response
                result = {
                    "success": True,
                    "message": "Postmortem ingestion completed successfully",
                    "processing_time_seconds": response.processing_time_seconds,
                    "extracted_data": response.extracted_data.dict(),
                    "confidence_score": response.extracted_data.confidence_score
                }
                
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            else:
                logger.error(f"❌ Ingestion failed: {response.error_message}")
                
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": response.error_message,
                        "processing_time_seconds": response.processing_time_seconds
                    }, indent=2)
                )]
                
        except Exception as e:
            logger.error(f"❌ Ingestion exception: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Ingestion exception: {str(e)}"
                }, indent=2)
            )]
    
    async def _handle_store_failure_memory(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle storing failure memory"""
        if not self.failure_memory:
            return [TextContent(
                type="text",
                text="❌ Failure memory not available"
            )]
        
        postmortem_data = arguments.get("postmortem_data")
        
        try:
            logger.info(f"💾 Storing postmortem in memory: {postmortem_data.get('title', 'Unknown')}")
            
            # Convert dict back to ExtractedPostmortem object
            from schemas.postmortem_schema import ExtractedPostmortem
            extracted_postmortem = ExtractedPostmortem(**postmortem_data)
            
            # Store in memory system
            doc_id = self.failure_memory.store_failure_memory(extracted_postmortem)
            
            logger.info(f"✅ Stored successfully with ID: {doc_id}")
            
            result = {
                "success": True,
                "message": "Failure memory stored successfully",
                "document_id": doc_id,
                "title": postmortem_data.get('title', 'Unknown')
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"❌ Memory storage failed: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Memory storage failed: {str(e)}"
                }, indent=2)
            )]
    
    async def _handle_query_similar_failures(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle querying similar failures"""
        if not self.failure_memory:
            return [TextContent(
                type="text",
                text="❌ Failure memory not available"
            )]
        
        query = arguments.get("query", "")
        limit = arguments.get("limit", 5)
        
        # Placeholder logic
        result = {
            "query": query,
            "similar_failures": [
                {
                    "title": "Sample Similar Incident",
                    "similarity_score": 0.85,
                    "summary": "This is a placeholder similar incident"
                }
            ],
            "total_found": 1
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    async def _handle_search_failures(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle structured failure search"""
        if not self.failure_memory:
            return [TextContent(
                type="text",
                text="❌ Failure memory not available"
            )]
        
        organization = arguments.get("organization")
        severity = arguments.get("severity")
        failure_type = arguments.get("failure_type")
        limit = arguments.get("limit", 10)
        
        # Placeholder logic
        result = {
            "filters": {
                "organization": organization,
                "severity": severity,
                "failure_type": failure_type
            },
            "failures": [
                {
                    "title": "Sample Filtered Incident",
                    "organization": organization or "Unknown",
                    "severity": severity or "medium"
                }
            ],
            "total_found": 1
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    async def _handle_get_memory_stats(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle memory statistics request"""
        if not self.failure_memory:
            return [TextContent(
                type="text",
                text="❌ Failure memory not available"
            )]
        
        # Placeholder logic
        result = {
            "vector_store": {
                "total_documents": 0,
                "index_size": 0
            },
            "metadata_store": {
                "total_postmortems": 0
            },
            "total_stored": 0,
            "last_updated": "2026-02-13T23:57:00Z"
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

async def main():
    """Main entry point for MCP server"""
    logger.info("🚀 Starting Postmortem Intelligence Engine MCP Server...")
    
    try:
        mcp_server = PostmortemMCPServer()
        
        # Create a simple server instance for testing
        server = Server("postmortem-intelligence-engine")
        
        # Add list_tools handler
        @server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            tools = []
            for tool_info in mcp_server.tools_registry.values():
                tools.append(Tool(
                    name=tool_info["name"],
                    description=tool_info["description"],
                    inputSchema=tool_info["inputSchema"]
                ))
            return tools
        
        # Add call_tool handler
        @server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                logger.info(f"🔧 Tool called: {name} with args: {list(arguments.keys())}")
                
                if name == "ingest_postmortem":
                    return await mcp_server._handle_ingest_postmortem(arguments)
                elif name == "store_failure_memory":
                    return await mcp_server._handle_store_failure_memory(arguments)
                elif name == "query_similar_failures":
                    return await mcp_server._handle_query_similar_failures(arguments)
                elif name == "search_failures":
                    return await mcp_server._handle_search_failures(arguments)
                elif name == "get_memory_stats":
                    return await mcp_server._handle_get_memory_stats(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                    
            except Exception as e:
                logger.error(f"❌ Tool execution failed: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error executing tool {name}: {str(e)}"
                )]
        
        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="postmortem-intelligence-engine",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )
            
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
