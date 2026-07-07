"""Read-mostly WebUI over the derived DuckDB index (docs/07 §WebUI, docs/12).

`paperproof ui serve` mounts the FastAPI app in ``app.py``; every read endpoint
goes through the index (``paperproof.db.IndexReader``) so the stale-index banner
is honest. The three write actions (queue claim/release, db rebuild) call the same
code paths as the CLI.
"""
