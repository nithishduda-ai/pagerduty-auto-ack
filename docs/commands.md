# Command Reference

Use `pd-auto-ack --help` to see all commands.

## `pd-auto-ack init`

Creates a starter configuration file.

```sh
pd-auto-ack init --env-file ~/.pd-auto-ack.env
```

What it does:

- Creates the env file if it does not exist.
- Writes placeholders for required values and optional filters.
- Sets file permissions to `0600` where supported.
- Does not call PagerDuty.

Useful flags:

- `--env-file PATH`: choose where to create the config file.
- `--force`: overwrite an existing config file.

## `pd-auto-ack doctor`

Validates local configuration without calling PagerDuty.

```sh
pd-auto-ack doctor --env-file ~/.pd-auto-ack.env
```

What it does:

- Loads the env file.
- Verifies local config parsing.
- Shows whether key values are configured.
- Does not call PagerDuty.
- Does not acknowledge anything.

Use this first when debugging a config file.

## `pd-auto-ack check`

Validates PagerDuty API access and shows current on-call/incident state without acknowledging anything.

```sh
pd-auto-ack check --env-file ~/.pd-auto-ack.env
```

What it does:

- Calls PagerDuty to validate the API token.
- Resolves the configured user.
- Shows whether the user is currently on call.
- Lists the count of currently triggered incidents assigned to that user.
- Does not acknowledge anything.

Use this after `doctor` and before `run`.

## `pd-auto-ack run`

Runs the auto-ack decision flow.

Dry-run one cycle:

```sh
pd-auto-ack run --env-file ~/.pd-auto-ack.env --once
```

Continuous dry-run:

```sh
pd-auto-ack run --env-file ~/.pd-auto-ack.env --watch --interval 30
```

Continuous live mode:

```sh
pd-auto-ack run --env-file ~/.pd-auto-ack.env --watch --interval 30 --apply
```

What it does:

- Checks whether the configured user is on call.
- If the user is not on call, exits or waits for the next poll.
- If the user is on call, looks for `triggered` incidents assigned to that user.
- In dry-run mode, prints what it would acknowledge.
- In live mode with `--apply`, acknowledges matching incidents.

Useful flags:

- `--env-file PATH`: load config from a specific env file.
- `--once`: run one poll cycle and exit. This is the default for `run`.
- `--watch`: keep polling until stopped with `Ctrl-C`.
- `--interval SECONDS`: wait this many seconds between polls in `--watch` mode.
- `--apply`: live mode. Actually acknowledge matching incidents.
- `--dry-run`: force dry-run mode even if `PD_APPLY=true` is set in the env file.

## Common Flags

- `--env-file PATH`: path to the config file. Example: `~/.pd-auto-ack.env`.
- `--user-id USER_ID`: override `PD_USER_ID` from the env file.
- `--from-email EMAIL`: override `PD_FROM_EMAIL` from the env file.
- `--service-id SERVICE_ID`: restrict incident lookup to a service. Can be repeated.
- `--team-id TEAM_ID`: restrict incident lookup to a team. Can be repeated.
- `--escalation-policy-id POLICY_ID`: restrict on-call checks to an escalation policy. Can be repeated.
- `--schedule-id SCHEDULE_ID`: restrict on-call checks to a schedule. Can be repeated.
- `--timeout SECONDS`: PagerDuty API request timeout.
- `--max-pages COUNT`: pagination safety limit for list requests.
- `--quiet`: only print errors.
