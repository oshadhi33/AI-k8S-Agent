# AI Kubernetes Troubleshooting Agent

An AI-powered platform that investigates Kubernetes failures, analyzes logs/events/cluster state, identifies root causes, and suggests fixes. Built with **FastAPI**, **React**, **InsForge**, and **OpenRouter**.

## Architecture

```
Kubernetes Cluster
       ↓ kubectl / K8s API
Investigation Layer (pods, logs, events, deployments, network)
       ↓ structured evidence
AI Agent (OpenRouter LLM)
       ↓ diagnosis + fixes
InsForge Backend (auth, history, realtime)
       ↓ API
React Dashboard
       ↓
InsForge Deployment → public URL
```

## Quick Start

### 1. InsForge Setup

1. Create a project at [insforge.dev](https://insforge.dev)
2. Copy **Base URL**, **Anon Key**, and **Service Key**
3. Add your **OpenRouter API key** in InsForge → AI Integration
4. Run the database migration:

```bash
# Via InsForge CLI or dashboard SQL editor
cat migrations/001_investigations.sql
```

5. (Optional) Connect InsForge MCP for agent-native workflows:

```bash
npx @insforge/install --client cursor \
  --env API_KEY=your_service_key \
  --env API_BASE_URL=https://your-project.us-east.insforge.app
```

### 2. Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your InsForge + OpenRouter credentials

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Ensure kubectl is configured for your cluster
uvicorn main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open http://localhost:5173

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/investigations` | Run full investigation |
| POST | `/api/investigations/stream` | SSE streaming progress |
| GET | `/api/investigations` | List investigation history |
| GET | `/api/investigations/{id}` | Get single investigation |

## Supported Problems

- CrashLoopBackOff
- ImagePullBackOff
- OOMKilled
- Pending Pods
- Resource Exhaustion
- Deployment Rollout Failures
- Service Selector Mismatch
- DNS / Networking Issues
- Readiness/Liveness Probe Failures

## Deploy to InsForge

1. Push this repo to GitHub
2. In InsForge dashboard → Sites → Create deployment
3. Set environment variables from `backend/.env.example`
4. For frontend, set `VITE_API_URL` to your backend public URL before build

Or use the InsForge CLI:

```bash
npx @insforge/cli login
npx @insforge/cli deploy
```

## Project Structure

```
ai-k8s-agent/
├── backend/
│   ├── investigation/     # K8s collectors (pods, logs, events, etc.)
│   ├── agent/             # LLM prompt builder + OpenRouter
│   ├── services/          # Orchestration + progress
│   ├── routers/           # FastAPI routes
│   └── main.py
├── frontend/              # React dashboard
├── migrations/            # InsForge Postgres schema
└── README.md
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `INSFORGE_BASE_URL` | InsForge project API URL |
| `INSFORGE_ANON_KEY` | Public anon key for client ops |
| `INSFORGE_SERVICE_KEY` | Server-side privileged key |
| `OPENROUTER_API_KEY` | From InsForge AI Integration |
| `OPENROUTER_MODEL` | e.g. `anthropic/claude-sonnet-4` |
| `KUBECONFIG_PATH` | Optional explicit kubeconfig |
| `K8S_NAMESPACE` | Default namespace |


