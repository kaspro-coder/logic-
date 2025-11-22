# Testing the /analyze-context Endpoint

## Quick Start

1. **Start the server:**
   ```bash
   cd python
   python server.py
   ```

2. **In another terminal, run the test:**
   ```bash
   python test_analyze_context.py
   ```

## Manual Testing with curl

```bash
curl -X POST http://localhost:5000/analyze-context \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2025-11-22T17:28:02",
    "process": "Chrome",
    "title": "Gmail - Inbox",
    "url": "https://mail.google.com",
    "screenshot_base64": "",
    "context": "User is viewing Gmail inbox"
  }'
```

## Manual Testing with Python

```python
import requests
import json

url = "http://localhost:5000/analyze-context"
data = {
    "timestamp": "2025-11-22T17:28:02",
    "process": "Code",
    "title": "loupedeck_context.json - TutorialPlugin - Visual Studio Code",
    "url": "N/A",
    "screenshot_base64": "",
    "context": "User is editing a Python file"
}

response = requests.post(url, json=data)
print(json.dumps(response.json(), indent=2))
```

## Expected Response

```json
{
  "app": "Gmail",
  "context": "Timestamp: 2025-11-22T17:28:02\nProcess: Chrome\n...",
  "workflows": [
    {
      "id": "gmail_send_email",
      "name": "Send Email",
      "description": "Compose and send an email"
    },
    ...
  ]
}
```

## Testing Different Scenarios

### Test with Gmail
```json
{
  "process": "Chrome",
  "title": "Gmail - Inbox",
  "url": "https://mail.google.com",
  "context": "Viewing inbox"
}
```

### Test with Slack
```json
{
  "process": "Slack",
  "title": "Slack - General",
  "url": "https://workspace.slack.com",
  "context": "In Slack channel"
}
```

### Test with VS Code
```json
{
  "process": "Code",
  "title": "file.py - Visual Studio Code",
  "url": "N/A",
  "context": "Editing Python file"
}
```

## Troubleshooting

- **Connection Error**: Make sure the server is running on `http://localhost:5000`
- **Timeout**: LLM calls can take 10-30 seconds, increase timeout if needed
- **No Workflows**: Check if MCP server is configured and running for the detected app
- **Wrong App Detected**: Check the process/title/url fields match expected patterns

