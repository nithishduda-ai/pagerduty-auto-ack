#!/usr/bin/env python3
"""Acknowledge triggered PagerDuty incidents only while a user is on call."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any


API_BASE_URL = "https://api.pagerduty.com"
ACCEPT_HEADER = "application/vnd.pagerduty+json;version=2"
VERSION = "0.5.0"
USER_AGENT = f"pagerduty-oncall-ack/{VERSION}"
COMMANDS = {"init", "run", "check", "doctor", "tui"}
OPEN_INCIDENT_STATUSES = ("triggered", "acknowledged")
ENV_TEMPLATE = """# PagerDuty On-Call Ack configuration
# Keep this file private. It contains a PagerDuty API token.

# Required. Use a PagerDuty REST API token.
PD_API_TOKEN=REPLACE_WITH_PAGERDUTY_TOKEN

# Optional but recommended. If omitted, the CLI will try to infer these from /users/me.
PD_USER_ID=PAGERDUTY_USER_ID
PD_FROM_EMAIL=you@example.com

# Safe default. Keep false until dry-run output looks right.
PD_APPLY=false
PD_POLL_SECONDS=30

# Optional comma-separated safety filters.
PD_SERVICE_IDS=
PD_TEAM_IDS=
PD_ESCALATION_POLICY_IDS=
PD_SCHEDULE_IDS=

