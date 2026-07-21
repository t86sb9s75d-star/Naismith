"""FastAPI application: the API + session gateway for the vertical slice."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .audit import AuditStore
from .config import Settings, get_settings
from .governance import load_constitution, load_constitutional_tests
from .model_gateway import MockModelAdapter
from .schemas import (
    AuditEvent,
    ConstitutionalTestRegistry,
    ConstitutionInfo,
    CreateSessionRequest,
    HealthResponse,
    MessageResponse,
    SendMessageRequest,
    Session,
)
from .sessions import SessionNotFoundError, SessionStore


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    constitution = load_constitution(settings)
    audit = AuditStore(settings.audit_log_path)
    model = MockModelAdapter()
    sessions = SessionStore(model=model, audit=audit)

    app = FastAPI(
        title="Naismith API",
        version=__version__,
        summary="Text-first conversation core with a governance skeleton.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Stash shared state for tests / introspection.
    app.state.settings = settings
    app.state.audit = audit
    app.state.sessions = sessions

    @app.get("/health", response_model=HealthResponse, tags=["meta"])
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            version=__version__,
            constitution_version=constitution.version,
        )

    @app.get(
        "/v1/governance/constitution",
        response_model=ConstitutionInfo,
        tags=["governance"],
    )
    def get_constitution() -> ConstitutionInfo:
        # Re-read so an edited constitution is reflected without a restart.
        return load_constitution(settings)

    @app.get(
        "/v1/governance/constitutional-tests",
        response_model=ConstitutionalTestRegistry,
        tags=["governance"],
    )
    def get_constitutional_tests() -> ConstitutionalTestRegistry:
        return load_constitutional_tests(settings)

    @app.get(
        "/v1/governance/audit-events",
        response_model=list[AuditEvent],
        tags=["governance"],
    )
    def get_audit_events(session_id: str | None = None) -> list[AuditEvent]:
        return audit.list(session_id=session_id)

    @app.post("/v1/sessions", response_model=Session, tags=["sessions"])
    def create_session(req: CreateSessionRequest) -> Session:
        return sessions.create(req)

    @app.get("/v1/sessions/{session_id}", response_model=Session, tags=["sessions"])
    def get_session(session_id: str) -> Session:
        try:
            return sessions.get(session_id)
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail="session not found") from exc

    @app.post(
        "/v1/sessions/{session_id}/messages",
        response_model=MessageResponse,
        tags=["sessions"],
    )
    def send_message(session_id: str, req: SendMessageRequest) -> MessageResponse:
        try:
            return sessions.handle_message(session_id, req.text)
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail="session not found") from exc

    return app


app = create_app()
