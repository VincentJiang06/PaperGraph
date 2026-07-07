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
# stub surface (unbuilt commands - replaced with real behavior each milestone)
# ---------------------------------------------------------------------------


def _make_stub(command: str) -> Callable[[], None]:
    def _cmd() -> None:
        _stub(command)

    return _cmd


_STUB_GROUPS: dict[str, list[str]] = {
    "graph": ["list-nodes", "list-edges", "show", "msa-check", "park", "unpark"],
    "expand": ["ingest"],
    "proof": ["build-tasks", "build-task"],
    "docs": ["ingest", "search", "build-pack", "request", "ingest-result"],
    "queue": [
        "list", "claim", "heartbeat", "release", "complete", "fail",
        "expire", "requeue", "events",
    ],
    "validate": ["result", "proposal", "docs-result"],
    "commit": ["apply"],
    "freeze": ["apply", "unfreeze"],
    "compiler": ["dry-run", "draft-map", "ingest-prose"],
    "audit": ["run"],
    "db": ["rebuild", "check"],
    "ui": ["serve"],
}

for _group_name, _commands in _STUB_GROUPS.items():
    _group_app = typer.Typer(no_args_is_help=False)
    for _cname in _commands:
        _group_app.command(_cname)(_make_stub(f"{_group_name} {_cname}"))
    app.add_typer(_group_app, name=_group_name)

# top-level stub commands
app.command("verify")(_make_stub("verify"))
app.command("trace")(_make_stub("trace"))


def main() -> None:
    """Console-script entrypoint (paperproof = paperproof.cli.app:main)."""
    command = typer.main.get_command(app)
    command()
