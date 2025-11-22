"""
Flask backend server for Logitech MX Creative Console hackathon prototype.
Provides REST API endpoints for workflow management and MCP tool execution.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from typing import Dict, List, Any

from mcp_client import call_mcp_tool, list_mcp_tools, MCPError
from llm_client import get_workflow_suggestions, get_contextual_workflows
from config import SERVER_HOST, SERVER_PORT

app = Flask(__name__)
CORS(app)  # Enable CORS for localhost requests from C# plugin

# Load workflows data
WORKFLOWS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'workflows.json')
workflows_data = {}


def load_workflows():
    """Load workflows data from JSON file."""
    global workflows_data
    try:
        with open(WORKFLOWS_FILE, 'r', encoding='utf-8') as f:
            workflows_data = json.load(f)
    except FileNotFoundError:
        print(f"Warning: {WORKFLOWS_FILE} not found. Using empty workflows.")
        workflows_data = {}
    except json.JSONDecodeError as e:
        print(f"Error parsing {WORKFLOWS_FILE}: {e}")
        workflows_data = {}


@app.route('/list-workflows', methods=['GET'])
def list_workflows():
    """
    GET /list-workflows?service=SERVICE_NAME
    
    Queries the MCP server for available tools, then optionally uses LLM to rank/suggest workflows.
    Returns a list of workflow suggestions for the active service.
    Response: [{"id": "...", "name": "...", "description": "..."}]
    """
    service_name = request.args.get('service', '').strip()
    
    if not service_name:
        return jsonify({
            'error': 'Missing required parameter: service'
        }), 400
    
    try:
        # Step 1: Query MCP server for available tools
        mcp_tools = []
        try:
            mcp_tools = list_mcp_tools(service_name)
            print(f"[MCP] Found {len(mcp_tools)} tools for {service_name}")
        except MCPError as e:
            print(f"[MCP] Warning: Could not query MCP server for {service_name}: {e}")
            print(f"[MCP] Falling back to workflows.json and LLM suggestions")
        except Exception as e:
            print(f"[MCP] Unexpected error querying MCP server: {e}")
        
        # Step 2: Convert MCP tools to workflow format
        workflows_from_mcp = []
        if mcp_tools:
            for tool in mcp_tools:
                tool_name = tool.get('name', '')
                tool_description = tool.get('description', '')
                
                # Create workflow ID (service_tool format)
                workflow_id = f"{service_name.lower()}_{tool_name}"
                
                workflows_from_mcp.append({
                    'id': workflow_id,
                    'name': tool_name.replace('_', ' ').title(),
                    'description': tool_description or f"Execute {tool_name} tool"
                })
        
        # Step 3: Use LLM to rank/suggest workflows (if MCP tools found) or fallback
        if workflows_from_mcp:
            # Pass MCP tools to LLM for ranking
            try:
                ranked_workflows = get_workflow_suggestions(
                    service_name, 
                    workflows_data,
                    available_tools=workflows_from_mcp
                )
                if ranked_workflows:
                    return jsonify(ranked_workflows)
            except Exception as e:
                print(f"[LLM] Warning: LLM ranking failed: {e}. Using MCP tools directly.")
            
            # Fallback to MCP tools if LLM fails
            return jsonify(workflows_from_mcp)
        else:
            # No MCP tools found, use LLM with workflows.json fallback
            workflows = get_workflow_suggestions(service_name, workflows_data)
            return jsonify(workflows)
            
    except Exception as e:
        print(f"Error in list_workflows: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Failed to retrieve workflows: {str(e)}'
        }), 500


@app.route('/trigger-workflow', methods=['POST'])
def trigger_workflow():
    """
    POST /trigger-workflow
    
    Accepts JSON: {"tool": "TOOL_ID", "parameters": {...}}
    Calls the corresponding MCP tool and returns the result.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Request body must be JSON'
            }), 400
        
        tool_id = data.get('tool')
        parameters = data.get('parameters', {})
        
        if not tool_id:
            return jsonify({
                'error': 'Missing required field: tool'
            }), 400
        
        # Extract service name from tool_id if not provided
        service_name = data.get('service')
        if not service_name:
            # Try to infer from tool_id (e.g., "gmail_send_email" -> "gmail")
            parts = tool_id.split('_', 1)
            if len(parts) > 1:
                service_name = parts[0]
        
        # Call MCP tool
        try:
            result = call_mcp_tool(tool_id, parameters, service_name=service_name)
            
            return jsonify({
                'success': True,
                'result': result
            })
        except MCPError as e:
            print(f"MCP Error in trigger_workflow: {e}")
            return jsonify({
                'error': f'MCP server error: {str(e)}',
                'success': False
            }), 500
        except ValueError as e:
            print(f"Validation Error in trigger_workflow: {e}")
            return jsonify({
                'error': f'Invalid parameters: {str(e)}',
                'success': False
            }), 400
    except Exception as e:
        print(f"Error in trigger_workflow: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Failed to trigger workflow: {str(e)}',
            'success': False
        }), 500


