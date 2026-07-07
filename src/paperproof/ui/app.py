"""FastAPI app for `paperproof ui serve` (docs/07 §WebUI, docs/12).

Read-mostly monitor over the derived DuckDB index. Every GET reads through the
index (honest stale banner, docs/12 P3); the three writes (queue claim/release,
db rebuild) call the same code paths as the CLI (docs/12 P1). The HTTP surface is
CLOSED to exactly the routes docs/07 lists.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from ..db import indexer
from ..db.indexer import IndexReader
from ..errors import CorruptStateError
from ..paths import Paths, paths_for
from ..queue import engine as queue_engine
from . import readmodel

STATIC_DIR = Path(__file__).resolve().parent / "static"


def _ensure_index(paths: Paths) -> None:
    """Build the index if it is missing (rebuild-or-report, docs/12 P3).

    A merely *stale* index is left as-is so the stale banner stays meaningful — we
    never silently rebuild-on-read, which would hide drift. Only a fully absent
    index is materialized so endpoints have data to serve.
    """
    db_path = paths.resolve(indexer.DB_FILE)
    manifest = paths.resolve(indexer.MANIFEST_FILE)
    if not db_path.exists() or not manifest.exists():
        indexer.rebuild(paths)


def create_app(root: str | Path, project: str) -> FastAPI:
    app = FastAPI(title="PaperGraph Monitor", docs_url=None, redoc_url=None, openapi_url=None)

    def _paths() -> Paths:
        return paths_for(root, project)

    def _guarded(fn):
        """Run a read against the index, materializing it first; surface exit-3
        corruption as a locked-banner payload (docs/12 banner priority 1)."""
        paths = _paths()
        try:
            _ensure_index(paths)
            reader = IndexReader(paths.resolve(indexer.DB_FILE))
            try:
                return JSONResponse(fn(reader, paths))
            finally:
                reader.close()
        except CorruptStateError as exc:
            return JSONResponse(
                {"corrupted": True, "errors": exc.errors, "detail": "State corrupted — run `paperproof verify`"},
                status_code=200,
            )

    # --- GET (all JSON) ----------------------------------------------------

    @app.get("/api/overview")
    def api_overview() -> Any:
        return _guarded(lambda r, p: readmodel.overview(r, p))

    @app.get("/api/graph")
    def api_graph(
        lane: Optional[str] = Query(None),
        layer: Optional[int] = Query(None),
        state: Optional[str] = Query(None),
    ) -> Any:
        return _guarded(lambda r, p: readmodel.graph(r, lane, layer, state))

    @app.get("/api/record/{rid}")
    def api_record(rid: str) -> Any:
        return _guarded(lambda r, p: readmodel.record(r, rid))

    @app.get("/api/queue")
    def api_queue(
        queue: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
    ) -> Any:
        return _guarded(lambda r, p: readmodel.queue(r, queue, status))

    @app.get("/api/events")
    def api_events(
        after: Optional[str] = Query(None),
        limit: Optional[int] = Query(None),
    ) -> Any:
        return _guarded(lambda r, p: readmodel.events(r, after, limit))

    @app.get("/api/evidence")
    def api_evidence(q: Optional[str] = Query(None)) -> Any:
        return _guarded(lambda r, p: readmodel.evidence(r, q))

    @app.get("/api/compiler")
    def api_compiler() -> Any:
        return _guarded(lambda r, p: readmodel.compiler(r, p))

    @app.get("/api/trace/{node}")
    def api_trace(node: str) -> Any:
        return _guarded(lambda r, p: readmodel.trace(r, p, node))

    # --- POST (writes: same code paths as the CLI) -------------------------

    @app.post("/api/queue/{wid}/claim")
    def api_claim(wid: str, body: dict[str, Any] | None = None) -> Any:
        paths = _paths()
        agent = (body or {}).get("agent") or "webui"
        try:
            item = queue_engine.get_item(paths, wid)
        except Exception as exc:  # unknown id
            return JSONResponse({"ok": False, "errors": [str(exc)]}, status_code=404)
        try:
            result = queue_engine.claim(paths, queue_name=item["queue_name"], agent=agent, wi_id=wid)
        except Exception as exc:
            return JSONResponse({"ok": False, "errors": [str(exc)]}, status_code=200)
        return JSONResponse({"ok": True, "work_item": result})

    @app.post("/api/queue/{wid}/release")
    def api_release(wid: str) -> Any:
        paths = _paths()
        try:
            result = queue_engine.release(paths, wid)
        except Exception as exc:
            return JSONResponse({"ok": False, "errors": [str(exc)]}, status_code=200)
        return JSONResponse({"ok": True, "work_item": result})

    @app.post("/api/db/rebuild")
    def api_rebuild() -> Any:
        paths = _paths()
        try:
            data = indexer.rebuild(paths)
        except CorruptStateError as exc:
            return JSONResponse({"ok": False, "corrupted": True, "errors": exc.errors}, status_code=200)
        return JSONResponse({"ok": True, "manifest": data})

    # --- static page (mounted last so /api/* wins) -------------------------
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app


def serve(paths: Paths, port: int = 8420) -> dict[str, Any]:
    """Blocking: build the app for one project and run uvicorn (docs/10 §4)."""
    import uvicorn

    app = create_app(paths.root, paths.project_id)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
    return {"served": True, "port": port, "project": paths.project_id}
