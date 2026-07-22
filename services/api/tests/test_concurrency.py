from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from naismith_api.audit import AuditStore
from naismith_api.db import Database
from naismith_api.model_gateway import ModelResult
from naismith_api.repositories import ModelCallRepository, SessionRepository
from naismith_api.schemas import CreateSessionRequest, MessageResponse
from naismith_api.sessions import SessionStore


class _SlowModel:
    """A model that pauses mid-turn, so any cross-request interleaving of the
    user-turn and assistant-turn appends would manifest as a broken pairing."""

    MODEL_VERSION = "slow-test-model"

    @property
    def name(self) -> str:
        return "slow"

    @property
    def model_version(self) -> str:
        return self.MODEL_VERSION

    def generate(self, prompt: str) -> ModelResult:
        time.sleep(0.05)
        return ModelResult(text=f"reply to {prompt}", model_version=self.MODEL_VERSION)


def test_concurrent_same_session_turns_stay_paired(tmp_path: Path) -> None:
    db = Database(f"sqlite:///{tmp_path / 'naismith.db'}")
    db.create_all()
    store = SessionStore(
        model=_SlowModel(),
        audit=AuditStore(db),
        sessions=SessionRepository(db),
        model_calls=ModelCallRepository(db),
    )
    session = store.create(CreateSessionRequest())

    def send(i: int) -> MessageResponse:
        return store.handle_message(session.id, f"msg {i}")

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(send, range(8)))

    # The invariant Copilot flagged: an assistant reply must sit exactly one
    # slot after its own triggering user turn, even under concurrent requests
    # to the same session. Without per-session serialization, another request
    # could append its turns in between and break this.
    for r in results:
        assert r.assistant_turn.sequence_number == r.user_turn.sequence_number + 1

    # Users land on the even slots, assistants on the odd slots — no interleave.
    assert sorted(r.user_turn.sequence_number for r in results) == [0, 2, 4, 6, 8, 10, 12, 14]
    assert sorted(r.assistant_turn.sequence_number for r in results) == [1, 3, 5, 7, 9, 11, 13, 15]
