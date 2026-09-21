"""Textual terminal dashboard for PagerDuty On-Call Ack."""

from __future__ import annotations

import dataclasses
import threading
import time
from datetime import datetime
from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Footer, Header, Static

from . import cli


@dataclasses.dataclass(frozen=True)
class TuiSnapshot:
    checked_at: datetime
    user_id: str
    active_oncalls: list[dict[str, Any]]
    open_incidents: list[dict[str, Any]]
    triggered_incidents: list[dict[str, Any]]
    acknowledged_ids: list[str]
    dry_run_ids: list[str]
    errors: list[str]
    api_calls: int


class CountingPagerDutyClient(cli.PagerDutyClient):
    def __init__(self, config: cli.Config) -> None:
        super().__init__(config)
        self.request_count = 0

    def request(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.request_count += 1
        return super().request(*args, **kwargs)


def incident_id(incident: dict[str, Any]) -> str:
    return str(incident.get("id") or "")


def incident_title(incident: dict[str, Any]) -> str:
    return str(incident.get("title") or incident.get("summary") or "untitled")


def incident_service(incident: dict[str, Any]) -> str:
    service = incident.get("service") or {}
    return str(service.get("summary") or service.get("id") or "-")


def incident_age(incident: dict[str, Any], now: datetime) -> str:
    try:
        created_at = cli.parse_pd_time(incident.get("created_at") or incident.get("last_status_change_at"))
    except ValueError:
        return "-"
    if not created_at:
        return "-"

    seconds = max(int((now - created_at).total_seconds()), 0)
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    if hours < 48:
        return f"{hours}h"
    return f"{hours // 24}d"


def collect_snapshot(client: CountingPagerDutyClient, config: cli.Config) -> TuiSnapshot:
    request_start = client.request_count
    checked_at = cli.utc_now()
    errors: list[str] = []
    acknowledged_ids: list[str] = []
    dry_run_ids: list[str] = []

    active_oncalls = cli.list_active_oncalls(client, config, checked_at)
    open_incidents: list[dict[str, Any]] = []
    triggered_incidents: list[dict[str, Any]] = []

    if active_oncalls:
        open_incidents = cli.list_open_incidents(client, config)
        triggered_incidents = cli.filter_triggered_incidents(open_incidents)

        for incident in triggered_incidents:
            item_id = incident_id(incident)
            if not item_id:
                errors.append(f"Skipping incident without an id: {incident_title(incident)}")
                continue

            if config.apply:
                try:
                    client.acknowledge_incident(item_id)
                    acknowledged_ids.append(item_id)
                except Exception as exc:  # Keep the dashboard alive during partial failures.
                    errors.append(f"Could not acknowledge {item_id}: {exc}")
            else:
                dry_run_ids.append(item_id)

    return TuiSnapshot(
        checked_at=checked_at,
        user_id=config.user_id or "unknown",
        active_oncalls=active_oncalls,
        open_incidents=open_incidents,
        triggered_incidents=triggered_incidents,
        acknowledged_ids=acknowledged_ids,
        dry_run_ids=dry_run_ids,
        errors=errors,
        api_calls=client.request_count - request_start,
    )


class PagerDutyTuiApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }

    #summary {
        height: 4;
        padding: 0 1;
        border: solid $accent;
    }

    #body {
        height: 1fr;
    }

    #incidents {
        width: 2fr;
        height: 100%;
    }

    #side {
        width: 1fr;
        height: 100%;
    }

    #details {
        height: 2fr;
        padding: 0 1;
        border: solid $accent;
    }

    #events {
        height: 1fr;
        padding: 0 1;
        border: solid $secondary;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("p", "toggle_pause", "Pause"),
    ]

    def __init__(self, config: cli.Config) -> None:
        super().__init__()
        self.config = config
        self.client = CountingPagerDutyClient(config)
        self.snapshot: TuiSnapshot | None = None
        self.incidents_by_id: dict[str, dict[str, Any]] = {}
        self.selected_incident_id: str | None = None
        self.next_poll_at = 0.0
        self.polling = False
        self.paused = False
        self.events: list[str] = ["Ready. Press r to refresh, p to pause, q to quit."]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("", id="summary")
        with Horizontal(id="body"):
            yield DataTable(id="incidents")
            with Vertical(id="side"):
                yield Static("No incident selected.", id="details")
                yield Static("", id="events")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#incidents", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns("Status", "Urgency", "Service", "Incident", "Age", "ID")
        self.update_summary("starting")
        self.update_events()
        self.trigger_refresh()
        self.set_interval(1, self.tick)

    def tick(self) -> None:
        self.update_summary("polling" if self.polling else "paused" if self.paused else "watching")
        if not self.paused and not self.polling and time.monotonic() >= self.next_poll_at:
            self.trigger_refresh()

    def action_refresh(self) -> None:
        self.add_event("Manual refresh requested.")
        self.trigger_refresh(force=True)

    def action_toggle_pause(self) -> None:
        self.paused = not self.paused
        self.add_event("Paused." if self.paused else "Resumed.")
        self.update_summary("paused" if self.paused else "watching")

    def trigger_refresh(self, *, force: bool = False) -> None:
        if self.polling:
            if force:
                self.add_event("Refresh already in progress.")
            return

        self.polling = True
        self.update_summary("polling")
        worker = threading.Thread(target=self.poll_in_thread, daemon=True)
        worker.start()

    def poll_in_thread(self) -> None:
        try:
            snapshot = collect_snapshot(self.client, self.config)
        except Exception as exc:
            self.call_from_thread(self.apply_error, exc)
        else:
            self.call_from_thread(self.apply_snapshot, snapshot)

    def apply_error(self, exc: Exception) -> None:
        self.polling = False
        self.next_poll_at = time.monotonic() + self.config.interval_seconds
        self.add_event(f"Error: {exc}")
        self.update_summary("error")

    def apply_snapshot(self, snapshot: TuiSnapshot) -> None:
        self.snapshot = snapshot
        self.polling = False
        self.next_poll_at = time.monotonic() + self.config.interval_seconds
        self.refresh_incident_table(snapshot)
        self.refresh_details()
        self.add_snapshot_event(snapshot)
        self.update_summary("watching")

    def refresh_incident_table(self, snapshot: TuiSnapshot) -> None:
        table = self.query_one("#incidents", DataTable)
        table.clear()
        self.incidents_by_id = {}

        if not snapshot.open_incidents:
            table.add_row("-", "-", "-", "No open incidents assigned to user", "-", "-", key="__empty__")
            self.selected_incident_id = None
            return

        now = snapshot.checked_at
        for index, incident in enumerate(snapshot.open_incidents):
            item_id = incident_id(incident) or f"incident-{index}"
            self.incidents_by_id[item_id] = incident
            status = str(incident.get("status") or "-")
            urgency = str(incident.get("urgency") or "-")
            title = incident_title(incident)
            table.add_row(
                status,
                urgency,
                incident_service(incident),
                title,
                incident_age(incident, now),
                item_id,
                key=item_id,
            )

        if self.selected_incident_id not in self.incidents_by_id:
            self.selected_incident_id = next(iter(self.incidents_by_id), None)

    def refresh_details(self) -> None:
        details = self.query_one("#details", Static)
        if not self.selected_incident_id:
            details.update("No incident selected.")
            return

        incident = self.incidents_by_id.get(self.selected_incident_id)
        if not incident:
            details.update("No incident selected.")
            return

        service = incident.get("service") or {}
        escalation_policy = incident.get("escalation_policy") or {}
        assignments = incident.get("assignments") or []
        assignees = ", ".join(
            str((assignment.get("assignee") or {}).get("summary") or (assignment.get("assignee") or {}).get("id") or "unknown")
            for assignment in assignments
            if isinstance(assignment, dict)
        )

        lines = [
            incident_title(incident),
            "",
            f"ID: {incident.get('id', '-')}",
            f"Number: {incident.get('incident_number', '-')}",
            f"Status: {incident.get('status', '-')}",
            f"Urgency: {incident.get('urgency', '-')}",
            f"Service: {service.get('summary') or service.get('id') or '-'}",
            f"Escalation policy: {escalation_policy.get('summary') or escalation_policy.get('id') or '-'}",
            f"Assignments: {assignees or '-'}",
            f"Created: {incident.get('created_at', '-')}",
            f"URL: {incident.get('html_url', '-')}",
        ]
        details.update("\n".join(lines))

    def on_data_table_cell_highlighted(self, event: Any) -> None:
        row_key = getattr(getattr(event, "cell_key", None), "row_key", None)
        self.select_row_key(row_key)

    def on_data_table_row_highlighted(self, event: Any) -> None:
        self.select_row_key(getattr(event, "row_key", None))

    def on_data_table_row_selected(self, event: Any) -> None:
        self.select_row_key(getattr(event, "row_key", None))

    def select_row_key(self, row_key: Any) -> None:
        value = getattr(row_key, "value", row_key)
        if not value or value == "__empty__":
            return
        self.selected_incident_id = str(value)
        self.refresh_details()

    def update_summary(self, state: str) -> None:
        summary = self.query_one("#summary", Static)
        mode = "LIVE APPLY" if self.config.apply else "DRY-RUN"
        oncall = "unknown"
        open_count = 0
        eligible_count = 0
        api_calls = 0
        last_poll = "-"

        if self.snapshot:
            oncall = "yes" if self.snapshot.active_oncalls else "no"
            open_count = len(self.snapshot.open_incidents)
            eligible_count = len(self.snapshot.triggered_incidents)
            api_calls = self.snapshot.api_calls
            last_poll = cli.format_pd_time(self.snapshot.checked_at)

        if self.polling:
            next_poll = "now"
        elif self.paused:
            next_poll = "paused"
        else:
            remaining = max(int(self.next_poll_at - time.monotonic()), 0)
            next_poll = f"{remaining}s"

        summary.update(
            "\n".join(
                [
                    f"User: {self.config.user_id or '-'}    Mode: {mode}    State: {state}",
                    f"On call: {oncall}    Open: {open_count}    Eligible: {eligible_count}    API calls: {api_calls}",
                    f"Last poll: {last_poll}    Next poll: {next_poll}",
                ]
            )
        )

    def add_snapshot_event(self, snapshot: TuiSnapshot) -> None:
        timestamp = snapshot.checked_at.strftime("%H:%M:%S")
        if not snapshot.active_oncalls:
            self.add_event(f"{timestamp} user is not on call; incident lookup skipped.")
        elif snapshot.acknowledged_ids:
            self.add_event(f"{timestamp} acknowledged {len(snapshot.acknowledged_ids)} triggered incident(s).")
        elif snapshot.dry_run_ids:
            self.add_event(f"{timestamp} dry-run would acknowledge {len(snapshot.dry_run_ids)} incident(s).")
        else:
            self.add_event(f"{timestamp} no triggered incidents eligible for acknowledgement.")

        for error in snapshot.errors:
            self.add_event(error)

    def add_event(self, message: str) -> None:
        self.events.append(message)
        self.events = self.events[-8:]
        self.update_events()

    def update_events(self) -> None:
        events = self.query_one("#events", Static)
        events.update("\n".join(self.events))


def run_tui(config: cli.Config) -> int:
    app = PagerDutyTuiApp(config)
    app.run()
    return 0
