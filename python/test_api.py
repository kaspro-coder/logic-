"""
Simple test script to verify the backend API endpoints.
Run this after starting the server to test the endpoints.
"""

import requests
import json

BASE_URL = "http://localhost:5000"


def test_health():
    """Test the health endpoint."""
    print("Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_list_workflows(service="Gmail"):
    """Test the list-workflows endpoint."""
    print(f"Testing /list-workflows?service={service} endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/list-workflows", params={"service": service}, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            workflows = response.json()
            print(f"Found {len(workflows)} workflows")
            print(f"Response: {json.dumps(workflows, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    print()


def test_analyze_context():
    """Test the analyze-context endpoint."""
    print("Testing /analyze-context endpoint...")
    
    # Test with Gmail context
    payload = {
        "timestamp": "2025-11-22T17:28:02",
        "process": "Chrome",
        "title": "Gmail - Inbox",
        "url": "https://mail.google.com",
        "screenshot_base64": "",  # Optional - leave empty for text-only test
        "context": "User is viewing their inbox, has 5 unread emails"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze-context",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # LLM calls can take longer
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Detected App: {result.get('app', 'Unknown')}")
            print(f"Context: {result.get('context', 'N/A')[:100]}...")  # First 100 chars
            print(f"Workflows Found: {len(result.get('workflows', []))}")
            print(f"Full Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    print()
    
    # Test with VS Code context
    payload2 = {
        "timestamp": "2025-11-22T17:30:00",
        "process": "Code",
        "title": "loupedeck_context.json - TutorialPlugin - Visual Studio Code",
        "url": "N/A",
        "screenshot_base64": "",
        "context": "User is editing a Python file in VS Code"
    }
    
    try:
        response2 = requests.post(
            f"{BASE_URL}/analyze-context",
            json=payload2,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        print(f"Status: {response2.status_code}")
        if response2.status_code == 200:
            result = response2.json()
            print(f"Detected App: {result.get('app', 'Unknown')}")
            print(f"Workflows Found: {len(result.get('workflows', []))}")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Error: {response2.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    print()


def test_trigger_workflow():
    """Test the trigger-workflow endpoint."""
    print("Testing /trigger-workflow endpoint...")
    
    # Test Gmail send_email
    payload = {
        "tool": "gmail_send_email",
        "parameters": {
            "to": "test@example.com",
            "subject": "Test Email",
            "body": "This is a test email from the backend API"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/trigger-workflow",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
    
    # Test Gmail search_attachments
    payload2 = {
        "tool": "gmail_search_attachments",
        "parameters": {
            "query": "from:example@gmail.com",
            "max_results": 5
        }
    }
    
    response2 = requests.post(
        f"{BASE_URL}/trigger-workflow",
        json=payload2,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response2.status_code}")
    print(f"Response: {json.dumps(response2.json(), indent=2)}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Backend API Test Script")
    print("=" * 60)
    print()
    
    try:
        test_health()
        test_list_workflows("Gmail")
        test_list_workflows("Slack")
        test_analyze_context()  # Test the new endpoint
        # test_trigger_workflow()  # Commented out - requires MCP server
        
        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server.")
        print("Make sure the server is running on http://localhost:5000")
    except Exception as e:
        print(f"Error: {e}")

