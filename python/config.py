"""
Configuration management for MCP servers and API keys.
Supports environment variables and config file.
"""

import os
import json
from typing import Dict, Optional

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')


def load_config() -> Dict[str, any]:
    """Load configuration from file if it exists."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config file: {e}")
    return {}


def get_env_or_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get value from environment variable first, then config file, then default."""
    # Check environment variable first
    value = os.getenv(key)
    if value:
        return value
    
    # Check config file
    config = load_config()
    if key in config:
        return config[key]
    
    # Return default
    return default


# MCP Server Configuration
# Map service names to their MCP server URLs
MCP_SERVERS = {
    'gmail': get_env_or_config('GMAIL_MCP_SERVER_URL', 'http://localhost:3000/mcp'),
    'slack': get_env_or_config('SLACK_MCP_SERVER_URL', 'http://localhost:3001/mcp'),
    'notion': get_env_or_config('NOTION_MCP_SERVER_URL', 'http://localhost:3002/mcp'),
    'calendar': get_env_or_config('CALENDAR_MCP_SERVER_URL', 'http://localhost:3003/mcp'),
}

# MCP Server Authentication
# Map service names to their authentication tokens/keys
MCP_AUTH = {
    'gmail': get_env_or_config('GMAIL_MCP_AUTH_TOKEN'),
    'slack': get_env_or_config('SLACK_MCP_AUTH_TOKEN'),
    'notion': get_env_or_config('NOTION_MCP_AUTH_TOKEN'),
    'calendar': get_env_or_config('CALENDAR_MCP_AUTH_TOKEN'),
}

# Together AI Configuration
TOGETHER_AI_API_KEY = get_env_or_config('TOGETHER_AI_API_KEY', 'tgp_v1_kJIx6K3NHmKtnBPoNQYu1vR55WTed7LNMs4oe-ArjJ0')
TOGETHER_AI_API_URL = 'https://api.together.xyz/v1/chat/completions'
TOGETHER_AI_MODEL = get_env_or_config('TOGETHER_AI_MODEL', 'meta-llama/Llama-3-8b-chat-hf')

# Server Configuration
SERVER_HOST = get_env_or_config('SERVER_HOST', 'localhost')
SERVER_PORT = int(get_env_or_config('SERVER_PORT', '5000'))

# MCP Request Timeout (seconds)
MCP_TIMEOUT = int(get_env_or_config('MCP_TIMEOUT', '30'))


def get_mcp_server_url(service_name: str) -> Optional[str]:
    """Get MCP server URL for a given service."""
    service_lower = service_name.lower()
    return MCP_SERVERS.get(service_lower)


def get_mcp_auth_token(service_name: str) -> Optional[str]:
    """Get authentication token for a given service's MCP server."""
    service_lower = service_name.lower()
    return MCP_AUTH.get(service_lower)


def create_config_file():
    """Create an example config.json file."""
    example_config = {
        "GMAIL_MCP_SERVER_URL": "http://localhost:3000/mcp",
        "SLACK_MCP_SERVER_URL": "http://localhost:3001/mcp",
        "NOTION_MCP_SERVER_URL": "http://localhost:3002/mcp",
        "CALENDAR_MCP_SERVER_URL": "http://localhost:3003/mcp",
        "GMAIL_MCP_AUTH_TOKEN": "your_gmail_auth_token_here",
        "SLACK_MCP_AUTH_TOKEN": "your_slack_auth_token_here",
        "NOTION_MCP_AUTH_TOKEN": "your_notion_auth_token_here",
        "CALENDAR_MCP_AUTH_TOKEN": "your_calendar_auth_token_here",
        "TOGETHER_AI_API_KEY": "your_together_ai_key_here",
        "TOGETHER_AI_MODEL": "meta-llama/Llama-3-8b-chat-hf",
        "SERVER_HOST": "localhost",
        "SERVER_PORT": "5000",
        "MCP_TIMEOUT": "30"
    }
    
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(example_config, f, indent=2)
        print(f"Created example config file: {CONFIG_FILE}")
        print("Please update it with your actual MCP server URLs and authentication tokens.")
    else:
        print(f"Config file already exists: {CONFIG_FILE}")

