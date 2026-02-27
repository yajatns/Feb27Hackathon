"""backoffice.ai — FastAPI Application Entry Point"""

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from models.database import init_db
from integrations.neo4j_client import neo4j_client
from integrations.openrouter import openrouter_client
from integrations.senso import senso_client
from integrations.tavily import tavily_client
from integrations.reka import reka_client
from integrations.yutori import yutori_client
from integrations.airbyte import airbyte_client
from routes import hire, query, graph, status, override

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB + Neo4j schema. Shutdown: close connections."""
    # Startup
    try:
        await init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ Database init failed (will retry on first request): {e}")

    try:
        await neo4j_client.connect()
        print("✅ Neo4j connected")
        # Setup schema + constraints
        try:
            from backend.graph.client import get_neo4j_driver
            from backend.graph.schema import setup_schema
            driver = await get_neo4j_driver()
            await setup_schema(driver)
            logger.info("Neo4j schema ready")
        except Exception as exc:
            logger.warning("Neo4j schema setup skipped: %s", exc)
    except Exception as e:
        print(f"⚠️ Neo4j not available (graph features disabled): {e}")

    yield

    # Shutdown
    await neo4j_client.close()
    await openrouter_client.close()
    await senso_client.close()
    await tavily_client.close()
    await reka_client.close()
    await yutori_client.close()
    await airbyte_client.close()
    try:
        from backend.graph.client import close_neo4j_driver
        await close_neo4j_driver()
    except Exception:
        pass


app = FastAPI(
    title="backoffice.ai",
    description="One AI that runs your entire back office. You talk. It handles the tools.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(hire.router, prefix="/api", tags=["hire"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(graph.router, prefix="/api", tags=["graph"])
app.include_router(status.router, prefix="/api", tags=["status"])
app.include_router(override.router, prefix="/api", tags=["override"])


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "backoffice.ai", "version": "0.1.0"}


# WebSocket for real-time agent status streaming
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: dict):
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@app.websocket("/api/stream")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time agent status updates via WebSocket."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "ack", "data": {"received": data}})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
