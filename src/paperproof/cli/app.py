"""The paperproof CLI (docs/10 §4).

Every command prints exactly ONE JSON envelope {ok, command, data, errors,
warnings} to stdout with the exit-code convention:
  0 ok | 1 domain failure | 2 usage error | 3 corrupt state.

The full closed command surface is registered here. M0 commands (project
init|status, spec build|accept|show) are real; every other command is a stub
that prints {ok:false, errors:["NOT-IMPLEMENTED"]} and exits 1.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any, Callable, Optional

import click
import typer
from typer.core import TyperGroup

from .. import project as project_mod
from ..errors import DomainError, PaperproofError
from ..paths import paths_for
from ..scoping import build as scoping_build

# ---------------------------------------------------------------------------
# Envelope emission
# ---------------------------------------------------------------------------


def _print_envelope(command: str, ok: bool, data: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    env = {
        "ok": ok,
        "command": command,
        "data": data or {},
        "errors": list(errors or []),
        "warnings": list(warnings or []),
    }
    click.echo(json.dumps(env, ensure_ascii=False))


def _emit(
    command: str,
    *,
    data: dict[str, Any] | None = None,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    code: int | None = None,
) -> None:
    ok = not errors
    _print_envelope(command, ok, data or {}, errors or [], warnings or [])
    if code is None:
        code = 0 if ok else 1
    raise typer.Exit(code)


def _dispatch(command: str, fn: Callable[[], dict[str, Any]]) -> None:
    """Run a real command body, converting any outcome into one envelope."""
    try:
        data = fn()
    except typer.Exit:
        raise
    except PaperproofError as exc:
        _emit(command, data=exc.data, errors=exc.errors, warnings=exc.warnings, code=exc.exit_code)
    except Exception as exc:  # pragma: no cover - safety net
        _emit(command, errors=[f"INTERNAL: {type(exc).__name__}: {exc}"], code=1)
    warnings: list[str] = []
    if isinstance(data, dict):
        warnings = data.pop("warnings", []) or []
    _emit(command, data=data if isinstance(data, dict) else {"result": data}, warnings=warnings, code=0)


def _stub(command: str) -> None:
    _emit(command, errors=["NOT-IMPLEMENTED"], code=1)


# ---------------------------------------------------------------------------
# Envelope group: turns usage errors into envelopes too
# ---------------------------------------------------------------------------


def _command_label(raw_args: Any, exc: click.UsageError | None) -> str:
    if exc is not None and getattr(exc, "ctx", None) is not None:
        parts = exc.ctx.command_path.split()
        if len(parts) > 1:
            return " ".join(parts[1:])
    toks: list[str] = []
    skip_value = False
    for tok in list(raw_args or []):
        if skip_value:
            skip_value = False
            continue
        if isinstance(tok, str) and tok.startswith("-"):
            if tok in ("--root", "--project"):
                skip_value = True
            continue
        toks.append(str(tok))
        if len(toks) >= 2:
            break
    return " ".join(toks) if toks else "unknown"


def _exc_message(exc: Exception) -> str:
    fmt = getattr(exc, "format_message", None)
    if callable(fmt):
        return fmt()
    return str(exc)


class EnvelopeGroup(TyperGroup):
    """Root group whose main() renders every failure mode as one JSON envelope.

    Note: typer vendors its own click (``typer._click``); its ``UsageError`` is a
    distinct class from ``click.UsageError``. We classify by MRO class name so
    the handler is robust to whichever click the command tree was built with.
    """

    def main(self, *args: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        kwargs["standalone_mode"] = False
        raw_args = kwargs.get("args")
        if raw_args is None and args:
            raw_args = args[0]
        try:
            rv = super().main(*args, **kwargs)
        except SystemExit:
            raise
        except Exception as exc:
            names = {c.__name__ for c in type(exc).__mro__}
            label = _command_label(raw_args, exc if "UsageError" in names else None)
            if "Abort" in names:
                _print_envelope(label, False, {}, ["ABORTED"], [])
                sys.exit(1)
            if "UsageError" in names:
                _print_envelope(label, False, {}, [f"USAGE: {_exc_message(exc)}"], [])
                sys.exit(2)
            if "ClickException" in names:
                code = getattr(exc, "exit_code", 1)
                _print_envelope(label, False, {}, [f"ERROR: {_exc_message(exc)}"], [])
                sys.exit(code if isinstance(code, int) else 1)
            _print_envelope(
                label, False, {}, [f"INTERNAL: {type(exc).__name__}: {exc}"], []
            )
            sys.exit(1)
        if isinstance(rv, int):
            sys.exit(rv)
        sys.exit(0)


# ---------------------------------------------------------------------------
# App + global options
# ---------------------------------------------------------------------------

app = typer.Typer(
    cls=EnvelopeGroup,
    add_completion=False,
    pretty_exceptions_enable=False,
    no_args_is_help=False,
    help="PaperGraph deterministic core.",
)


@dataclass
class AppState:
    root: str
    project: Optional[str]


@app.callback()
def _root(
    ctx: typer.Context,
    root: str = typer.Option("./data", "--root", help="data root directory"),
    project: Optional[str] = typer.Option(None, "--project", help="project id"),
) -> None:
    import os

    ctx.obj = AppState(root=root, project=project or os.environ.get("PAPERPROOF_PROJECT"))


def _state(ctx: typer.Context) -> AppState:
    import os

    obj = ctx.obj
    if isinstance(obj, AppState):
        return obj
    return AppState(root="./data", project=os.environ.get("PAPERPROOF_PROJECT"))


def _require_project(state: AppState) -> str:
    if not state.project:
        raise DomainError(["no project selected (use --project or PAPERPROOF_PROJECT)"])
    return state.project


# ---------------------------------------------------------------------------
# project (real)
# ---------------------------------------------------------------------------

project_app = typer.Typer(no_args_is_help=False)


@project_app.command("init")
def project_init(ctx: typer.Context, project_id: str = typer.Argument(..., help="project id slug")) -> None:
    state = _state(ctx)
    _dispatch("project init", lambda: project_mod.init(paths_for(state.root, project_id)))


@project_app.command("status")
def project_status(ctx: typer.Context) -> None:
    state = _state(ctx)

    def body() -> dict[str, Any]:
        pid = _require_project(state)
        return project_mod.status(paths_for(state.root, pid))

    _dispatch("project status", body)


app.add_typer(project_app, name="project")


# ---------------------------------------------------------------------------
# spec (real)
# ---------------------------------------------------------------------------

spec_app = typer.Typer(no_args_is_help=False)


def _project_paths(state: AppState):
    pid = _require_project(state)
    paths = paths_for(state.root, pid)
    if not paths.project_dir.exists():
        raise DomainError([f"project not found: {pid}; run project init first"])
    return paths


@spec_app.command("build")
def spec_build(
    ctx: typer.Context,
    topic_file: str = typer.Argument(..., help="topic input markdown file"),
    patch: Optional[str] = typer.Option(None, "--patch", help="RFC 7386 merge patch json"),
) -> None:
    state = _state(ctx)
    _dispatch("spec build", lambda: scoping_build.build(_project_paths(state), topic_file, patch))


@spec_app.command("accept")
def spec_accept(ctx: typer.Context) -> None:
    state = _state(ctx)
    _dispatch("spec accept", lambda: scoping_build.accept(_project_paths(state)))


@spec_app.command("show")
def spec_show(ctx: typer.Context) -> None:
    state = _state(ctx)
    _dispatch("spec show", lambda: scoping_build.show(_project_paths(state)))


app.add_typer(spec_app, name="spec")


# ---------------------------------------------------------------------------
# db (M4): derived DuckDB index — rebuild / check
# ---------------------------------------------------------------------------

from ..db import indexer as _indexer  # noqa: E402

db_app = typer.Typer(no_args_is_help=False)


@db_app.command("rebuild")
def db_rebuild(ctx: typer.Context) -> None:
    s = _state(ctx)
    _dispatch("db rebuild", lambda: _indexer.rebuild(_project_paths(s)))


@db_app.command("check")
def db_check(ctx: typer.Context) -> None:
    s = _state(ctx)
    _dispatch("db check", lambda: _indexer.check(_project_paths(s)))


app.add_typer(db_app, name="db")


# ---------------------------------------------------------------------------
# ui (M4): read-only WebUI over the derived index
# ---------------------------------------------------------------------------

ui_app = typer.Typer(no_args_is_help=False)


@ui_app.command("serve")
def ui_serve(
    ctx: typer.Context,
    port: int = typer.Option(8420, "--port"),
    auto_rebuild: bool = typer.Option(False, "--auto-rebuild"),
) -> None:
    s = _state(ctx)

    def body() -> dict[str, Any]:
        from ..ui import app as ui_module

        return ui_module.serve(_project_paths(s), port, auto_rebuild)

    _dispatch("ui serve", body)


app.add_typer(ui_app, name="ui")

# ---------------------------------------------------------------------------
# M1 real command groups
# ---------------------------------------------------------------------------

from ..committer import apply as _committer  # noqa: E402
from ..docsdb import commands as _docs  # noqa: E402
from ..expander import ingest as _expander  # noqa: E402
from ..graph import commands as _graph  # noqa: E402
from ..prooftask import builder as _prooftask  # noqa: E402
from ..queue import commands as _queue  # noqa: E402
from ..validate import proof as _validate_proof  # noqa: E402
from .. import verify as _verify  # noqa: E402


# --- graph ------------------------------------------------------------------
graph_app = typer.Typer(no_args_is_help=False)


@graph_app.command("list-nodes")
def graph_list_nodes(
    ctx: typer.Context,
    state: Optional[str] = typer.Option(None, "--state"),
    lane: Optional[str] = typer.Option(None, "--lane"),
    layer: Optional[int] = typer.Option(None, "--layer"),
) -> None:
    s = _state(ctx)
    _dispatch("graph list-nodes", lambda: _graph.list_nodes(_project_paths(s), state, lane, layer))


@graph_app.command("list-edges")
def graph_list_edges(
    ctx: typer.Context,
    state: Optional[str] = typer.Option(None, "--state"),
    lane: Optional[str] = typer.Option(None, "--lane"),
    layer: Optional[int] = typer.Option(None, "--layer"),
) -> None:
    s = _state(ctx)
    _dispatch("graph list-edges", lambda: _graph.list_edges(_project_paths(s), state, lane, layer))


@graph_app.command("show")
def graph_show(ctx: typer.Context, target_id: str = typer.Argument(...)) -> None:
    s = _state(ctx)
    _dispatch("graph show", lambda: _graph.show(_project_paths(s), target_id))


@graph_app.command("msa-check")
def graph_msa_check(ctx: typer.Context) -> None:
    s = _state(ctx)

    def body() -> dict[str, Any]:
        data = _graph.msa_check(_project_paths(s))
        if not data["all_pass"]:
            raise DomainError(["MSA incomplete"], data=data)
        return data

    _dispatch("graph msa-check", body)


@graph_app.command("park")
def graph_park(
    ctx: typer.Context,
    target_id: str = typer.Argument(...),
    reason: str = typer.Option(..., "--reason"),
    into: Optional[str] = typer.Option(None, "--into"),
) -> None:
    s = _state(ctx)
    _dispatch("graph park", lambda: _graph.park(_project_paths(s), target_id, reason, into))


@graph_app.command("unpark")
def graph_unpark(ctx: typer.Context, target_id: str = typer.Argument(...)) -> None:
    s = _state(ctx)
    _dispatch("graph unpark", lambda: _graph.unpark(_project_paths(s), target_id))


app.add_typer(graph_app, name="graph")


# --- expand -----------------------------------------------------------------
expand_app = typer.Typer(no_args_is_help=False)


@expand_app.command("ingest")
def expand_ingest(ctx: typer.Context, proposal_file: str = typer.Argument(...)) -> None:
    s = _state(ctx)
    _dispatch("expand ingest", lambda: _expander.ingest(_project_paths(s), proposal_file))


app.add_typer(expand_app, name="expand")


# --- proof ------------------------------------------------------------------
proof_app = typer.Typer(no_args_is_help=False)


@proof_app.command("build-tasks")
def proof_build_tasks(ctx: typer.Context, frontier: bool = typer.Option(False, "--frontier")) -> None:
    s = _state(ctx)
    _dispatch("proof build-tasks", lambda: _prooftask.build_frontier(_project_paths(s)))


@proof_app.command("build-task")
def proof_build_task(ctx: typer.Context, target_id: str = typer.Argument(...)) -> None:
    s = _state(ctx)
    _dispatch("proof build-task", lambda: _prooftask.build_one(_project_paths(s), target_id))


app.add_typer(proof_app, name="proof")


# --- queue ------------------------------------------------------------------
queue_app = typer.Typer(no_args_is_help=False)


@queue_app.command("list")
def queue_list(
    ctx: typer.Context,
    queue: Optional[str] = typer.Option(None, "--queue"),
    status: Optional[str] = typer.Option(None, "--status"),
) -> None:
    s = _state(ctx)
    _dispatch("queue list", lambda: _queue.list_items(_project_paths(s), queue, status))


@queue_app.command("claim")
def queue_claim(
    ctx: typer.Context,
    queue: str = typer.Option(..., "--queue"),
    agent: str = typer.Option(..., "--agent"),
    id: Optional[str] = typer.Option(None, "--id"),
) -> None:
    s = _state(ctx)
    _dispatch("queue claim", lambda: _queue.claim(_project_paths(s), queue, agent, id))


@queue_app.command("heartbeat")
def queue_heartbeat(ctx: typer.Context, wi: str = typer.Argument(...), agent: str = typer.Option(..., "--agent")) -> None:
    s = _state(ctx)
    _dispatch("queue heartbeat", lambda: _queue.heartbeat(_project_paths(s), wi, agent))


@queue_app.command("release")
def queue_release(ctx: typer.Context, wi: str = typer.Argument(...)) -> None:
    s = _state(ctx)
    _dispatch("queue release", lambda: _queue.release(_project_paths(s), wi))


@queue_app.command("complete")
def queue_complete(ctx: typer.Context, wi: str = typer.Argument(...)) -> None:
    s = _state(ctx)
    _dispatch("queue complete", lambda: _queue.complete(_project_paths(s), wi))


@queue_app.command("fail")
def queue_fail(ctx: typer.Context, wi: str = typer.Argument(...), reason: str = typer.Option("manual", "--reason")) -> None:
    s = _state(ctx)
    _dispatch("queue fail", lambda: _queue.fail(_project_paths(s), wi, reason))


@queue_app.command("expire")
def queue_expire(ctx: typer.Context) -> None:
    s = _state(ctx)
    _dispatch("queue expire", lambda: _queue.expire(_project_paths(s)))


@queue_app.command("requeue")
def queue_requeue(ctx: typer.Context, wi: str = typer.Argument(...)) -> None:
    s = _state(ctx)
    _dispatch("queue requeue", lambda: _queue.requeue(_project_paths(s), wi))


@queue_app.command("events")
def queue_events(ctx: typer.Context, after: Optional[str] = typer.Option(None, "--after")) -> None:
    s = _state(ctx)
    _dispatch("queue events", lambda: _queue.events(_project_paths(s), after))


app.add_typer(queue_app, name="queue")


# --- validate ---------------------------------------------------------------
validate_app = typer.Typer(no_args_is_help=False)


@validate_app.command("result")
def validate_result(ctx: typer.Context, file: str = typer.Argument(...), work_item: str = typer.Option(..., "--work-item")) -> None:
    s = _state(ctx)
    _dispatch("validate result", lambda: _validate_proof.validate_result(_project_paths(s), file, work_item))


@validate_app.command("proposal")
def validate_proposal(ctx: typer.Context, file: str = typer.Argument(...)) -> None:
    s = _state(ctx)

    def body() -> dict[str, Any]:
        result = _expander.validate(_project_paths(s), file)
        if not result["ok"]:
            raise DomainError(result["failed_rules"], data=result)
        return result

    _dispatch("validate proposal", body)


@validate_app.command("docs-result")
def validate_docs_result(ctx: typer.Context, file: str = typer.Argument(...), work_item: str = typer.Option(..., "--work-item")) -> None:
    s = _state(ctx)
    _dispatch("validate docs-result", lambda: _docs.validate_docs_result(_project_paths(s), file, work_item))


app.add_typer(validate_app, name="validate")


# --- docs -------------------------------------------------------------------
docs_app = typer.Typer(no_args_is_help=False)


@docs_app.command("ingest")
def docs_ingest(
    ctx: typer.Context,
    file: str = typer.Argument(...),
    source_type: Optional[str] = typer.Option(None, "--source-type"),
    title: Optional[str] = typer.Option(None, "--title"),
    citation_key: Optional[str] = typer.Option(None, "--citation-key"),
) -> None:
    s = _state(ctx)
    _dispatch("docs ingest", lambda: _docs.ingest_file(_project_paths(s), file, source_type, title, citation_key))


@docs_app.command("search")
def docs_search(
    ctx: typer.Context,
    query: str = typer.Option(..., "--query"),
    scope: Optional[str] = typer.Option(None, "--scope"),
) -> None:
    s = _state(ctx)
    _dispatch("docs search", lambda: _docs.search(_project_paths(s), query, scope))


@docs_app.command("build-pack")
def docs_build_pack(ctx: typer.Context, task: str = typer.Option(..., "--task")) -> None:
    s = _state(ctx)
    _dispatch("docs build-pack", lambda: _docs.build_pack(_project_paths(s), task))


@docs_app.command("request")
def docs_request(
    ctx: typer.Context,
    target: str = typer.Option(..., "--target"),
    need: str = typer.Option(..., "--need"),
    hint: list[str] = typer.Option(None, "--hint"),
) -> None:
    s = _state(ctx)
    _dispatch("docs request", lambda: _docs.request(_project_paths(s), target, need, list(hint or [])))


@docs_app.command("ingest-result")
def docs_ingest_result(ctx: typer.Context, file: str = typer.Argument(...), work_item: str = typer.Option(..., "--work-item")) -> None:
    s = _state(ctx)
    _dispatch("docs ingest-result", lambda: _docs.ingest_result(_project_paths(s), file, work_item))


@docs_app.command("plan")
def docs_plan(ctx: typer.Context, request: str = typer.Option(..., "--request")) -> None:
    s = _state(ctx)
    _dispatch("docs plan", lambda: _docs.plan(_project_paths(s), request))


@docs_app.command("wave")
def docs_wave(
    ctx: typer.Context,
    request: str = typer.Option(..., "--request"),
    fan: bool = typer.Option(False, "--fan"),
) -> None:
    s = _state(ctx)
    _dispatch("docs wave", lambda: _docs.wave(_project_paths(s), request, fan))


@docs_app.command("coverage")
def docs_coverage(
    ctx: typer.Context,
    node: Optional[str] = typer.Option(None, "--node"),
) -> None:
    """The DERIVED coverage ledger (S4, docs/17): saturation + role-profile floor
    per non-rejected fact/mechanism node (and per bridge)."""
    s = _state(ctx)
    _dispatch("docs coverage", lambda: _docs.coverage(_project_paths(s), node))


# docs source (S3 Stage A-lite, docs/16): the source registry curation surface.
docs_source_app = typer.Typer(no_args_is_help=False)


@docs_source_app.command("list")
def docs_source_list(ctx: typer.Context) -> None:
    s = _state(ctx)
    _dispatch("docs source list", lambda: _docs.source_list(_project_paths(s)))


@docs_source_app.command("set")
def docs_source_set(
    ctx: typer.Context,
    domain: str = typer.Option(..., "--domain"),
    tier: Optional[str] = typer.Option(None, "--tier"),
    publisher: Optional[str] = typer.Option(None, "--publisher"),
    workaround: Optional[str] = typer.Option(None, "--workaround"),
    note: Optional[str] = typer.Option(None, "--note"),
    blocked: Optional[bool] = typer.Option(None, "--blocked/--no-blocked"),
) -> None:
    s = _state(ctx)
    _dispatch(
        "docs source set",
        lambda: _docs.source_set(_project_paths(s), domain, tier, publisher, workaround, note, blocked),
    )


docs_app.add_typer(docs_source_app, name="source")


app.add_typer(docs_app, name="docs")


# --- commit -----------------------------------------------------------------
commit_app = typer.Typer(no_args_is_help=False)


@commit_app.command("apply")
def commit_apply(ctx: typer.Context, result: str = typer.Option(..., "--result")) -> None:
    s = _state(ctx)
    _dispatch("commit apply", lambda: _committer.apply_proof_verdict(_project_paths(s), result))


app.add_typer(commit_app, name="commit")


# --- freeze (M3) ------------------------------------------------------------
from ..freeze import apply as _freeze  # noqa: E402
from ..compiler import draft_map as _draft_map  # noqa: E402
from ..compiler import dry_run as _dry_run  # noqa: E402
from ..compiler import prose as _prose  # noqa: E402
from ..audit import run as _audit  # noqa: E402
from ..graph import trace as _trace  # noqa: E402

freeze_app = typer.Typer(no_args_is_help=False)


@freeze_app.command("apply")
def freeze_apply(
    ctx: typer.Context,
    target: str = typer.Option(..., "--target"),
    level: str = typer.Option(..., "--level"),
) -> None:
    s = _state(ctx)
    _dispatch("freeze apply", lambda: _freeze.apply(_project_paths(s), target, level))


@freeze_app.command("unfreeze")
def freeze_unfreeze(ctx: typer.Context, target: str = typer.Option(..., "--target")) -> None:
    s = _state(ctx)
    _dispatch("freeze unfreeze", lambda: _freeze.unfreeze(_project_paths(s), target))


app.add_typer(freeze_app, name="freeze")


# --- compiler (M3) ----------------------------------------------------------
compiler_app = typer.Typer(no_args_is_help=False)


@compiler_app.command("dry-run")
def compiler_dry_run(ctx: typer.Context) -> None:
    s = _state(ctx)
    _dispatch("compiler dry-run", lambda: _dry_run.dry_run(_project_paths(s)))


@compiler_app.command("draft-map")
def compiler_draft_map(ctx: typer.Context) -> None:
    s = _state(ctx)
    _dispatch("compiler draft-map", lambda: _draft_map.draft_map(_project_paths(s)))


@compiler_app.command("ingest-prose")
def compiler_ingest_prose(
    ctx: typer.Context,
    file: str = typer.Argument(...),
    work_item: str = typer.Option(..., "--work-item"),
) -> None:
    s = _state(ctx)
    _dispatch("compiler ingest-prose", lambda: _prose.ingest_prose(_project_paths(s), file, work_item))


app.add_typer(compiler_app, name="compiler")


# --- audit (M3) -------------------------------------------------------------
audit_app = typer.Typer(no_args_is_help=False)


@audit_app.command("run")
def audit_run(ctx: typer.Context, draft: str = typer.Option(..., "--draft")) -> None:
    s = _state(ctx)

    def body() -> dict[str, Any]:
        report = _audit.run(_project_paths(s), draft)
        if not report["passed"]:
            raise DomainError(["audit findings present"], data=report)
        return report

    _dispatch("audit run", body)


app.add_typer(audit_app, name="audit")


# --- trace (M3) -------------------------------------------------------------
@app.command("trace")
def trace_cmd(ctx: typer.Context, node: str = typer.Option(..., "--node")) -> None:
    s = _state(ctx)
    _dispatch("trace", lambda: _trace.trace_node(_project_paths(s), node))


# --- verify -----------------------------------------------------------------
@app.command("verify")
def verify_cmd(ctx: typer.Context) -> None:
    s = _state(ctx)
    _dispatch("verify", lambda: _verify.run(_project_paths(s)))


def main() -> None:
    """Console-script entrypoint (paperproof = paperproof.cli.app:main)."""
    command = typer.main.get_command(app)
    command()
