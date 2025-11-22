# Implementation TODOs

## ✅ Completed

1. **Flask Backend Server** - REST API endpoints implemented
   - ✅ GET /list-workflows
   - ✅ POST /trigger-workflow
   - ✅ GET /health
   - ✅ CORS enabled for localhost

2. **Together AI Integration** - LLM workflow suggestions
   - ✅ API key configured
   - ✅ HTTP requests to Together AI API
   - ✅ JSON response parsing
   - ✅ Fallback to workflows.json if LLM fails

3. **Project Structure** - All core files created
   - ✅ server.py
   - ✅ mcp_client.py
   - ✅ llm_client.py
   - ✅ data/workflows.json
   - ✅ requirements.txt

## 🔧 Remaining TODOs

### 1. MCP Server Integration (HIGH PRIORITY)
**File:** `backend/mcp_client.py`

**Current Status:** MCP tool calls are stubbed/simulated

**Tasks:**
- [ ] Set up connection to actual MCP server (HTTP endpoint or stdio)
- [ ] Replace stubbed `_handle_gmail_send_email()` with real HTTP requests to MCP server
- [ ] Replace stubbed `_handle_gmail_search_attachments()` with real HTTP requests to MCP server
- [ ] Add MCP server URL/connection configuration (environment variable or config file)
- [ ] Implement proper error handling for MCP server failures
- [ ] Add authentication if MCP server requires it

**Example Implementation:**
```python
# In mcp_client.py, replace TODO comments with:
MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', 'http://localhost:3000/mcp')
response = requests.post(MCP_SERVER_URL, json=mcp_request, headers={'Content-Type': 'application/json'})
```

### 2. Additional MCP Tools (MEDIUM PRIORITY)
**File:** `backend/mcp_client.py`

**Tasks:**
- [ ] Add Slack MCP tools (send_message, search_messages, set_status)
- [ ] Add Notion MCP tools (create_page, search_pages, add_to_database)
- [ ] Add Calendar MCP tools (create_event, view_schedule)
- [ ] Extend `tool_handlers` dictionary with new tool mappings
- [ ] Create handler functions for each new tool

### 3. C# Plugin Integration (MEDIUM PRIORITY)
**File:** `ExamplePlugin/src/`

**Tasks:**
- [ ] Create HTTP client wrapper in C# plugin
- [ ] Implement workflow listing action that calls GET /list-workflows
- [ ] Implement workflow trigger action that calls POST /trigger-workflow
- [ ] Add error handling and retry logic
- [ ] Add UI components to display workflows from backend
- [ ] Handle service detection (detect active application: Gmail, Slack, etc.)

**Example C# Code:**
```csharp
// In ExamplePlugin, add HTTP client
private static readonly HttpClient httpClient = new HttpClient 
{ 
    BaseAddress = new Uri("http://localhost:5000") 
};

// Call backend API
var response = await httpClient.GetAsync($"/list-workflows?service={serviceName}");
var workflows = await response.Content.ReadFromJsonAsync<List<Workflow>>();
```

### 4. Environment Configuration (LOW PRIORITY)
**File:** `backend/`

**Tasks:**
- [ ] Create `.env` file support (use python-dotenv)
- [ ] Move API keys to environment variables (security best practice)
- [ ] Add configuration file for MCP server settings
- [ ] Document environment variable requirements

**Implementation:**
```bash
# Install python-dotenv
pip install python-dotenv

# Create .env file
TOGETHER_AI_API_KEY=your_key_here
MCP_SERVER_URL=http://localhost:3000/mcp
```

### 5. Error Handling & Logging (MEDIUM PRIORITY)
**Files:** `backend/server.py`, `backend/mcp_client.py`, `backend/llm_client.py`

**Tasks:**
- [ ] Add structured logging (use Python logging module)
- [ ] Improve error messages for API responses
- [ ] Add request/response logging for debugging
- [ ] Add timeout handling for external API calls
- [ ] Add retry logic for transient failures

### 6. Testing (LOW PRIORITY)
**File:** `backend/`

**Tasks:**
- [ ] Add unit tests for mcp_client functions
- [ ] Add unit tests for llm_client functions
- [ ] Add integration tests for API endpoints
- [ ] Add mock MCP server for testing
- [ ] Test error scenarios (API failures, invalid inputs)

### 7. Documentation (LOW PRIORITY)
**File:** `backend/README.md`

**Tasks:**
- [ ] Update README with Together AI setup instructions
- [ ] Add MCP server setup instructions
- [ ] Add C# plugin integration examples
- [ ] Add troubleshooting section
- [ ] Add API documentation with examples

## Priority Summary

**Must Have (for MVP):**
1. MCP Server Integration (#1)
2. C# Plugin Integration (#3) - at least basic workflow listing

**Should Have (for full functionality):**
3. Additional MCP Tools (#2)
4. Error Handling & Logging (#5)

**Nice to Have (for production):**
5. Environment Configuration (#4)
6. Testing (#6)
7. Documentation (#7)

## Quick Start Checklist

Before running the backend:
- [x] Install dependencies: `pip install -r requirements.txt`
- [x] Together AI API key configured (hardcoded for now)
- [ ] MCP server running and accessible (if using real MCP tools)
- [ ] Start backend: `python server.py`
- [ ] Test API: `python test_api.py`

## Notes

- The Together AI integration is complete and functional
- MCP tool calls currently return mock responses - replace with actual MCP server calls
- The C# plugin needs to be updated to call the backend API endpoints
- All core infrastructure is in place, focus on MCP server integration next

