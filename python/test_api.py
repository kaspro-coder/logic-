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
        test_trigger_workflow()
        
        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server.")
        print("Make sure the server is running on http://localhost:5000")
    except Exception as e:
        print(f"Error: {e}")

