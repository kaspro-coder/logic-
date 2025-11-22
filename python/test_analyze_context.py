"""
Quick test script for the /analyze-context endpoint.
Run this after starting the server.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"


def test_analyze_context():
    """Test the /analyze-context endpoint with sample data."""
    
    # Sample test data matching the expected format
    test_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "process": "Chrome",
        "title": "Gmail - Inbox (5) - Google Chrome",
        "url": "https://mail.google.com/mail/u/0/#inbox",
        "screenshot_base64": "",  # Leave empty for text-only test
        "context": "User is viewing Gmail inbox with 5 unread emails. Currently looking at an email from john@example.com about project updates."
    }
    
    print("=" * 60)
    print("Testing /analyze-context endpoint")
    print("=" * 60)
    print(f"\nSending request with data:")
    print(json.dumps(test_data, indent=2))
    print("\n" + "-" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze-context",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60  # LLM calls can take longer
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Success! Response:")
            print(f"  App: {result.get('app', 'Unknown')}")
            print(f"  Workflows: {len(result.get('workflows', []))} found")
            print(f"\n  Context (first 200 chars):")
            print(f"  {result.get('context', '')[:200]}...")
            print(f"\n  Workflows:")
            for i, wf in enumerate(result.get('workflows', [])[:8], 1):
                print(f"    {i}. {wf.get('name', 'N/A')} - {wf.get('description', 'N/A')[:50]}...")
            
            print("\n" + "-" * 60)
            print("Full Response:")
            print(json.dumps(result, indent=2))
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server!")
        print("Make sure the server is running:")
        print("  python server.py")
    except requests.exceptions.Timeout:
        print("\n❌ Error: Request timed out (LLM call took too long)")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_analyze_context()

