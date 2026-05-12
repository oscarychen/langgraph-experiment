# HR-RAG

Retrieval-Augmented Generation system for HR document Q&A. A LangGraph agent answers employee questions by retrieving HR policy chunks from pgvector, grading their sufficiency, and combining them with structured HR tools (leave balance, payroll, benefits, etc.).

## High-Level Architecture

```
[React UI :5173] ──HTTP──> [FastAPI :8000] ──> [LangGraph Agent]
                                                     │
                       ┌─────────────────────────────┼─────────────────────────────┐
                       ▼                             ▼                             ▼
              [pgvector retriever]          [Gemini LLM]                  [HR tools]
                       │                             │                             │
                       ▼                             ▼                             ▼
           [AlloyDB Omni + pgvector]   [Google Gemini API]            (mock HRIS data)
```

## RAG Pipeline

The agent is a LangGraph state machine (`backend/src/hr_rag/rag/graph.py`) with five nodes wired by conditional edges:

```
                                                  ┌──► clarify ──► END
                                                  │
   START ─┬─(first turn)──► retrieve ──► grade ───┼──► retrieve (refined query, loop)
          │                                       │
          │                                       ▼
          └─(follow-up turn)────────────────► [ agent ] ──┬──► tools
                                                  ▲       │
                                                  │       ├──► retrieve (agent-initiated)
                                                  │       │
                                                  └───────┴──► END
```

There is a single `agent` node — both entry branches converge on it, and both `tools` and the agent-initiated `retrieve` loop back into it until the agent produces a reply with no tool calls. The entry edge branches on whether the request carries prior conversation: a first turn runs the deterministic `retrieve → grade` prefix; a follow-up turn (any prior `AIMessage` in state) hands the full history straight to the agent, which decides whether to answer, call an HR tool, or re-retrieve.

### Nodes

| Node       | Responsibility                                                                                          |
|------------|---------------------------------------------------------------------------------------------------------|
| `retrieve` | Embed the query with Gemini embeddings, run cosine-distance search in pgvector, attach chunks to state |
| `grade`    | LLM judge classifies retrieved chunks as `sufficient`, `insufficient`, or `ambiguous` (with refined query / clarification question) |
| `clarify`  | Emits a clarifying question back to the user (terminal)                                                 |
| `agent`    | Gemini chat model bound to HR tools + the `search_hr_documents` signaling tool                          |
| `tools`    | `ToolNode` that executes real HR tools (`get_leave_balance`, `submit_leave_request`, …)                 |

### Routing

Three routers drive the conditional edges:

- **`route_entry`** — picks the entry point for each request. With no prior `AIMessage` in state (first turn), routes to `retrieve` so the question is grounded in fresh policy chunks. Otherwise (follow-up turn), skips the deterministic prefix and hands the full history to `agent` — which can answer directly, call an HR tool, or re-issue `search_hr_documents`. This avoids re-retrieving on contextual replies like "yes" that would be meaningless as standalone queries.
- **`route_after_grade`** — loops back to `retrieve` on `insufficient` (with `refined_query`), branches to `clarify` on `ambiguous` (only for the initial turn), or hands off to `agent` otherwise. Caps the loop at `max_retrieval_attempts` (default 3).
- **`route_after_agent`** — inspects the agent's tool calls. If the agent emits `search_hr_documents`, routes to `retrieve` so the signaling tool's `tool_call_id` is satisfied by the retrieval pipeline. Any other tool call routes to `tools`. No tool call ends the turn.

### Conversation state

The chat endpoint is stateless on the server: each request carries its own `history: [{role, content}, …]` (sent by the React client from its Zustand store) and the new `question`. The handler converts these into LangChain `HumanMessage`/`AIMessage` records and seeds the graph. Only user/assistant turns survive across requests — intermediate `ToolMessage`s and retrieved chunks from prior turns are not replayed, which is sufficient for clarify-style follow-ups since the prior assistant message already paraphrases the cited policy.

## Tech Stack

- **Backend**: FastAPI, LangGraph, LangChain, SQLAlchemy 2 + asyncpg, Alembic, pgvector
- **LLM**: Google Gemini (`gemini-2.5-flash`) via `langchain-google-genai`
- **Embeddings**: `models/gemini-embedding-001` (3072-dim)
- **DB**: AlloyDB Omni (Docker) with pgvector
- **Frontend**: React 19, Vite, TypeScript, Zustand, shadcn/ui, Tailwind v4

## Project Structure

```
backend/src/hr_rag/
├── api/chat.py            # FastAPI chat endpoint
├── rag/
│   ├── graph.py           # LangGraph wiring (nodes + edges)
│   ├── nodes.py           # retrieve / grade / clarify / agent / routers
│   ├── grader.py          # Structured-output sufficiency judge
│   ├── retriever.py       # pgvector cosine search
│   ├── tools.py           # HR tools + search_hr_documents signaling tool
│   ├── prompts.py
│   ├── llm.py
│   └── state.py           # AgentState TypedDict
├── db/                    # SQLAlchemy models + session
└── config.py              # Pydantic settings
frontend/                  # React + Vite UI
db/init/                   # SQL bootstrap
docker-compose.yml         # AlloyDB Omni
Makefile                   # Entry point for all dev tasks
```

## Getting Started

```bash
make setup     # one-time: install deps, install git hooks, init DB
```
Add API key from [Google AI Studio](https://aistudio.google.com/) in .env.
```bash
make dev       # start DB + backend (:8000) + frontend (:5173)
```

See `CLAUDE.md` for the full command reference and conventions. Configure via `.env` (see `.env.example`); key vars are `DATABASE_URL` and `GOOGLE_API_KEY`.