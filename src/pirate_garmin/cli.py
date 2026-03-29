from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from pirate_garmin import __version__
from pirate_garmin.auth import GarminAuthError, MissingCredentialsError
from pirate_garmin.client import GarminClient
from pirate_garmin.endpoints import ENDPOINTS, parse_kv_pairs, render_endpoint, resolve_endpoint

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Thin Garmin Connect CLI built around Garmin's native Android auth flow.",
)


class HostChoice(StrEnum):
    connectapi = "connectapi"
    services = "services"


def _client(username: str | None, password: str | None, app_dir: Path | None) -> GarminClient:
    return GarminClient.from_credentials(
        username=username,
        password=password,
        app_dir=str(app_dir) if app_dir else None,
    )


def _emit_json(payload: object) -> None:
    typer.echo(json.dumps(payload, indent=2))


@app.command("version")
def version() -> None:
    _emit_json({"version": __version__})


@app.command("login")
def login(
    username: Annotated[
        str | None,
        typer.Option("--username", envvar="GARMIN_USERNAME", help="Garmin username / email"),
    ] = None,
    password: Annotated[
        str | None,
        typer.Option(
            "--password", envvar="GARMIN_PASSWORD", help="Garmin password", hide_input=True
        ),
    ] = None,
    app_dir: Annotated[
        Path | None,
        typer.Option("--app-dir", help="Directory for cached Garmin auth files"),
    ] = None,
) -> None:
    client = _client(username, password, app_dir)
    session = client.auth.ensure_authenticated()
    bundle = client.auth.fetch_profile_bundle(session)
    _emit_json(
        {
            "tokenPath": str(client.auth.native_oauth2_path),
            "profilePath": str(client.auth.profile_path),
            "auth": session.to_dict(),
            "profile": bundle.social_profile,
            "settings": bundle.settings,
        }
    )


@app.command("whoami")
def whoami(
    username: Annotated[
        str | None,
        typer.Option("--username", envvar="GARMIN_USERNAME", help="Garmin username / email"),
    ] = None,
    password: Annotated[
        str | None,
        typer.Option(
            "--password", envvar="GARMIN_PASSWORD", help="Garmin password", hide_input=True
        ),
    ] = None,
    app_dir: Annotated[
        Path | None,
        typer.Option("--app-dir", help="Directory for cached Garmin auth files"),
    ] = None,
) -> None:
    client = _client(username, password, app_dir)
    _emit_json(client.whoami())


@app.command("profile")
def profile(
    username: Annotated[
        str | None,
        typer.Option("--username", envvar="GARMIN_USERNAME", help="Garmin username / email"),
    ] = None,
    password: Annotated[
        str | None,
        typer.Option(
            "--password", envvar="GARMIN_PASSWORD", help="Garmin password", hide_input=True
        ),
    ] = None,
    app_dir: Annotated[
        Path | None,
        typer.Option("--app-dir", help="Directory for cached Garmin auth files"),
    ] = None,
) -> None:
    client = _client(username, password, app_dir)
    _emit_json(client.get_profile_bundle())


@app.command("endpoints")
def endpoints(
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
) -> None:
    payload = [
        {
            "key": endpoint.key,
            "host": endpoint.host,
            "path": endpoint.path,
            "description": endpoint.description,
            "defaults": endpoint.defaults,
            "placeholders": endpoint.placeholders,
        }
        for endpoint in ENDPOINTS
    ]
    if json_output:
        _emit_json(payload)
        return
    for item in payload:
        defaults = (
            " " + ", ".join(f"{key}={value}" for key, value in item["defaults"].items())
            if item["defaults"]
            else ""
        )
        placeholders = (
            " placeholders=" + ",".join(item["placeholders"]) if item["placeholders"] else ""
        )
        typer.echo(f"{item['key']}: {item['path']}{placeholders}{defaults}")
        typer.echo(f"  {item['description']}")


@app.command("get")
def get_endpoint(
    endpoint_key: Annotated[
        str, typer.Argument(help="Endpoint key from `pirate-garmin endpoints`")
    ],
    path: Annotated[
        list[str] | None,
        typer.Option("--path", help="Path placeholder value as key=value. Repeatable."),
    ] = None,
    query: Annotated[
        list[str] | None,
        typer.Option("--query", help="Query parameter as key=value. Repeatable."),
    ] = None,
    username: Annotated[
        str | None,
        typer.Option("--username", envvar="GARMIN_USERNAME", help="Garmin username / email"),
    ] = None,
    password: Annotated[
        str | None,
        typer.Option(
            "--password", envvar="GARMIN_PASSWORD", help="Garmin password", hide_input=True
        ),
    ] = None,
    app_dir: Annotated[
        Path | None,
        typer.Option("--app-dir", help="Directory for cached Garmin auth files"),
    ] = None,
) -> None:
    client = _client(username, password, app_dir)
    endpoint = resolve_endpoint(endpoint_key)
    profile_bundle = client.auth.ensure_profile_bundle()
    rendered_path, params = render_endpoint(
        endpoint,
        parse_kv_pairs(path or []),
        parse_kv_pairs(query or []),
        profile_bundle,
    )
    _emit_json(client.request_json(endpoint.host, rendered_path, params))


@app.command("raw")
def raw(
    path: Annotated[
        str,
        typer.Argument(help="Absolute Garmin API path, e.g. /sleep-service/sleep/dailySleepData"),
    ],
    host: Annotated[
        HostChoice,
        typer.Option("--host", help="Host family to use"),
    ] = HostChoice.connectapi,
    query: Annotated[
        list[str] | None,
        typer.Option("--query", help="Query parameter as key=value. Repeatable."),
    ] = None,
    username: Annotated[
        str | None,
        typer.Option("--username", envvar="GARMIN_USERNAME", help="Garmin username / email"),
    ] = None,
    password: Annotated[
        str | None,
        typer.Option(
            "--password", envvar="GARMIN_PASSWORD", help="Garmin password", hide_input=True
        ),
    ] = None,
    app_dir: Annotated[
        Path | None,
        typer.Option("--app-dir", help="Directory for cached Garmin auth files"),
    ] = None,
) -> None:
    client = _client(username, password, app_dir)
    _emit_json(client.request_json(host.value, path, parse_kv_pairs(query or [])))


def _exit_with_message(message: str) -> None:
    typer.echo(message, err=True)
    raise typer.Exit(code=1)


def main() -> None:
    try:
        app()
    except MissingCredentialsError as exc:
        _exit_with_message(str(exc))
    except GarminAuthError as exc:
        _exit_with_message(str(exc))
    except ValueError as exc:
        _exit_with_message(str(exc))


if __name__ == "__main__":
    main()