@app.route('/analyze-context', methods=['POST'])
def analyze_context():
    """
    POST /analyze-context
    
    Receives context information about the user's current screen and returns relevant workflows.
    Accepts JSON:
    {
        "timestamp": "2025-11-22T17:28:02",
        "process": "Code",
        "title": "loupedeck_context.json - TutorialPlugin - Visual Studio Code",
        "url": "N/A",
        "screenshot_base64": "...",
        "context": "..."
    }
    
    Returns:
    [{"id": "...", "name": "...", "description": "..."}]
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Request body must be JSON'
            }), 400
        
        # Extract context information
        process = data.get('process', '').strip()
        title = data.get('title', '').strip()
        url = data.get('url', 'N/A').strip()
        screenshot_base64 = data.get('screenshot_base64', '').strip()
        context = data.get('context', '').strip()
        
        if not process and not title:
            return jsonify({
                'error': 'Missing required fields: process or title'
            }), 400
        
        # Only pass screenshot if it's not empty
        screenshot = screenshot_base64 if screenshot_base64 else None
        
        # Try to get MCP tools for the inferred service
        # Extract service name from context
        from llm_client import extract_service_name
        service_name = extract_service_name(process, title, url)
        
        # Query MCP server for available tools
        mcp_tools = []
        try:
            mcp_tools = list_mcp_tools(service_name)
            print(f"[MCP] Found {len(mcp_tools)} tools for {service_name}")
        except MCPError as e:
            print(f"[MCP] Warning: Could not query MCP server for {service_name}: {e}")
        except Exception as e:
            print(f"[MCP] Unexpected error querying MCP server: {e}")
        
        # Convert MCP tools to workflow format
        available_tools = []
        if mcp_tools:
            for tool in mcp_tools:
                tool_name = tool.get('name', '')
                tool_description = tool.get('description', '')
                
                # Create workflow ID (service_tool format)
                workflow_id = f"{service_name.lower()}_{tool_name}"
                
                available_tools.append({
                    'id': workflow_id,
                    'name': tool_name.replace('_', ' ').title(),
                    'description': tool_description or f"Execute {tool_name} tool"
                })
        
        # Get contextual workflows using LLM
        try:
            workflows = get_contextual_workflows(
                process=process,
                title=title,
                url=url,
                context=context,
                screenshot_base64=screenshot,
                workflows_data=workflows_data,
                available_tools=available_tools if available_tools else None
            )
            
            return jsonify(workflows)
            
        except Exception as e:
            print(f"Error in analyze_context: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to available tools or workflows
            if available_tools:
                return jsonify(available_tools[:5])
            else:
                # Try to get workflows from workflows_data
                service_name_lower = service_name.lower()
                if workflows_data and service_name_lower in workflows_data:
                    fallback_workflows = workflows_data[service_name_lower].get('workflows', [])
                    return jsonify(fallback_workflows[:5])
                else:
                    return jsonify({
                        'error': f'Failed to retrieve workflows: {str(e)}'
                    }), 500
            
    except Exception as e:
        print(f"Error in analyze_context: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Failed to analyze context: {str(e)}'
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Logitech MX Creative Console Backend'
    })


if __name__ == '__main__':
    # Load workflows on startup
    load_workflows()
    
    print("=" * 60)
    print("Logitech MX Creative Console Backend Server")
    print("=" * 60)
    print(f"Server starting on http://localhost:5000")
    print(f"Endpoints:")
    print(f"  GET  /list-workflows?service=SERVICE_NAME")
    print(f"  POST /trigger-workflow")
    print(f"  POST /analyze-context")
    print(f"  GET  /health")
    print("=" * 60)
    
    # Run Flask server
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=True)

