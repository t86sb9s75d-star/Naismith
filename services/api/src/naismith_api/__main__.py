"""Console entry point: `naismith-api` runs the dev server via uvicorn."""

from __future__ import annotations

import os


def main() -> None:
    import uvicorn

    uvicorn.run(
        "naismith_api.main:app",
        host=os.environ.get("NAISMITH_HOST", "127.0.0.1"),
        port=int(os.environ.get("NAISMITH_PORT", "8000")),
        reload=os.environ.get("NAISMITH_RELOAD", "false").lower() == "true",
    )


if __name__ == "__main__":
    main()
