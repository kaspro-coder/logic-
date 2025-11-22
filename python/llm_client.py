"""
LLM client for generating workflow suggestions based on service context.
Integrated with Together AI API for intelligent workflow suggestions.
"""

import json
import requests
from typing import Dict, List, Any, Optional
from config import TOGETHER_AI_API_KEY, TOGETHER_AI_API_URL, TOGETHER_AI_MODEL, MCP_SERVERS


def analyze_context_and_get_workflows(
    timestamp: str,
    process: str,
    title: str,
    url: str,
    screenshot_base64: Optional[str],
    context: str,
    mcp_tools: List[Dict[str, Any]],
    workflows_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main function: Takes context JSON and returns app name, context, and 8 best workflows.
    
    Args:
        timestamp: Timestamp of the context
        process: Process name (e.g., "Code")
        title: Window title
        url: Current URL
        screenshot_base64: Optional base64 screenshot
        context: Additional context string
        mcp_tools: List of available MCP tools from the server
        
    Returns:
        {
            "app": "Gmail",  # Detected app/service name
            "context": "...",  # Context for later MCP calls
            "workflows": [...]  # Exactly 8 best workflows
        }
    """
    # Extract app/service name
    app_name = _extract_app_name(process, title, url, workflows_data)
    
    # Build context string for later use in MCP calls
    context_string = f"""Timestamp: {timestamp}
Process: {process}
Window Title: {title}
URL: {url if url and url != 'N/A' else 'Not applicable'}
Additional Context: {context if context else 'None'}"""
    
    # Convert MCP tools to workflow format
    available_workflows = []
    for tool in mcp_tools:
        tool_name = tool.get('name', '')
        tool_description = tool.get('description', '')
        workflow_id = f"{app_name.lower()}_{tool_name}"
        
        available_workflows.append({
            'id': workflow_id,
            'name': tool_name.replace('_', ' ').title(),
            'description': tool_description or f"Execute {tool_name} tool"
        })
    
    if not available_workflows:
        # No MCP tools available, return empty workflows
        return {
            'app': app_name,
            'context': context_string,
            'workflows': []
        }
    
    # Use LLM to select exactly 8 best workflows based on context
    workflows = _get_best_workflows(
        app_name=app_name,
        context_string=context_string,
        available_workflows=available_workflows,
        screenshot_base64=screenshot_base64
    )
    
    # Ensure we return exactly 8 (or fewer if not enough available)
    workflows = workflows[:8]
    
    return {
        'app': app_name,
        'context': context_string,
        'workflows': workflows
    }


def _get_best_workflows(
    app_name: str,
    context_string: str,
    available_workflows: List[Dict[str, str]],
    screenshot_base64: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Use LLM to select the best 8 workflows based on context.
    """
    # Build workflow list for LLM
    workflows_text = "\n".join([
        f"- {wf['id']}: {wf['name']} - {wf['description']}"
        for wf in available_workflows
    ])
    
    system_prompt = """You are a helpful assistant that selects the most relevant workflows based on user context.
You must return exactly 8 workflows (or fewer if less than 8 are available) as a JSON array.
Each workflow object must have: "id", "name", "description".
Return ONLY valid JSON array, no markdown, no extra text."""
    
    user_prompt = f"""Based on this context, select the 8 most relevant workflows:

Context:
{context_string}

Available Workflows:
{workflows_text}

Return exactly 8 workflows (or all if less than 8) as a JSON array with id, name, and description."""
    
    if screenshot_base64:
        user_prompt += "\n\nA screenshot is provided - use it to better understand what the user is doing."
    
    try:
        # Call LLM API
        llm_response = _call_llm_api(user_prompt, system_prompt, screenshot_base64)
        
        # Parse response
        workflows = _parse_workflows(llm_response)
        
        # Validate and return
        validated = []
        for wf in workflows:
            if isinstance(wf, dict) and 'id' in wf and 'name' in wf:
                validated.append({
                    'id': str(wf.get('id', '')),
                    'name': str(wf.get('name', '')),
                    'description': str(wf.get('description', ''))
                })
        
        return validated if validated else available_workflows[:8]
        
    except Exception as e:
        print(f"LLM error: {e}, returning first 8 workflows")
        return available_workflows[:8]


def _call_llm_api(prompt: str, system_prompt: str, image_base64: Optional[str] = None) -> str:
    """Call Together AI API."""
    headers = {
        'Authorization': f'Bearer {TOGETHER_AI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    messages = [{'role': 'system', 'content': system_prompt}]
    
    # Build user message
    if image_base64:
        # Clean base64 string
        image_data = image_base64
        if image_base64.startswith('data:image'):
            image_data = image_base64.split(',', 1)[1] if ',' in image_base64 else image_base64
        
        messages.append({
            'role': 'user',
            'content': [
                {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{image_data}'}},
                {'type': 'text', 'text': prompt}
            ]
        })
    else:
        messages.append({'role': 'user', 'content': prompt})
    
    payload = {
        'model': TOGETHER_AI_MODEL,
        'messages': messages,
        'temperature': 0.7,
        'max_tokens': 2000
    }
    
    response = requests.post(TOGETHER_AI_API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    
    result = response.json()
    if 'choices' in result and len(result['choices']) > 0:
        return result['choices'][0]['message']['content']
    else:
        raise ValueError(f"Unexpected API response: {result}")


def _parse_workflows(llm_response: str) -> List[Dict[str, str]]:
    """Parse LLM response to extract workflows."""
    response_text = llm_response.strip()
    
    # Remove markdown code blocks
    if response_text.startswith('```'):
        lines = response_text.split('\n')
        json_lines = []
        in_block = False
        for line in lines:
            if line.strip().startswith('```'):
                in_block = not in_block
                continue
            if in_block:
                json_lines.append(line)
        response_text = '\n'.join(json_lines)
    elif '```json' in response_text:
        response_text = response_text.split('```json')[1].split('```')[0].strip()
    
    # Parse JSON
    try:
        parsed = json.loads(response_text)
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict) and 'workflows' in parsed:
            return parsed['workflows']
    except json.JSONDecodeError:
        pass
    
    return []


def _extract_app_name(process: str, title: str, url: str, workflows_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Extract app/service name from process, title, or URL.
    Dynamically checks against available services from MCP_SERVERS and workflows_data.
    """
    process_lower = process.lower()
    title_lower = title.lower()
    url_lower = url.lower() if url and url != 'N/A' else ''
    
    # Get available services dynamically
    available_services = set(MCP_SERVERS.keys())
    if workflows_data:
        available_services.update(workflows_data.keys())
    
    # Build service patterns: service name -> keywords/domains
    service_patterns = {}
    for service in available_services:
        service_lower = service.lower()
        patterns = {
            'keywords': [service_lower],
            'domains': [],
            'process_names': [service_lower]
        }
        
        # Add common domain patterns
        if service_lower == 'gmail':
            patterns['domains'] = ['gmail.com', 'mail.google.com']
            patterns['keywords'].extend(['mail', 'email'])
        elif service_lower == 'slack':
            patterns['domains'] = ['slack.com']
        elif service_lower == 'notion':
            patterns['domains'] = ['notion.so']
        elif service_lower == 'calendar':
            patterns['domains'] = ['calendar.google.com', 'outlook.com/calendar']
            patterns['keywords'].extend(['outlook'])
        
        service_patterns[service] = patterns
    
    # Check process name
    for service, patterns in service_patterns.items():
        for keyword in patterns['keywords']:
            if keyword in process_lower:
                # Special case: Chrome with service in title
                if 'chrome' in process_lower and keyword in title_lower:
                    return service.capitalize()
                elif keyword in process_lower:
                    return service.capitalize()
    
    # Check URL
    if url_lower:
        for service, patterns in service_patterns.items():
            for domain in patterns['domains']:
                if domain in url_lower:
                    return service.capitalize()
    
    # Check title
    for service, patterns in service_patterns.items():
        for keyword in patterns['keywords']:
            if keyword in title_lower:
                return service.capitalize()
    
    # Fallback: try exact match against available services
    for service in available_services:
        service_lower = service.lower()
        if service_lower == process_lower or service_lower in process_lower:
            return service.capitalize()
    
    # Final fallback
    return process if process else 'Unknown'


def get_workflow_suggestions(service_name: str, workflows_data: Dict[str, Any], available_tools: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
    """
    Simple function for /list-workflows endpoint (legacy support).
    Just returns available tools or workflows from workflows_data.
    """
    if available_tools:
        return available_tools
    
    service_name_lower = service_name.lower()
    if workflows_data and service_name_lower in workflows_data:
        return workflows_data[service_name_lower].get('workflows', [])
    
    return []
