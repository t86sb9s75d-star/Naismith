"""FastAPI application: the API + session gateway for the vertical slice."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .audit import AuditStore
from .config import Settings, get_settings
from .db import Database
from .governance import load_constitution, load_constitutional_tests
from .model_gateway import (
    AnthropicModelAdapter,
    MockModelAdapter,
    ModelGateway,
    ModelProvider,
)
from .repositories import ModelCallRepository, SessionRepository
from .schemas import (
    AuditEvent,
    ConstitutionalTestRegistry,
    ConstitutionInfo,
    CreateSessionRequest,
    HealthResponse,
    MessageResponse,
    ModelProviderInfo,
    ModelProvidersResponse,
    SendMessageRequest,
    Session,
)
from .sessions import ModelUnavailableError, SessionNotFoundError, SessionStore


def _build_gateway(settings: Settings) -> tuple[ModelGateway, list[ModelProviderInfo]]:
    mock = MockModelAdapter()
    anthropic = AnthropicModelAdapter(
        api_key=settings.anthropic_api_key or None,
        model=settings.anthropic_model,
    )
    providers: dict[str, ModelProvider] = {mock.name: mock, anthropic.name: anthropic}
    gateway = ModelGateway(
        providers,
        default_provider=settings.default_model_provider,
        timeout_seconds=settings.model_timeout_seconds,
        max_retries=settings.model_max_retries,
    )
    default = settings.default_model_provider
    info = [
        ModelProviderInfo(
            name=mock.name,
            model_version=mock.model_version,
            is_default=default == mock.name,
            live=True,
            configured=True,
        ),
        ModelProviderInfo(
            name=anthropic.name,
            model_version=anthropic.model_version,
            is_default=default == anthropic.name,
            live=False,  # inert this phase: no network call, no paid usage.
            configured=anthropic.is_configured,
        ),
    ]
    return gateway, info


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    constitution = load_constitution(settings)

    database = Database(settings.database_url)
    database.create_all()

    audit = AuditStore(database)
    sessions_repo = SessionRepository(database)
    model_calls = ModelCallRepository(database)
    gateway, providers_info = _build_gateway(settings)
    sessions = SessionStore(
        model=gateway,
        audit=audit,
        sessions=sessions_repo,
        model_calls=model_calls,
    )

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
    app.state.database = database
    app.state.audit = audit
    app.state.sessions = sessions
    app.state.gateway = gateway

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
        # Serve the constitution loaded once at startup — the same object
        # /health reports — so the two endpoints can never disagree on the
        # active version. This also matches governance intent: a running
        # instance operates under one fixed constitution for its lifetime;
        # adopting a new version is a deploy/restart, not a silent hot-swap
        # (Article III). A future audited admin reload can supersede this.
        return constitution

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

    @app.get(
        "/v1/models/providers",
        response_model=ModelProvidersResponse,
        tags=["models"],
    )
    def list_providers() -> ModelProvidersResponse:
        return ModelProvidersResponse(
            default_provider=gateway.default_provider,
            providers=providers_info,
        )

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
        except ModelUnavailableError as exc:
            # The selected provider could not produce a result (e.g. an inert or
            # unconfigured real provider). The user turn is recorded and the
            # failure is audited; surface a clean 503.
            raise HTTPException(
                status_code=503, detail="model provider unavailable"
            ) from exc

    return app


app = create_app()
