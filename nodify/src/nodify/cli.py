"""nd — the closed CLI surface (design §5; mirrored bidirectionally by tests).

Every command prints exactly one envelope.v1 JSON object on stdout and appends
exactly one event.v1 to the session trace (read-only commands included; a
failed command logs a FAILED event). Exit codes: 0 ok / 1 domain / 2 usage.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional

import typer

from . import brief as brief_mod
from . import checks, events, export, session as session_mod, store, tree
from .errors import NodifyError, UsageError
from .paths import Paths, paths_for

app = typer.Typer(add_completion=False, no_args_is_help=True)

_ROOT_OPT = typer.Option(None, "--root", help="workspace root (default: . or NODIFY_ROOT)")
_SESSION_OPT = typer.Option(None, "--session", help="session id (or NODIFY_SESSION)")


def _emit(command: str, data: dict[str, Any], *, errors: list[str] | None = None,
          warnings: list[str] | None = None, exit_code: int = 0) -> None:
    envelope = {"schema": "envelope.v1", "ok": not errors, "command": command,
                "data": data, "errors": errors or [], "warnings": warnings or []}
    envelope.pop("schema")  # envelope.v1 keys are pinned; schema field is implicit
    typer.echo(json.dumps(envelope, ensure_ascii=False))
    if exit_code:
        raise typer.Exit(exit_code)


def _run(command: str, root: Optional[str], session_id: Optional[str],
         fn, *, mutating: bool, needs_session: bool = True) -> None:
    """Shared wrapper: resolve paths, load session, run, log event, emit."""
    try:
        paths = paths_for(root, session_id)
        session = session_mod.load(paths) if needs_session else None
        data, touched, summary = fn(paths, session)
    except NodifyError as exc:
        try:
            paths = paths_for(root, session_id)
            if paths.exists():
                events.log(paths, command, mutating=False, touched=[],
                           summary=f"FAILED: {'; '.join(exc.errors)[:200]}")
        except Exception:
            pass
        _emit(command, {}, errors=exc.errors, exit_code=exc.exit_code)
        return
    events.log(paths, command, mutating=mutating, touched=touched, summary=summary)
    _emit(command, data)


@app.command()
def init(session_id: str = typer.Argument(...),
         question: str = typer.Option(..., "--question"),
         boundary: Optional[str] = typer.Option(None, "--boundary"),
         language: str = typer.Option("zh", "--language"),
         budget: list[str] = typer.Option([], "--budget", help="k=v, repeatable"),
         root: Optional[str] = _ROOT_OPT) -> None:
    def go(paths: Paths, _s):
        budgets = {}
        for kv in budget:
            if "=" not in kv:
                raise UsageError([f"--budget expects k=v, got {kv!r}"])
            k, v = kv.split("=", 1)
            budgets[k] = v
        record = session_mod.init(paths, question, boundary_note=boundary,
                                  language=language, budgets=budgets)
        return {"session": record}, [record["session_id"]], f"init: {question[:120]}"
    _run("init", root, session_id, go, mutating=True, needs_session=False)


@app.command()
def add(parent: Optional[str] = typer.Option(None, "--parent"),
        kind: Optional[str] = typer.Option(None, "--kind"),
        statement: Optional[str] = typer.Option(None, "--statement"),
        why: Optional[str] = typer.Option(None, "--why"),
        orientation: Optional[str] = typer.Option(None, "--orientation"),
        note: Optional[str] = typer.Option(None, "--note", help="promotion_note for a claim child"),
        file: Optional[Path] = typer.Option(None, "--file", help="batch expand JSON"),
        root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, sess):
        if file is not None:
            payload = store.read_json(file)
            parent_id = payload.get("parent_id")
            children = payload.get("children", [])
            if not isinstance(children, list) or not children:
                raise UsageError(["--file expects {parent_id, children:[...]} with ≥1 child"])
        else:
            if not statement:
                raise UsageError(["single add needs --statement (or use --file)"])
            parent_id = parent
            children = [{"statement": statement, "why_helps_parent": why,
                         "orientation": orientation,
                         **({"kind": kind} if kind else {}),
                         **({"promotion_note": note} if note else {})}]
        made = tree.add_children(paths, sess, parent_id, children)
        ids = [n["node_id"] for n in made]
        return ({"nodes": made}, ids,
                f"add {len(made)} under {parent_id or 'root'}: {', '.join(ids)}")
    _run("add", root, session, go, mutating=True)


@app.command()
def promote(node_id: str = typer.Argument(...),
            note: str = typer.Option(..., "--note"),
            root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, sess):
        record = tree.promote(paths, sess, node_id, note)
        return {"node": record}, [node_id], f"promote {node_id} -> claim"
    _run("promote", root, session, go, mutating=True)


@app.command("set-status")
def set_status(node_id: str = typer.Argument(...),
               status: str = typer.Argument(...),
               note: Optional[str] = typer.Option(None, "--note"),
               reason: Optional[str] = typer.Option(None, "--reason"),
               root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, _sess):
        record = tree.set_status(paths, node_id, status, note=note, reason=reason)
        return {"node": record}, [node_id], f"{node_id} -> {status}"
    _run("set-status", root, session, go, mutating=True)


@app.command()
def conclude(file: Path = typer.Option(..., "--file"),
             root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, _sess):
        record = tree.conclude(paths, store.read_json(file))
        return ({"synthesis": record}, [record["synthesis_id"], record["node_id"]],
                f"conclude {record['node_id']} [{record['lean']}]")
    _run("conclude", root, session, go, mutating=True)


@app.command()
def brief(max_chars: int = typer.Option(8000, "--max-chars"),
          root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, sess):
        text = brief_mod.render(paths, sess, max_chars=max_chars)
        return {"brief": text}, [], f"brief ({len(text)} chars)"
    _run("brief", root, session, go, mutating=False)


@app.command()
def show(node_id: str = typer.Argument(...),
         root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, _sess):
        from .errors import DomainError
        nodes = tree.nodes_by_id(paths)
        if node_id not in nodes:
            raise DomainError([f"unknown node: {node_id}"])
        return ({"node": nodes[node_id],
                 "path": tree.path_of(nodes, node_id),
                 "children": [c["node_id"] for c in tree.children_of(nodes, node_id)],
                 "synthesis": tree.latest_synthesis(paths, node_id)},
                [], f"show {node_id}")
    _run("show", root, session, go, mutating=False)


@app.command("tree")
def tree_cmd(root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, _sess):
        nodes = tree.nodes_by_id(paths)
        skeleton = [{"node_id": n["node_id"], "parent_id": n["parent_id"],
                     "kind": n["kind"], "status": n["status"],
                     "statement": n["statement"]}
                    for n in sorted(nodes.values(), key=lambda x: x["node_id"])]
        return {"nodes": skeleton}, [], f"tree ({len(skeleton)} nodes)"
    _run("tree", root, session, go, mutating=False)


@app.command("log")
def log_cmd(tail: int = typer.Option(20, "--tail"),
            root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, _sess):
        evs = events.read(paths, tail=tail)
        return {"events": evs}, [], f"log tail={tail}"
    _run("log", root, session, go, mutating=False)


@app.command()
def check(root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, sess):
        hard, soft = checks.run(paths, sess)
        if hard:
            from .errors import DomainError
            raise DomainError([f"HARD: {h}" for h in hard])
        return ({"hard": [], "soft": soft}, [],
                f"check: 0 hard, {len(soft)} soft")
    _run("check", root, session, go, mutating=False)


@app.command("export")
def export_cmd(format: str = typer.Option("json", "--format"),
               root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, sess):
        if format == "json":
            return {"export": export.as_json(paths, sess)}, [], "export json"
        if format == "md":
            return {"export_md": export.as_markdown(paths, sess)}, [], "export md"
        raise UsageError([f"unknown format: {format} (json|md)"])
    _run("export", root, session, go, mutating=False)


def main() -> None:
    try:
        app(standalone_mode=False)
    except typer.Exit as exc:
        sys.exit(exc.exit_code)
    except (typer.Abort, KeyboardInterrupt):
        sys.exit(2)
    except Exception as exc:  # usage errors from typer (bad args) land here
        typer.echo(json.dumps({"ok": False, "command": " ".join(sys.argv[1:2]),
                               "data": {}, "errors": [str(exc)], "warnings": []},
                              ensure_ascii=False))
        sys.exit(2)


if __name__ == "__main__":
    main()
