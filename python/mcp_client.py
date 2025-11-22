"""
MCP (Model Context Protocol) client for calling MCP tools.
Handles JSON-RPC style communication with MCP servers over HTTP.
"""

import json
import requests
import os
from typing import Dict, Any, Optional, List
from config import get_mcp_server_url, get_mcp_auth_token, MCP_TIMEOUT


class MCPError(Exception):
    """Custom exception for MCP-related errors."""
    pass


def list_mcp_tools(service_name: str) -> List[Dict[str, Any]]:
    """
    List available tools from an MCP server for a given service.
    
    Args:
        service_name: Name of the service (e.g., "Gmail", "Slack")
        
    Returns:
        List of available tools with their schemas
        
    Raises:
        MCPError: If the MCP server request fails
    """
    mcp_url = get_mcp_server_url(service_name)
    if not mcp_url:
        raise MCPError(f"No MCP server URL configured for service: {service_name}")
    
    # MCP JSON-RPC request to list tools
    mcp_request = {
        'jsonrpc': '2.0',
        'method': 'tools/list',
        'params': {},
        'id': 1
    }
    
    try:
        headers = _get_mcp_headers(service_name)
        response = requests.post(
            mcp_url,
            json=mcp_request,
            headers=headers,
            timeout=MCP_TIMEOUT
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Handle JSON-RPC response
        if 'error' in result:
            raise MCPError(f"MCP server error: {result['error']}")
        
        if 'result' in result and 'tools' in result['result']:
            return result['result']['tools']
        else:
            raise MCPError(f"Unexpected MCP response format: {result}")
            
    except requests.exceptions.RequestException as e:
        raise MCPError(f"Failed to connect to MCP server at {mcp_url}: {str(e)}")
    except json.JSONDecodeError as e:
        raise MCPError(f"Invalid JSON response from MCP server: {str(e)}")


def call_mcp_tool(tool_id: str, parameters: Dict[str, Any], service_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Call an MCP tool with the given parameters.
    
    Args:
        tool_id: The ID of the MCP tool to call (e.g., "send_email", "search_attachments")
        parameters: Dictionary of parameters for the tool
        service_name: Optional service name to determine which MCP server to use.
                     If not provided, will try to infer from tool_id.
        
    Returns:
        Dictionary containing the result of the MCP tool call
        
    Raises:
        MCPError: If the MCP tool call fails
        ValueError: If required parameters are missing
    """
    # Infer service name from tool_id if not provided
    if not service_name:
        service_name = _infer_service_from_tool_id(tool_id)
    
    mcp_url = get_mcp_server_url(service_name)
    if not mcp_url:
        raise MCPError(f"No MCP server URL configured for service: {service_name}")
    
    # Format as JSON-RPC style MCP call
    mcp_request = {
        'jsonrpc': '2.0',
        'method': 'tools/call',
        'params': {
            'name': tool_id,
            'arguments': parameters
        },
        'id': 1
    }
    
    try:
        headers = _get_mcp_headers(service_name)
        response = requests.post(
            mcp_url,
            json=mcp_request,
            headers=headers,
            timeout=MCP_TIMEOUT
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Handle JSON-RPC error response
        if 'error' in result:
            error_msg = result['error'].get('message', 'Unknown error')
            error_code = result['error'].get('code', -1)
            raise MCPError(f"MCP tool call failed (code {error_code}): {error_msg}")
        
        # Return the result
        if 'result' in result:
            return result
        else:
            raise MCPError(f"Unexpected MCP response format: {result}")
            
    except requests.exceptions.Timeout:
        raise MCPError(f"Timeout waiting for MCP server response (>{MCP_TIMEOUT}s)")
    except requests.exceptions.ConnectionError:
        raise MCPError(f"Could not connect to MCP server at {mcp_url}. Is the server running?")
    except requests.exceptions.RequestException as e:
        raise MCPError(f"HTTP error calling MCP server: {str(e)}")
    except json.JSONDecodeError as e:
        raise MCPError(f"Invalid JSON response from MCP server: {str(e)}")


def _get_mcp_headers(service_name: str) -> Dict[str, str]:
    """Get HTTP headers for MCP server requests, including authentication if configured."""
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Add authentication token if available
    auth_token = get_mcp_auth_token(service_name)
    if auth_token:
        headers['Authorization'] = f'Bearer {auth_token}'
    
    return headers


def _infer_service_from_tool_id(tool_id: str) -> str:
    """
    Infer service name from tool ID.
    Examples: "gmail_send_email" -> "gmail", "slack_send_message" -> "slack"
    """
    tool_id_lower = tool_id.lower()
    
    # Check for service prefixes
    if tool_id_lower.startswith('gmail_'):
        return 'gmail'
    elif tool_id_lower.startswith('slack_'):
        return 'slack'
    elif tool_id_lower.startswith('notion_'):
        return 'notion'
    elif tool_id_lower.startswith('calendar_'):
        return 'calendar'
    
    # Default to gmail if unknown
    return 'gmail'


def format_mcp_request(tool_name: str, arguments: Dict[str, Any], request_id: int = 1) -> Dict[str, Any]:
    """
    Format a request according to MCP JSON-RPC specification.
    
    Args:
        tool_name: Name of the MCP tool
        arguments: Arguments for the tool
        request_id: Request ID for JSON-RPC
        
    Returns:
        Formatted JSON-RPC request
    """
    return {
        'jsonrpc': '2.0',
        'method': 'tools/call',
        'params': {
            'name': tool_name,
            'arguments': arguments
        },
        'id': request_id
    }


# Legacy handler functions for backward compatibility
# These can be removed once all tools are dynamically discovered
def _handle_gmail_send_email(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle Gmail send_email MCP tool call.
    This is a wrapper that calls the generic call_mcp_tool function.
    """
    # Extract tool name from function name
    tool_name = 'send_email'
    
    # Validate required parameters
    required_params = ['to', 'subject', 'body']
    for param in required_params:
        if param not in parameters:
            raise ValueError(f"Missing required parameter: {param}")
    
    return call_mcp_tool(tool_name, parameters, service_name='gmail')


def _handle_gmail_search_attachments(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle Gmail search_attachments MCP tool call.
    This is a wrapper that calls the generic call_mcp_tool function.
    """
    # Extract tool name from function name
    tool_name = 'search_attachments'
    
    # Validate required parameters
    if 'query' not in parameters:
        raise ValueError("Missing required parameter: query")
    
    return call_mcp_tool(tool_name, parameters, service_name='gmail')
