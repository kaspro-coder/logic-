# Logitech MX Creative Console Backend

Python backend server for the Logitech MX Creative Console hackathon prototype. Integrates with MCP (Model Context Protocol) servers to provide dynamic, context-aware workflows.

## Features

- ✅ **MCP Server Integration** - Queries MCP servers to discover available tools
- ✅ **Dynamic Workflow Discovery** - Automatically lists tools from MCP servers
- ✅ **LLM-Powered Ranking** - Uses Together AI to intelligently rank workflow suggestions
- ✅ **JSON-RPC Protocol** - Full MCP JSON-RPC support over HTTP
- ✅ **Configurable** - Environment variables and config file support
- ✅ **Error Handling** - Comprehensive error handling for MCP calls

## Setup

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure MCP servers:**
   
   Option A: Use environment variables:
   ```bash
   export GMAIL_MCP_SERVER_URL="http://localhost:3000/mcp"
   export GMAIL_MCP_AUTH_TOKEN="your_token_here"
   export TOGETHER_AI_API_KEY="your_key_here"
   ```

   Option B: Create `config.json` (copy from `config.json.example`):
   ```bash
   cp config.json.example config.json
   # Edit config.json with your MCP server URLs and tokens
   ```

3. **Run the server:**
```bash
python server.py
```

The server will start on `http://localhost:5000` (configurable via `SERVER_HOST` and `SERVER_PORT`)

## API Endpoints

### GET /list-workflows
Get workflow suggestions for a service by querying the MCP server.

**Query Parameters:**
- `service` (required): Name of the service (e.g., "Gmail", "Slack")

**Example:**
```bash
curl "http://localhost:5000/list-workflows?service=Gmail"
```

**Response:**
```json
[
  {
    "id": "gmail_send_email",
    "name": "Send Email",
    "description": "Send an email to one or more recipients"
  },
  {
    "id": "gmail_search_attachments",
    "name": "Search Attachments",
    "description": "Search for emails with attachments"
  }
]
```

**How it works:**
1. Queries the MCP server for the service to get available tools
2. Converts MCP tools to workflow format
3. Optionally uses LLM to rank/suggest the top workflows
4. Returns ranked list of workflows

### POST /trigger-workflow
Trigger an MCP tool workflow by calling the MCP server.

**Request Body:**
```json
{
  "tool": "send_email",
  "service": "gmail",
  "parameters": {
    "to": "recipient@example.com",
    "subject": "Hello",
    "body": "This is a test email"
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "jsonrpc": "2.0",
    "result": {
      "content": [
        {
          "type": "text",
          "text": "Email sent successfully to recipient@example.com"
        }
      ],
      "isError": false
    },
    "id": 1
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "MCP server error: Could not connect to MCP server at http://localhost:3000/mcp. Is the server running?"
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "Logitech MX Creative Console Backend"
}
```

## Project Structure

- `server.py` - Flask backend server with REST API endpoints
- `mcp_client.py` - MCP server client with tool discovery and execution
- `llm_client.py` - Together AI integration for workflow ranking
- `config.py` - Configuration management (environment variables + config file)
- `data/workflows.json` - Fallback service-to-workflow mappings
- `config.json.example` - Example configuration file

## MCP Server Integration

The backend supports connecting to MCP servers via HTTP using JSON-RPC protocol.

### MCP Server Discovery

The `/list-workflows` endpoint automatically:
1. Queries the MCP server using `tools/list` method
2. Retrieves available tools with their schemas
3. Converts tools to workflow format
4. Optionally ranks them using LLM

### MCP Tool Execution

The `/trigger-workflow` endpoint:
1. Formats the request as JSON-RPC
2. Calls the MCP server using `tools/call` method
3. Returns the MCP server response

### Configuration

MCP servers are configured per service:

```python
# In config.py or environment variables
GMAIL_MCP_SERVER_URL = "http://localhost:3000/mcp"
GMAIL_MCP_AUTH_TOKEN = "your_auth_token"
```

### Supported Services

- **Gmail** - Email operations (send_email, search_attachments)
- **Slack** - Messaging operations (send_message, search_messages)
- **Notion** - Note-taking operations (create_page, search_pages)
- **Calendar** - Calendar operations (create_event, view_schedule)

Add more services by updating `MCP_SERVERS` in `config.py`.

## LLM Integration

The backend uses Together AI to intelligently rank workflow suggestions:

1. **Tool Discovery** - MCP servers provide available tools
2. **LLM Ranking** - Together AI ranks tools based on context and user needs
3. **Fallback** - If LLM fails, returns tools directly from MCP server

Configure Together AI in `config.py` or environment variables:
```python
TOGETHER_AI_API_KEY = "your_key_here"
TOGETHER_AI_MODEL = "meta-llama/Llama-3-8b-chat-hf"
```

## Error Handling

The backend includes comprehensive error handling:

- **MCP Connection Errors** - Handles timeouts, connection failures
- **MCP Protocol Errors** - Handles JSON-RPC errors from MCP servers
- **Validation Errors** - Validates required parameters
- **LLM Errors** - Falls back gracefully if LLM fails

All errors return appropriate HTTP status codes and error messages.

## C# Plugin Integration

The C# Logitech plugin can call the backend using HTTP requests:

```csharp
// Example: List workflows
var httpClient = new HttpClient { BaseAddress = new Uri("http://localhost:5000") };
var response = await httpClient.GetAsync($"/list-workflows?service={serviceName}");
var workflows = await response.Content.ReadFromJsonAsync<List<Workflow>>();

// Example: Trigger workflow
var request = new { 
    tool = "send_email", 
    service = "gmail",
    parameters = new { 
        to = "recipient@example.com",
        subject = "Hello",
        body = "Test email"
    } 
};
var response = await httpClient.PostAsJsonAsync("/trigger-workflow", request);
var result = await response.Content.ReadFromJsonAsync<WorkflowResult>();
```

## Testing

Run the test script to verify the API:

```bash
python test_api.py
```

Make sure the backend server is running before testing.

## Development Notes

- The server runs in debug mode by default
- CORS is enabled for localhost requests
- MCP server URLs are configurable per service
- Authentication tokens are optional (if MCP server requires them)
- Timeout for MCP calls is configurable (default: 30 seconds)

## Troubleshooting

**MCP server connection fails:**
- Check that the MCP server is running
- Verify the MCP server URL in config
- Check network connectivity
- Verify authentication token if required

**No tools returned:**
- Check MCP server logs
- Verify the service name matches the configured service
- Check MCP server implements `tools/list` method

**LLM ranking fails:**
- Check Together AI API key is configured
- Verify API key is valid
- Check network connectivity to Together AI
- System will fallback to MCP tools directly
