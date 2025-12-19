# CoursePilot WebUI Plugin

## Overview

FastAPI backend + SvelteKit frontend for the CoursePilot educational AI assistant.

**P0 Scope:** Basic chat interface (input → LLM → streaming output). No adaptive behavior yet.

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Browser                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │           SvelteKit Frontend (:5173)             │   │
│  └─────────────────────────────────────────────────┘   │
└───────────────────────┬─────────────────────────────────┘
                        │ REST + WebSocket
┌───────────────────────▼─────────────────────────────────┐
│              FastAPI Backend (:8000)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ /api/chat│  │/api/course│ │/api/health│             │
│  └─────┬────┘  └─────┬────┘  └──────────┘             │
└────────┼─────────────┼──────────────────────────────────┘
         │             │
    ┌────▼────┐   ┌────▼────────────┐
    │LLM Gate-│   │Moodle Adapter   │
    │way Mgr  │   │Plugin           │
    └─────────┘   └─────────────────┘
```

## Features

- **REST API** for course data and health checks
- **WebSocket streaming** for real-time LLM responses
- **CORS configured** for SvelteKit dev server
- **Dependency injection** for testability
- **Production mode** serves built SvelteKit as static files

## Usage

### Start API Only (for frontend development)

```bash
cd plugins/coursepilot_webui_plugin
python coursepilot_webui_plugin.py --api-only
```

Or:

```python
from plugins.coursepilot_webui_plugin import start_api
start_api()
```

### Start Full Dev Environment

```bash
# Terminal 1: API
python coursepilot_webui_plugin.py --api-only

# Terminal 2: Frontend (after creating SvelteKit project)
cd frontend && npm run dev
```

### API Endpoints

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/api/health` | GET | Health check |
| `/api/health/ready` | GET | Readiness with dependency checks |
| `/api/courses` | GET | List courses |
| `/api/courses/{id}` | GET | Get course content |
| `/api/courses/{id}/search?q=` | GET | Search course |
| `/api/chat` | POST | Non-streaming chat |
| `/api/chat/ws` | WebSocket | Streaming chat |

### WebSocket Protocol

```javascript
// Connect
const ws = new WebSocket('ws://localhost:8000/api/chat/ws');

// Send message
ws.send(JSON.stringify({ type: 'message', content: 'Hello!' }));

// Receive tokens
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'token') {
    // Append to response
    response += msg.content;
  } else if (msg.type === 'complete') {
    // Full response available
    console.log(msg.content);
  }
};
```

## Module Structure

```
coursepilot_webui_plugin/
├── __init__.py                  # Module exports
├── init.yaml                    # Module metadata
├── coursepilot_webui_plugin.py  # Main entry point
├── refresh.py                   # Lifecycle (npm install, etc.)
├── requirements.txt             # Python deps (FastAPI, uvicorn)
├── .config_template             # Configuration schema
│
├── api/                         # FastAPI backend
│   ├── __init__.py
│   ├── main.py                  # FastAPI app
│   ├── dependencies.py          # DI for managers
│   └── routes/
│       ├── __init__.py
│       ├── health.py            # /api/health
│       ├── courses.py           # /api/courses
│       └── chat.py              # /api/chat (WebSocket)
│
├── frontend/                    # SvelteKit (user-created)
│   └── ... (npm create svelte@latest)
│
├── tests/                       # Unit tests
└── playground/                  # Dev experiments
```

## Frontend Setup (User Task)

```bash
cd plugins/coursepilot_webui_plugin
npm create svelte@latest frontend

# Choose:
# - Template: Skeleton or Demo
# - TypeScript: Yes
# - ESLint, Prettier: Yes

cd frontend
npm install

# Configure Vite proxy (vite.config.ts):
# server: { proxy: { '/api': 'http://localhost:8000' } }
```

## Configuration

See `.config_template` for available options:

```json
{
  "api": {
    "host": "127.0.0.1",
    "port": 8000,
    "cors_origins": ["http://localhost:5173"]
  },
  "frontend": {
    "mode": "dev",
    "dev_port": 5173
  }
}
```

## Dependencies

### Python (requirements.txt)
- fastapi
- uvicorn
- websockets

### ADHD Modules
- `llm_gateway_manager` - LLM abstraction
- `moodle_adapter_plugin` - Course data

## Testing

```bash
# Run tests
pytest plugins/coursepilot_webui_plugin/tests/

# Manual API test
curl http://localhost:8000/api/health
```