# Optional tuning.
PD_REQUEST_TIMEOUT_SECONDS=20
PD_MAX_PAGES=10
"""


class ConfigError(Exception):
    pass


class PagerDutyAPIError(Exception):
    def __init__(self, method: str, url: str, status: int, body: str) -> None:
        self.method = method
        self.url = url
        self.status = status
        self.body = body
        super().__init__(f"{method} {url} failed with HTTP {status}: {body}")


@dataclasses.dataclass(frozen=True)
class Config:
    api_base_url: str
    auth_header: str
    user_id: str | None
    from_email: str | None
    apply: bool
    interval_seconds: int
    request_timeout_seconds: int
    max_pages: int
    service_ids: list[str]
    team_ids: list[str]
    escalation_policy_ids: list[str]
    schedule_ids: list[str]
    quiet: bool


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_pd_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_pd_time(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def log(config: Config, message: str) -> None:
    if not config.quiet:
        timestamp = format_pd_time(utc_now())
        print(f"{timestamp} {message}", flush=True)


def load_env_file(path: str | None) -> None:
    if not path or not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for line_number, raw_line in enumerate(env_file, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise ConfigError(f"{path}:{line_number} is not KEY=VALUE")

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def create_env_file(path: str, *, force: bool = False) -> str:
    expanded_path = os.path.expanduser(path)
    if os.path.exists(expanded_path) and not force:
        raise ConfigError(f"{expanded_path} already exists. Pass --force to overwrite it.")

    directory = os.path.dirname(expanded_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(expanded_path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as env_file:
        env_file.write(ENV_TEMPLATE)
    try:
        os.chmod(expanded_path, 0o600)
    except OSError:
        pass
    return expanded_path


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def none_if_placeholder(value: str | None, placeholders: set[str]) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped or stripped in placeholders:
        return None
    return stripped


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc


def build_auth_header(token: str | None) -> str:
    token = none_if_placeholder(token, {"REPLACE_WITH_PAGERDUTY_TOKEN"})
    if not token:
        raise ConfigError("Set PD_API_TOKEN or pass a token through your environment.")

    if token.startswith("Token token=") or token.startswith("Bearer "):
        return token
    return f"Token token={token}"


def compact_params(params: dict[str, Any]) -> dict[str, Any]:
    compacted: dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, list) and not value:
            continue
        compacted[key] = value
    return compacted


class PagerDutyClient:
    def __init__(self, config: Config) -> None:
        self.config = config

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        include_from_header: bool = False,
    ) -> dict[str, Any]:
        base_url = self.config.api_base_url.rstrip("/")
        url = f"{base_url}{path}"
        query = urllib.parse.urlencode(compact_params(params or {}), doseq=True)
        if query:
            url = f"{url}?{query}"

        headers = {
            "Accept": ACCEPT_HEADER,
            "Authorization": self.config.auth_header,
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }
        if include_from_header:
            if not self.config.from_email:
                raise ConfigError("PD_FROM_EMAIL is required when acknowledging incidents.")
            headers["From"] = self.config.from_email

        encoded_body = None
        if body is not None:
            encoded_body = json.dumps(body).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=encoded_body,
            headers=headers,
            method=method,
        )

        for attempt in range(4):
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=self.config.request_timeout_seconds,
                ) as response:
                    raw = response.read()
                    if not raw:
                        return {}
                    return json.loads(raw.decode("utf-8"))
            except urllib.error.HTTPError as exc:
                raw_body = exc.read().decode("utf-8", errors="replace")
                if exc.code in {429, 500, 502, 503, 504} and attempt < 3:
                    retry_after = exc.headers.get("Retry-After")
                    delay = int(retry_after) if retry_after and retry_after.isdigit() else 2**attempt
                    time.sleep(max(delay, 1))
                    continue
                raise PagerDutyAPIError(method, url, exc.code, raw_body) from exc
            except urllib.error.URLError as exc:
                if attempt < 3:
                    time.sleep(2**attempt)
                    continue
                raise ConfigError(f"Network error calling PagerDuty: {exc}") from exc

        raise ConfigError("PagerDuty request retry loop exited unexpectedly.")

    def paginate(
        self,
        path: str,
        collection_key: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        offset = 0
        pages = 0

        while True:
            page_params = dict(params or {})
            page_params["limit"] = 100
            page_params["offset"] = offset

            payload = self.request("GET", path, params=page_params)
            page_items = payload.get(collection_key, [])
            if not isinstance(page_items, list):
                raise ConfigError(f"PagerDuty response did not contain a list at {collection_key}.")

            items.extend(page_items)
            pages += 1
            if not payload.get("more"):
                break
            if pages >= self.config.max_pages:
                raise ConfigError(
                    f"Stopped after {self.config.max_pages} pages from {path}; "
                    "increase PD_MAX_PAGES if this account legitimately returns more."
                )

            offset += len(page_items) or 100

        return items

    def get_current_user(self) -> dict[str, Any]:
        payload = self.request("GET", "/users/me")
        user = payload.get("user")
        if not isinstance(user, dict):
            raise ConfigError("PagerDuty /users/me response did not include a user object.")
        return user

    def test_ability(self, ability: str) -> bool:
        self.request("GET", f"/abilities/{urllib.parse.quote(ability)}")
        return True

    def acknowledge_incident(self, incident_id: str) -> dict[str, Any]:
        return self.request(
            "PUT",
            f"/incidents/{urllib.parse.quote(incident_id)}",
            body={"incident": {"type": "incident_reference", "status": "acknowledged"}},
            include_from_header=True,
        )


def resolve_identity(config: Config) -> Config:
    if config.user_id and config.from_email:
        return config

    client = PagerDutyClient(config)
    try:
        user = client.get_current_user()
    except Exception as exc:
        missing = []
        if not config.user_id:
            missing.append("PD_USER_ID")
        if not config.from_email:
            missing.append("PD_FROM_EMAIL")
        raise ConfigError(
            f"Could not infer {', '.join(missing)} from /users/me; set them explicitly."
        ) from exc

    return dataclasses.replace(
        config,
        user_id=config.user_id or user.get("id"),
        from_email=config.from_email or user.get("email"),
    )


def oncall_is_active_for_user(oncall: dict[str, Any], user_id: str, now: datetime) -> bool:
    user = oncall.get("user") or {}
    if user.get("id") != user_id:
        return False

    start = parse_pd_time(oncall.get("start"))
    end = parse_pd_time(oncall.get("end"))
    if start and now < start:
        return False
    if end and now >= end:
        return False
    return True


def list_active_oncalls(client: PagerDutyClient, config: Config, now: datetime) -> list[dict[str, Any]]:
    if not config.user_id:
        raise ConfigError("PD_USER_ID is required.")

    params = {
        "user_ids[]": [config.user_id],
        "since": format_pd_time(now - timedelta(seconds=1)),
        "until": format_pd_time(now + timedelta(seconds=1)),
        "earliest": "true",
        "escalation_policy_ids[]": config.escalation_policy_ids,
        "schedule_ids[]": config.schedule_ids,
    }

    oncalls = client.paginate("/oncalls", "oncalls", params=params)
    return [
        oncall
        for oncall in oncalls
        if oncall_is_active_for_user(oncall, config.user_id, now)
    ]


def incident_is_assigned_to_user(incident: dict[str, Any], user_id: str) -> bool:
    assignments = incident.get("assignments")
    if not isinstance(assignments, list) or not assignments:
        # The API query already filters by assigned user. If assignments are omitted
        # from a response variant, trust the server-side filter.
        return True

    for assignment in assignments:
        assignee = assignment.get("assignee") or {}
        if assignee.get("id") == user_id:
            return True
    return False


def list_incidents(
    client: PagerDutyClient,
    config: Config,
    *,
    statuses: tuple[str, ...],
) -> list[dict[str, Any]]:
    if not config.user_id:
        raise ConfigError("PD_USER_ID is required.")

    params = {
        "statuses[]": list(statuses),
        "user_ids[]": [config.user_id],
        "service_ids[]": config.service_ids,
        "team_ids[]": config.team_ids,
    }
    incidents = client.paginate("/incidents", "incidents", params=params)
    allowed_statuses = set(statuses)
    return [
        incident
        for incident in incidents
        if incident.get("status") in allowed_statuses
        and incident_is_assigned_to_user(incident, config.user_id)
    ]


def list_open_incidents(client: PagerDutyClient, config: Config) -> list[dict[str, Any]]:
    return list_incidents(client, config, statuses=OPEN_INCIDENT_STATUSES)


def list_triggered_incidents(client: PagerDutyClient, config: Config) -> list[dict[str, Any]]:
    return list_incidents(client, config, statuses=("triggered",))


def filter_triggered_incidents(incidents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [incident for incident in incidents if incident.get("status") == "triggered"]


def describe_oncall(oncall: dict[str, Any]) -> str:
    policy = (oncall.get("escalation_policy") or {}).get("summary")
    schedule = (oncall.get("schedule") or {}).get("summary")
    level = oncall.get("escalation_level")
    parts = [part for part in [policy, schedule, f"level {level}" if level else None] if part]
    return " / ".join(parts) if parts else oncall.get("id", "unknown on-call")


def describe_incident(
    incident: dict[str, Any],
    *,
    include_status: bool = False,
    include_url: bool = False,
) -> str:
    number = incident.get("incident_number")
    title = incident.get("title") or incident.get("summary") or "untitled"
    incident_id = incident.get("id", "unknown")
    if number:
        description = f"#{number} {title} ({incident_id})"
    else:
        description = f"{title} ({incident_id})"

    status = incident.get("status")
    if include_status and status:
        description = f"{description} [{status}]"

    url = incident.get("html_url")
    if include_url and url:
        description = f"{description} {url}"

    return description


def log_incidents(config: Config, heading: str, incidents: list[dict[str, Any]]) -> None:
    log(config, f"{heading}: {len(incidents)}")
    for incident in incidents:
        log(config, f"- {describe_incident(incident, include_status=True, include_url=True)}")


def print_incidents(heading: str, incidents: list[dict[str, Any]]) -> None:
    print(f"{heading}: {len(incidents)}")
    for incident in incidents:
        print(f"- {describe_incident(incident, include_status=True, include_url=True)}")


def print_triggered_summary(incidents: list[dict[str, Any]]) -> None:
    print(f"Triggered incidents eligible for acknowledgement: {len(incidents)}")
    for incident in incidents:
        print(f"- {describe_incident(incident, include_status=True, include_url=True)}")


def log_triggered_summary(config: Config, incidents: list[dict[str, Any]]) -> None:
    log(config, f"Triggered incidents eligible for acknowledgement: {len(incidents)}")
    for incident in incidents:
        log(config, f"- {describe_incident(incident, include_status=True, include_url=True)}")


def run_once(client: PagerDutyClient, config: Config) -> int:
    now = utc_now()
    active_oncalls = list_active_oncalls(client, config, now)
    if not active_oncalls:
        log(config, "User is not currently on call; skipping incident lookup.")
        return 0

    oncall_summary = "; ".join(describe_oncall(oncall) for oncall in active_oncalls)
    log(config, f"User is on call: {oncall_summary}")

    open_incidents = list_open_incidents(client, config)
    log_incidents(config, "Open incidents assigned to user", open_incidents)

    triggered_incidents = filter_triggered_incidents(open_incidents)
    if not triggered_incidents:
        log(config, "No triggered incidents eligible for acknowledgement.")
        return 0

    acknowledged = 0
    log_triggered_summary(config, triggered_incidents)
    for incident in triggered_incidents:
        incident_id = incident.get("id")
        if not incident_id:
            log(config, f"Skipping incident without an id: {incident}")
            continue

        description = describe_incident(incident)
        if config.apply:
            client.acknowledge_incident(incident_id)
            log(config, f"Acknowledged {description}")
        else:
            log(config, f"[dry-run] Would acknowledge {description}")
        acknowledged += 1

    return acknowledged


def normalize_argv(argv: list[str]) -> list[str]:
    if not argv:
        return ["run"]
    if argv[0] in COMMANDS or argv[0] in {"-h", "--help", "--version"}:
        return argv
    return ["run", *argv]


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--env-file", default=os.getenv("PD_ENV_FILE", ".env"))
    parser.add_argument("--timeout", type=int, default=env_int("PD_REQUEST_TIMEOUT_SECONDS", 20), help="PagerDuty request timeout in seconds.")
    parser.add_argument("--max-pages", type=int, default=env_int("PD_MAX_PAGES", 10), help="Maximum paginated pages per API list request.")
    parser.add_argument("--user-id", default=none_if_placeholder(os.getenv("PD_USER_ID"), {"PAGERDUTY_USER_ID"}), help="PagerDuty user ID to check for on-call status.")
    parser.add_argument("--from-email", default=none_if_placeholder(os.getenv("PD_FROM_EMAIL"), {"you@example.com"}), help="Valid PagerDuty user email for the required From header.")
    parser.add_argument("--api-base-url", default=os.getenv("PD_API_BASE_URL", API_BASE_URL), help="PagerDuty REST API base URL.")
    parser.add_argument("--service-id", action="append", default=split_csv(os.getenv("PD_SERVICE_IDS")), help="Optional service ID filter. May be repeated.")
    parser.add_argument("--team-id", action="append", default=split_csv(os.getenv("PD_TEAM_IDS")), help="Optional team ID filter. May be repeated.")
    parser.add_argument("--escalation-policy-id", action="append", default=split_csv(os.getenv("PD_ESCALATION_POLICY_IDS")), help="Optional on-call escalation policy filter. May be repeated.")
    parser.add_argument("--schedule-id", action="append", default=split_csv(os.getenv("PD_SCHEDULE_IDS")), help="Optional on-call schedule filter. May be repeated.")
    parser.add_argument("--quiet", action="store_true", default=env_bool("PD_QUIET"), help="Only print errors.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pd-auto-ack",
        description="Acknowledge triggered PagerDuty incidents only while the configured user is on call.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init",
        help="Create a starter env file.",
        description="Create a starter env file for PagerDuty On-Call Ack.",
    )
    init_parser.add_argument("--env-file", default=os.getenv("PD_ENV_FILE", ".env"), help="Path to create. Defaults to .env.")
    init_parser.add_argument("--force", action="store_true", help="Overwrite the env file if it already exists.")

    run_parser = subparsers.add_parser(
        "run",
        help="Poll PagerDuty and acknowledge matching triggered incidents.",
        description="Poll PagerDuty and acknowledge matching triggered incidents.",
    )
    add_common_arguments(run_parser)
    run_parser.add_argument("--once", action="store_true", help="Run one poll cycle and exit. This is the default.")
    run_parser.add_argument("--watch", action="store_true", help="Keep polling until stopped.")
    run_parser.add_argument("--apply", action="store_true", default=env_bool("PD_APPLY"), help="Actually acknowledge incidents.")
    run_parser.add_argument("--dry-run", action="store_true", help="Force dry-run mode even if PD_APPLY=true.")
    run_parser.add_argument("--interval", type=int, default=env_int("PD_POLL_SECONDS", 30), help="Polling interval in seconds for --watch.")

    tui_parser = subparsers.add_parser(
        "tui",
        help="Open an interactive terminal dashboard.",
        description="Open a k9s-style terminal dashboard for PagerDuty On-Call Ack.",
    )
    add_common_arguments(tui_parser)
    tui_parser.add_argument("--apply", action="store_true", default=env_bool("PD_APPLY"), help="Actually acknowledge incidents from the TUI.")
    tui_parser.add_argument("--dry-run", action="store_true", help="Force dry-run mode even if PD_APPLY=true.")
    tui_parser.add_argument("--interval", type=int, default=env_int("PD_POLL_SECONDS", 30), help="Polling interval in seconds.")

    check_parser = subparsers.add_parser(
        "check",
        help="Validate PagerDuty access and show current on-call/incident state.",
        description="Validate PagerDuty access and show current on-call/incident state without acknowledging anything.",
    )
    add_common_arguments(check_parser)

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Validate local configuration without calling PagerDuty.",
        description="Validate local configuration without calling PagerDuty.",
    )
    add_common_arguments(doctor_parser)

    return parser


def build_config_from_args(args: argparse.Namespace) -> Config:
    interval = getattr(args, "interval", env_int("PD_POLL_SECONDS", 30))
    if interval < 5:
        raise ConfigError("--interval must be at least 5 seconds.")
    if args.timeout < 1:
        raise ConfigError("--timeout must be at least 1 second.")
    if args.max_pages < 1:
        raise ConfigError("--max-pages must be at least 1.")

    apply = bool(getattr(args, "apply", False) and not getattr(args, "dry_run", False))
    return Config(
        api_base_url=args.api_base_url,
        auth_header=build_auth_header(os.getenv("PD_API_TOKEN")),
        user_id=args.user_id,
        from_email=args.from_email,
        apply=apply,
        interval_seconds=interval,
        request_timeout_seconds=args.timeout,
        max_pages=args.max_pages,
        service_ids=args.service_id,
        team_ids=args.team_id,
        escalation_policy_ids=args.escalation_policy_id,
        schedule_ids=args.schedule_id,
        quiet=args.quiet,
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    argv = normalize_argv(argv)
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--env-file", default=os.getenv("PD_ENV_FILE", ".env"))
    pre_args, _ = pre_parser.parse_known_args(argv)
    if argv[0] not in {"init", "-h", "--help", "--version"}:
        load_env_file(pre_args.env_file)

    return build_parser().parse_args(argv)


def build_config(argv: list[str]) -> tuple[Config, bool]:
    args = parse_args(argv)
    return build_config_from_args(args), bool(getattr(args, "watch", False))


def run_command(config: Config, watch: bool) -> int:
    config = resolve_identity(config)
    if not config.user_id:
        raise ConfigError("PD_USER_ID could not be resolved.")
    if not config.from_email:
        raise ConfigError("PD_FROM_EMAIL could not be resolved.")

    client = PagerDutyClient(config)
    mode = "live apply" if config.apply else "dry-run"
    log(config, f"Starting PagerDuty auto-ack in {mode} mode for user {config.user_id}.")

    while True:
        run_once(client, config)
        if not watch:
            return 0
        time.sleep(config.interval_seconds)


def check_command(config: Config) -> int:
    config = resolve_identity(config)
    if not config.user_id:
        raise ConfigError("PD_USER_ID could not be resolved.")

    client = PagerDutyClient(config)
    user = client.get_current_user()
    print(f"PagerDuty API token is valid for {user.get('email', user.get('id', 'unknown user'))}.")

    now = utc_now()
    active_oncalls = list_active_oncalls(client, config, now)
    if active_oncalls:
        for oncall in active_oncalls:
            print(f"On call now: {describe_oncall(oncall)}")
    else:
        print("On call now: no")

    open_incidents = list_open_incidents(client, config)
    print_incidents("Open incidents assigned to user", open_incidents)
    print_triggered_summary(filter_triggered_incidents(open_incidents))

    if config.team_ids:
        client.test_ability("teams")
        print("Account ability check passed: teams")

    return 0


def doctor_command(config: Config) -> int:
    print("Local configuration looks usable.")
    print(f"API base URL: {config.api_base_url}")
    print(f"User ID configured: {'yes' if config.user_id else 'no; will try /users/me'}")
    print(f"From email configured: {'yes' if config.from_email else 'no; will try /users/me'}")
    print(f"Live apply default: {'yes' if config.apply else 'no'}")
    print(f"Service filters: {len(config.service_ids)}")
    print(f"Team filters: {len(config.team_ids)}")
    print(f"Escalation policy filters: {len(config.escalation_policy_ids)}")
    print(f"Schedule filters: {len(config.schedule_ids)}")
    return 0


def tui_command(config: Config) -> int:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise ConfigError("The TUI requires an interactive terminal. Use `pd-auto-ack run` for logs, cron, or redirected output.")

    try:
        from .tui import run_tui
    except ModuleNotFoundError as exc:
        if exc.name and (exc.name == "textual" or exc.name.startswith("textual.")):
            raise ConfigError(
                "The TUI requires Textual. Install with "
                '`pipx install "pagerduty-oncall-ack[tui]"` for a fresh install, '
                "or `pipx inject pagerduty-oncall-ack textual` for an existing pipx install."
            ) from exc
        raise

    config = resolve_identity(config)
    if not config.user_id:
        raise ConfigError("PD_USER_ID could not be resolved.")
    if not config.from_email:
        raise ConfigError("PD_FROM_EMAIL could not be resolved.")
    return run_tui(config)


def init_command(env_file: str, *, force: bool = False) -> int:
    path = create_env_file(env_file, force=force)
    print(f"Created {path}")
    print("Edit it, then run:")
    print(f"  pd-auto-ack doctor --env-file {path}")
    print(f"  pd-auto-ack check --env-file {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    try:
        args = parse_args(argv)
        if args.command == "init":
            return init_command(args.env_file, force=args.force)

        config = build_config_from_args(args)

        if args.command == "run":
            return run_command(config, bool(getattr(args, "watch", False)))
        if args.command == "check":
            return check_command(dataclasses.replace(config, apply=False))
        if args.command == "doctor":
            return doctor_command(config)
        if args.command == "tui":
            return tui_command(config)
        raise ConfigError(f"Unknown command: {args.command}")
    except KeyboardInterrupt:
        print("Stopped.", file=sys.stderr)
        return 130
    except (ConfigError, PagerDutyAPIError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
