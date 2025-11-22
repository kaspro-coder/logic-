"""
LLM client for generating workflow suggestions based on service context.
Integrated with Together AI API for intelligent workflow suggestions.
"""

import json
import os
import requests
from typing import Dict, List, Any, Optional
from config import TOGETHER_AI_API_KEY, TOGETHER_AI_API_URL, TOGETHER_AI_MODEL


def get_workflow_suggestions(service_name: str, workflows_data: Dict[str, Any], available_tools: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
    """
    Get ranked list of workflow suggestions for a given service.
    Uses Together AI to generate intelligent workflow suggestions.
    
    Args:
        service_name: Name of the active service (e.g., "Gmail", "Slack")
        workflows_data: Dictionary containing service-to-workflow mappings
        available_tools: Optional list of tools from MCP server to rank/suggest
        
    Returns:
        List of workflow dictionaries with id, name, and description
    """
    service_name_lower = service_name.lower()
    
    # Priority: Use available_tools from MCP server if provided
    if available_tools:
        try:
            # Use LLM to rank the MCP tools
            llm_suggestions = _get_llm_workflow_suggestions(service_name, available_tools)
            if llm_suggestions:
                return llm_suggestions
        except Exception as e:
            print(f"Warning: LLM API call failed: {e}. Using MCP tools directly.")
        # Fallback to MCP tools if LLM fails
        return available_tools
    
    # Fallback: Get workflows from workflows_data file
    available_workflows = []
    if workflows_data and service_name_lower in workflows_data:
        available_workflows = workflows_data[service_name_lower].get('workflows', [])
    
    # Use LLM to generate intelligent, ranked workflow suggestions
    try:
        llm_suggestions = _get_llm_workflow_suggestions(service_name, available_workflows)
        if llm_suggestions:
            return llm_suggestions
    except Exception as e:
        print(f"Warning: LLM API call failed: {e}. Falling back to default suggestions.")
    
    # Fallback to hardcoded suggestions if LLM fails
    if available_workflows:
        return available_workflows
    
    return _stub_llm_suggestions(service_name)


def _stub_llm_suggestions(service_name: str) -> List[Dict[str, str]]:
    """
    Stub LLM function that returns hardcoded workflow suggestions.
    In production, this would call an actual LLM API (OpenAI, Anthropic, etc.)
    
    Args:
        service_name: Name of the service
        
    Returns:
        List of workflow suggestions
    """
    # Hardcoded suggestions for common services
    service_suggestions = {
        'gmail': [
            {
                'id': 'gmail_send_email',
                'name': 'Send Email',
                'description': 'Compose and send an email to a recipient'
            },
            {
                'id': 'gmail_search_attachments',
                'name': 'Search Attachments',
                'description': 'Search for emails with attachments matching your query'
            },
            {
                'id': 'gmail_quick_reply',
                'name': 'Quick Reply',
                'description': 'Send a quick reply to the latest email'
            }
        ],
        'slack': [
            {
                'id': 'slack_send_message',
                'name': 'Send Message',
                'description': 'Send a message to a Slack channel or user'
            },
            {
                'id': 'slack_search_messages',
                'name': 'Search Messages',
                'description': 'Search for messages in Slack channels'
            },
            {
                'id': 'slack_set_status',
                'name': 'Set Status',
                'description': 'Update your Slack status and availability'
            }
        ],
        'notion': [
            {
                'id': 'notion_create_page',
                'name': 'Create Page',
                'description': 'Create a new page in Notion'
            },
            {
                'id': 'notion_search_pages',
                'name': 'Search Pages',
                'description': 'Search for pages in your Notion workspace'
            }
        ]
    }
    
    # Return suggestions for the service, or default suggestions
    suggestions = service_suggestions.get(service_name.lower(), [
        {
            'id': f'{service_name.lower()}_action_1',
            'name': f'{service_name} Action 1',
            'description': f'Perform an action in {service_name}'
        },
        {
            'id': f'{service_name.lower()}_action_2',
            'name': f'{service_name} Action 2',
            'description': f'Perform another action in {service_name}'
        }
    ])
    
    return suggestions


def call_llm_api(prompt: str, system_prompt: Optional[str] = None, image_base64: Optional[str] = None) -> str:
    """
    Call Together AI API to generate workflow suggestions.
    
    Args:
        prompt: The user prompt/question
        system_prompt: Optional system prompt for context
        image_base64: Optional base64-encoded image (for vision models)
        
    Returns:
        LLM response as a string
    """
    headers = {
        'Authorization': f'Bearer {TOGETHER_AI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    messages = []
    if system_prompt:
        messages.append({
            'role': 'system',
            'content': system_prompt
        })
    
    # Build user message - support both text and vision
    user_message = {
        'role': 'user',
        'content': []
    }
    
    # Add image if provided (for vision models)
    if image_base64:
        # Ensure base64 string doesn't have data URL prefix
        image_data = image_base64
        if image_base64.startswith('data:image'):
            # Extract base64 part from data URL
            image_data = image_base64.split(',', 1)[1] if ',' in image_base64 else image_base64
        
        user_message['content'].append({
            'type': 'image_url',
            'image_url': {
                'url': f'data:image/png;base64,{image_data}'
            }
        })
    
    # Add text prompt
    user_message['content'].append({
        'type': 'text',
        'text': prompt
    })
    
    # If no image, use simple string format for compatibility
    if not image_base64:
        user_message = {
            'role': 'user',
            'content': prompt
        }
    
    messages.append(user_message)
    
    payload = {
        'model': TOGETHER_AI_MODEL,
        'messages': messages,
        'temperature': 0.7,
        'max_tokens': 1000
    }
    
    try:
        response = requests.post(
            TOGETHER_AI_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            raise ValueError(f"Unexpected API response format: {result}")
            
    except requests.exceptions.RequestException as e:
        print(f"Together AI API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        raise
    except KeyError as e:
        print(f"Error parsing Together AI response: {e}")
        raise ValueError(f"Failed to parse API response: {result}")


def parse_llm_workflow_suggestions(llm_response: str, service_name: str) -> List[Dict[str, str]]:
    """
    Parse LLM response to extract workflow suggestions.
    Expects JSON format with workflow objects containing id, name, and description.
    
    Args:
        llm_response: Raw response from LLM
        service_name: Name of the service
        
    Returns:
        List of parsed workflow suggestions
    """
    try:
        # Try to parse as JSON first
        # The LLM might return JSON wrapped in markdown code blocks
        response_text = llm_response.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            # Extract JSON from code block
            lines = response_text.split('\n')
            json_lines = []
            in_code_block = False
            for line in lines:
                if line.strip().startswith('```'):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    json_lines.append(line)
            response_text = '\n'.join(json_lines)
        elif response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        # Try to parse as JSON
        try:
            parsed = json.loads(response_text)
            if isinstance(parsed, list):
                # Validate workflow format
                workflows = []
                for item in parsed:
                    if isinstance(item, dict) and 'id' in item and 'name' in item:
                        workflows.append({
                            'id': item.get('id', ''),
                            'name': item.get('name', ''),
                            'description': item.get('description', '')
                        })
                return workflows
            elif isinstance(parsed, dict) and 'workflows' in parsed:
                return parsed['workflows']
        except json.JSONDecodeError:
            pass
        
        # If JSON parsing fails, try to extract structured data from text
        # This is a fallback for when LLM returns plain text
        workflows = []
        lines = response_text.split('\n')
        current_workflow = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_workflow:
                    workflows.append(current_workflow)
                    current_workflow = {}
                continue
            
            # Try to extract workflow information from text
            if 'id:' in line.lower() or 'tool:' in line.lower():
                parts = line.split(':', 1)
                if len(parts) == 2:
                    current_workflow['id'] = parts[1].strip()
            elif 'name:' in line.lower() or 'title:' in line.lower():
                parts = line.split(':', 1)
                if len(parts) == 2:
                    current_workflow['name'] = parts[1].strip()
            elif 'description:' in line.lower() or 'desc:' in line.lower():
                parts = line.split(':', 1)
                if len(parts) == 2:
                    current_workflow['description'] = parts[1].strip()
        
        if current_workflow:
            workflows.append(current_workflow)
        
        return workflows if workflows else []
        
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        return []


def _get_llm_workflow_suggestions(service_name: str, available_workflows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Use Together AI to generate intelligent workflow suggestions for a service.
    
    Args:
        service_name: Name of the service
        available_workflows: List of available workflows from workflows.json (for context)
        
    Returns:
        List of workflow suggestions from LLM
    """
    # Build context about available workflows
    workflow_context = ""
    if available_workflows:
        workflow_context = "\nAvailable workflows for this service:\n"
        for wf in available_workflows[:5]:  # Limit to top 5 for context
            workflow_context += f"- {wf.get('name', '')}: {wf.get('description', '')}\n"
    
    system_prompt = """You are a helpful assistant that suggests relevant workflows for productivity applications.
Given a service name (like Gmail, Slack, Notion, etc.), suggest 3-5 most useful workflows that users might want to perform.
Return your response as a JSON array of workflow objects, each with:
- "id": a unique identifier (lowercase, underscores, e.g., "gmail_send_email")
- "name": a short, descriptive name (e.g., "Send Email")
- "description": a brief description of what the workflow does

Focus on the most common and useful workflows for the given service.
Return ONLY valid JSON, no additional text or markdown formatting."""

    user_prompt = f"""Suggest the top 3-5 most useful workflows for {service_name}.{workflow_context}

Return a JSON array of workflow objects with id, name, and description fields."""

    try:
        llm_response = call_llm_api(user_prompt, system_prompt)
        workflows = parse_llm_workflow_suggestions(llm_response, service_name)
        
        # Validate and ensure required fields
        validated_workflows = []
        for wf in workflows:
            if isinstance(wf, dict) and 'id' in wf and 'name' in wf:
                validated_workflows.append({
                    'id': str(wf.get('id', '')),
                    'name': str(wf.get('name', '')),
                    'description': str(wf.get('description', ''))
                })
        
        return validated_workflows if validated_workflows else []
        
    except Exception as e:
        print(f"Error getting LLM workflow suggestions: {e}")
        return []


def get_contextual_workflows(
    process: str,
    title: str,
    url: str,
    context: str,
    screenshot_base64: Optional[str] = None,
    workflows_data: Optional[Dict[str, Any]] = None,
    available_tools: Optional[List[Dict[str, str]]] = None
) -> List[Dict[str, str]]:
    """
    Get workflow suggestions based on user's current screen context.
    Uses LLM to analyze the context (process, title, URL, screenshot) and suggest relevant workflows.
    
    Args:
        process: Name of the active process/application
        title: Window title
        url: Current URL (if applicable)
        context: Additional context information
        screenshot_base64: Optional base64-encoded screenshot
        workflows_data: Dictionary containing service-to-workflow mappings
        available_tools: Optional list of tools from MCP server
        
    Returns:
        List of workflow dictionaries with id, name, and description
    """
    # Extract service name from process/title
    service_name = extract_service_name(process, title, url)
    
    # Build context description for LLM
    context_description = f"""Current Application Context:
- Process: {process}
- Window Title: {title}
- URL: {url if url and url != 'N/A' else 'Not applicable'}
- Additional Context: {context if context else 'None provided'}
"""
    
    # Get available workflows for the service
    available_workflows = []
    if workflows_data and service_name.lower() in workflows_data:
        available_workflows = workflows_data[service_name.lower()].get('workflows', [])
    
    # If MCP tools are available, use those
    if available_tools:
        workflows_to_rank = available_tools
    elif available_workflows:
        workflows_to_rank = available_workflows
    else:
        # Fallback to stub suggestions
        return _stub_llm_suggestions(service_name)
    
    # Build workflow context
    workflow_context = ""
    if workflows_to_rank:
        workflow_context = "\nAvailable workflows for this service:\n"
        for wf in workflows_to_rank[:10]:  # Limit to top 10 for context
            wf_name = wf.get('name', '')
            wf_desc = wf.get('description', '')
            workflow_context += f"- {wf_name}: {wf_desc}\n"
    
    # Create enhanced system prompt
    system_prompt = """You are a helpful assistant that suggests relevant workflows based on the user's current screen context.
Analyze the user's current application, window title, and any provided context to suggest the most relevant workflows.
Return your response as a JSON array of workflow objects, each with:
- "id": a unique identifier (lowercase, underscores, e.g., "gmail_send_email")
- "name": a short, descriptive name (e.g., "Send Email")
- "description": a brief description of what the workflow does

Focus on workflows that are most relevant to what the user is currently doing based on the context.
Return ONLY valid JSON, no additional text or markdown formatting."""
    
    # Create user prompt with context
    user_prompt = f"""Based on the following context, suggest the top 3-5 most relevant workflows:
{context_description}
{workflow_context}

Analyze the context and suggest workflows that would be most useful for the user right now.
Return a JSON array of workflow objects with id, name, and description fields."""
    
    # If screenshot is provided, mention it in the prompt
    if screenshot_base64:
        user_prompt += "\n\nA screenshot of the current screen is also provided. Use it to better understand the context."
    
    try:
        # Call LLM with context and optional screenshot
        llm_response = call_llm_api(user_prompt, system_prompt, image_base64=screenshot_base64)
        workflows = parse_llm_workflow_suggestions(llm_response, service_name)
        
        # Validate and ensure required fields
        validated_workflows = []
        for wf in workflows:
            if isinstance(wf, dict) and 'id' in wf and 'name' in wf:
                validated_workflows.append({
                    'id': str(wf.get('id', '')),
                    'name': str(wf.get('name', '')),
                    'description': str(wf.get('description', ''))
                })
        
        # If LLM didn't return valid workflows, fallback to available workflows
        if validated_workflows:
            return validated_workflows
        elif workflows_to_rank:
            return workflows_to_rank[:5]  # Return top 5
        else:
            return _stub_llm_suggestions(service_name)
            
    except Exception as e:
        print(f"Error getting contextual workflows: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to available workflows
        if workflows_to_rank:
            return workflows_to_rank[:5]
        return _stub_llm_suggestions(service_name)


def extract_service_name(process: str, title: str, url: str) -> str:
    """
    Extract service name from process, title, or URL.
    
    Args:
        process: Process name
        title: Window title
        url: Current URL
        
    Returns:
        Extracted service name (e.g., "Gmail", "Slack", "Notion")
    """
    # Normalize inputs
    process_lower = process.lower()
    title_lower = title.lower()
    url_lower = url.lower() if url and url != 'N/A' else ''
    
    # Check for common services in process name
    if 'gmail' in process_lower or 'chrome' in process_lower and 'gmail' in title_lower:
        return 'Gmail'
    elif 'slack' in process_lower:
        return 'Slack'
    elif 'notion' in process_lower:
        return 'Notion'
    elif 'calendar' in process_lower or 'outlook' in process_lower:
        return 'Calendar'
    elif 'code' in process_lower or 'vscode' in process_lower:
        # VS Code - could be various services, check title/context
        if 'gmail' in title_lower:
            return 'Gmail'
        elif 'slack' in title_lower:
            return 'Slack'
        else:
            return 'Code'  # Default for code editors
    
    # Check URL for service indicators
    if url_lower:
        if 'gmail.com' in url_lower or 'mail.google.com' in url_lower:
            return 'Gmail'
        elif 'slack.com' in url_lower:
            return 'Slack'
        elif 'notion.so' in url_lower:
            return 'Notion'
        elif 'calendar.google.com' in url_lower or 'outlook.com/calendar' in url_lower:
            return 'Calendar'
    
    # Check title for service indicators
    if 'gmail' in title_lower:
        return 'Gmail'
    elif 'slack' in title_lower:
        return 'Slack'
    elif 'notion' in title_lower:
        return 'Notion'
    elif 'calendar' in title_lower:
        return 'Calendar'
    
    # Default fallback
    return process if process else 'Unknown'

