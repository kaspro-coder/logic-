"""
LLM client for generating workflow suggestions based on service context.
Integrated with Together AI API for intelligent workflow suggestions.
"""

import json
import requests
from typing import Dict, List, Any, Optional
from config import TOGETHER_AI_API_KEY, TOGETHER_AI_API_URL, TOGETHER_AI_MODEL, MCP_SERVERS


def analyze_context_and_get_workflows(
    application_name: str,
    channel_name: str,
    context: str,
) -> Dict[str, Any]:
    """
    Main function: Takes context string and returns 8 best MCP tools that might be useful to the user.
    
    Args:
        application_name: Name of the application (e.g., "Slack")
        channel_name: Name of the channel or person (e.g., "general")
        context: Context string

    Returns:
        {
            "app": application_name,
            "context": context_string,
            "workflows": [...]  # Exactly 8 best MCP tools
        }
    """
    # Build context string for LLM
    context_string = (
        f"Application: {application_name}\n"
        f"Channel: {channel_name}\n"
        f"Additional Context: {context if context else 'None'}"
    )

    # Fetch available MCP tools
    try:
        mcp_tools = list_mcp_tools(application_name)
    except MCPError as e:
        print(f"Failed to fetch MCP tools: {e}")
        return {
            'app': application_name,
            'context': context_string,
            'workflows': []
        }

    # Convert MCP tools to workflow format
    available_workflows = [
        {
            'id': f"{application_name.lower()}_{tool.get('name', '').lower()}",
            'name': tool.get('name', '').replace('_', ' ').title(),
            'description': tool.get('description', f"Execute {tool.get('name', '')} tool")
        }
        for tool in mcp_tools
    ]

    if not available_workflows:
        return {
            'app': application_name,
            'context': context_string,
            'workflows': []
        }

    # Get top 8 workflows using LLM
    try:
        workflows = _get_best_workflows(
            app_name=application_name,
            context_string=context_string,
            available_workflows=available_workflows,
            screenshot_base64=screenshot_base64
        )
    except Exception as e:
        print(f"LLM selection failed: {e}, returning first 8 workflows")
        workflows = available_workflows[:8]

    return {
        'app': application_name,
        'context': context_string,
        'workflows': workflows[:8]
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