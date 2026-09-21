# How It Works

Every poll cycle follows this decision flow:

1. Load configuration from `--env-file`.
2. Resolve the PagerDuty user from `PD_USER_ID` or `/users/me`.
3. Call `GET /oncalls` for that user at the current time.
4. Stop immediately if the user is not currently on call.
5. Call `GET /incidents` for open incidents assigned to that user with `statuses[]=triggered` and `statuses[]=acknowledged`.
6. Display the open incident list.
7. Stop if there are no matching triggered incidents.
8. In dry-run mode, print what would be acknowledged.
9. In live mode, call `PUT /incidents/{id}` with `status: acknowledged`.

The CLI only acknowledges incidents when:

- the configured user is currently on call
- the incident is `triggered`
- the incident is assigned to that user

The CLI does not acknowledge incidents assigned to someone else. It does not acknowledge already acknowledged incidents. It does not resolve incidents, reassign incidents, edit titles, or add notes.

## Open vs Triggered

For display, open incidents means incidents with PagerDuty status `triggered` or `acknowledged`.

For action, only `triggered` incidents are eligible for acknowledgement. Already `acknowledged` incidents are shown for operator awareness but are not updated.

## Dry-Run vs Live Mode

Dry-run mode is the default. These commands do not change PagerDuty:

```sh
pd-auto-ack run --env-file ~/.pd-auto-ack.env --once
pd-auto-ack run --env-file ~/.pd-auto-ack.env --watch --interval 30
```

Live mode requires `--apply`:

```sh
pd-auto-ack run --env-file ~/.pd-auto-ack.env --watch --interval 30 --apply
```

You can also set `PD_APPLY=true` in the env file, but leaving `PD_APPLY=false` and passing `--apply` explicitly is safer.

## Terminal Dashboard

`pd-auto-ack tui` uses the same decision flow as `run`, but displays it in an interactive terminal dashboard.

The dashboard refreshes on the configured interval, shows open incidents and selected incident details, and starts in dry-run mode unless live mode is explicitly enabled with `--apply` or `PD_APPLY=true`.
