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
        result = fn(paths, session)
        data, touched, summary = result[:3]
        warnings = list(result[3]) if len(result) > 3 else []
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
    _emit(command, data, warnings=warnings)


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
        return ({"session": record,
                 "session_dir": str(paths.session_dir),
                 "notes_dir": str(paths.resolve("notes"))},
                [record["session_id"]], f"init: {question[:120]}")
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
    def go(paths: Paths, sess):
        record, warns = tree.conclude(paths, sess, store.read_json(file))
        return ({"synthesis": record}, [record["synthesis_id"], record["node_id"]],
                f"conclude {record['node_id']} [{record['lean']}]", warns)
    _run("conclude", root, session, go, mutating=True)


@app.command()
def brief(max_chars: int = typer.Option(8000, "--max-chars"),
          root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, sess):
        text = brief_mod.render(paths, sess, max_chars=max_chars)
        return ({"brief": text, "session_dir": str(paths.session_dir)},
                [], f"brief ({len(text)} chars)")
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


@app.command()
def upgrade(root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, sess):
        from .session import set_name
        before = set_name(sess)
        record = session_mod.upgrade(paths)
        after = set_name(record)
        return ({"session": record, "from": before, "to": after}, [],
                f"upgrade schema set {before} -> {after}")
    _run("upgrade", root, session, go, mutating=True)


@app.command()
def recall(node: str = typer.Option(..., "--node"),
           query: str = typer.Option(..., "--query"),
           k: int = typer.Option(8, "--k"),
           root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, sess):
        from . import docsdb
        session_mod.require_set(sess, "v2")
        result = docsdb.recall(paths, node, query, k=k)
        return ({"recall": result}, [],
                f"recall {node}: {len(result['hits'])} hits")
    _run("recall", root, session, go, mutating=False)


docs_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(docs_app, name="docs")


@docs_app.command("ingest")
def docs_ingest(file: Path = typer.Option(..., "--file"),
                root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, sess):
        from . import docsdb
        session_mod.require_set(sess, "v2")
        entry, warns = docsdb.ingest(paths, store.read_json(file))
        return ({"entry": entry}, [entry["doc_id"]],
                f"ingest {entry['doc_id']}: {entry['title'][:80]}", warns)
    _run("docs ingest", root, session, go, mutating=True)


@docs_app.command("for-node")
def docs_for_node(node_id: str = typer.Argument(...),
                  all: bool = typer.Option(False, "--all", help="ignore ancestors filter: list every entry"),
                  root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, sess):
        from . import docsdb
        session_mod.require_set(sess, "v2")
        if all:
            entries = [docsdb.entries_by_id(paths)[k]
                       for k in sorted(docsdb.entries_by_id(paths))]
        else:
            entries = docsdb.for_node(paths, node_id)
        return ({"entries": entries}, [], f"docs for-node {node_id}: {len(entries)}")
    _run("docs for-node", root, session, go, mutating=False)


_PAYLOAD_EXAMPLES = {
    "conclude": {
        "_for": "nd conclude --file <this>",
        "node_id": "N-0002", "lean": "supports", "summary": "一句话结论",
        "confidence": "medium",
        "based_on": {"children": [], "evidence": [
            {"title": "来源标题", "doc_id": "DOC-0001",
             "quote": "从归档文本原样复制的句子(或 null)",
             "url": None, "locator": None, "tool": "web_search", "note": None}]},
        "open_questions": []},
    "ingest": {
        "_for": "nd docs ingest --file <this>",
        "kind": "web", "title": "来源标题", "url": "https://…",
        "text_file": "notes/saved.txt  (session-relative, or absolute)",
        "summary": "≤500字符摘要",
        "bindings": [{"node_id": "N-0002", "relation": "supports",
                       "note": None}]},
    "outline": {
        "_for": "nd article outline --file <this>",
        "title": "文章标题", "thesis": "论题(须扎根 grounded_in 的 synthesis)",
        "grounded_in": ["SYN-0001"],
        "sections": [{"section_id": "S-01", "title": "引言",
                       "role": "introduction", "node_ids": ["N-0001"],
                       "intent": "一句话意图"}],
        "excluded": [{"node_id": "N-0005", "reason": "为何不入文"}]},
    "expand": {
        "_for": "nd add --file <this>",
        "parent_id": "N-0001",
        "children": [{"statement": "新方向子观点",
                       "why_helps_parent": "为何有助判断父观点",
                       "orientation": "adversarial"}]},
}
_SCHEMA_ALIASES = {"conclude": "synthesis.v2", "ingest": "docs.entry.v1",
                   "outline": "article.outline.v1", "expand": "node.v1"}


@app.command("schema")
def schema_cmd(name: str = typer.Argument(..., help="record name or alias: "
               "conclude|ingest|outline|expand|<schema file name>"),
               root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    from .schemas import SCHEMA_NAMES, load as load_schema
    resolved = _SCHEMA_ALIASES.get(name, name)
    if resolved not in SCHEMA_NAMES:
        _emit("schema", {}, errors=[f"unknown schema: {name!r} (aliases: "
              f"{sorted(_SCHEMA_ALIASES)}; records: {list(SCHEMA_NAMES)})"],
              exit_code=2)
        return
    data = {"name": resolved, "schema": load_schema(resolved)}
    if name in _PAYLOAD_EXAMPLES:
        data["payload_example"] = _PAYLOAD_EXAMPLES[name]
    _emit("schema", data)


article_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(article_app, name="article")


@article_app.command("outline")
def article_outline(file: Path = typer.Option(..., "--file"),
                    root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, sess):
        from . import article
        session_mod.require_set(sess, "v3")
        had = article.latest_outline(paths) is not None
        record = article.set_outline(paths, store.read_json(file))
        warns = ["OL-01 revised in place (append-only; latest record wins)"] if had else []
        return ({"outline": record, "revised": had}, [record["outline_id"]],
                f"outline: {record['title'][:80]} ({len(record['sections'])} sections)",
                warns)
    _run("article outline", root, session, go, mutating=True)


@article_app.command("section")
def article_section(id: str = typer.Option(..., "--id"),
                    file: Path = typer.Option(..., "--file"),
                    root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, sess):
        from . import article
        session_mod.require_set(sess, "v3")
        record, warns = article.register_section(paths, id, file)
        return ({"section": record}, [id],
                f"section {id}: {record['word_count']} words, "
                f"{len(record['cites'])} cites", warns)
    _run("article section", root, session, go, mutating=True)


@article_app.command("show")
def article_show(root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, sess):
        from . import article
        session_mod.require_set(sess, "v3")
        outline = article.latest_outline(paths)
        sections = article.latest_sections(paths)
        final = paths.resolve("article/final.md")
        return ({"outline": outline,
                 "sections": [sections[k] for k in sorted(sections)],
                 "final_md": str(final) if final.is_file() else None},
                [], f"article show: outline={'yes' if outline else 'no'}, "
                    f"{len(sections)} sections")
    _run("article show", root, session, go, mutating=False)


@article_app.command("assemble")
def article_assemble(root: Optional[str] = _ROOT_OPT, session: Optional[str] = _SESSION_OPT) -> None:
    def go(paths: Paths, sess):
        from . import article
        session_mod.require_set(sess, "v3")
        data, warns = article.assemble(paths)
        return (data, [], f"assemble -> {data['file']}", warns)
    _run("article assemble", root, session, go, mutating=True)


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
