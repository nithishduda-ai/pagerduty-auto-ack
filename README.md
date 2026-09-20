# PagerDuty Auto-Ack

`pagerduty-auto-ack` installs the `pd-auto-ack` CLI. It acknowledges PagerDuty incidents only when the configured user is currently on call.

It does only this:

- Checks whether the user is actively on call with `GET /oncalls`.
- Lists only `triggered` incidents assigned to that user with `GET /incidents`.
- Acknowledges those incidents with `PUT /incidents/{id}` and the minimal `status: acknowledged` payload.
- Does not resolve incidents, reassign incidents, edit titles, or create notes.

The endpoint behavior was checked against PagerDuty's official API reference and published OpenAPI schema:

- <https://developer.pagerduty.com/api-reference/>
- <https://github.com/PagerDuty/api-schema>

## Install

Recommended install uses `pipx`, which keeps CLI tools in isolated Python environments.

If `pipx` is not installed yet, install it first.

macOS with Homebrew:

```sh
brew install pipx
pipx ensurepath
exec zsh -l
```

Linux:

```sh
python3 -m pip install --user pipx
python3 -m pipx ensurepath
exec "$SHELL" -l
```

Verify `pipx`:

```sh
pipx --version
```

Install from GitHub:

```sh
pipx install git+https://github.com/nithishduda-ai/pagerduty-auto-ack.git
```

After install, verify:

```sh
pd-auto-ack --version
```

Upgrade an existing install:

```sh
pipx upgrade pagerduty-auto-ack
```

For local development from this checkout:

```sh
python3 -m pip install .
```

Or with `pipx`:

```sh
pipx install .
```

You can also run from a checkout without installing:

```sh
PYTHONPATH=src python3 -m pagerduty_auto_ack --help
```

The old script path still works for compatibility:

```sh
python3 pagerduty_auto_ack.py --help
```

## Quick Start

Create a starter config file. This file will contain your PagerDuty API token, so keep it local and private.

```sh
pd-auto-ack init --env-file ~/.pd-auto-ack.env
```

Then edit it:

```sh
nano ~/.pd-auto-ack.env
```

Fill in these values:

```sh
PD_API_TOKEN=...
PD_USER_ID=...
PD_FROM_EMAIL=...
PD_APPLY=false
PD_POLL_SECONDS=30
```

Run a local config check:

```sh
pd-auto-ack doctor --env-file ~/.pd-auto-ack.env
```

Then run a PagerDuty API check:

```sh
pd-auto-ack check --env-file ~/.pd-auto-ack.env
```

Example healthy output:

```text
PagerDuty API token is valid for user@example.com.
On call now: EU Support Escalation Policy / EU Support Escalation / level 1
Triggered incidents assigned to user: 0
```

That means the token works, the CLI can identify the PagerDuty user, the user is currently on call, and there are no triggered incidents assigned to them right now.

Run one dry-run cycle:

```sh
pd-auto-ack run --env-file ~/.pd-auto-ack.env --once
```

Run continuous dry-run mode:

```sh
pd-auto-ack run --env-file ~/.pd-auto-ack.env --watch --interval 30
```

Only after the dry-run output looks right, run live mode:

```sh
pd-auto-ack run --env-file ~/.pd-auto-ack.env --watch --interval 30 --apply
```

## Where To Get The Values

`PD_API_TOKEN` is a PagerDuty REST API token. Create one in PagerDuty or ask a PagerDuty admin to create one with the required permissions below. Keep this token private.

`PD_FROM_EMAIL` is the email address of a valid PagerDuty user in the same account. Use the email address you use to sign in to PagerDuty.

`PD_USER_ID` is the PagerDuty user ID for the person whose on-call status should be checked. If the API token belongs to that same user, the CLI can usually infer it from `/users/me`, so the generated placeholder can be left in place for a first test:

```sh
PD_USER_ID=PAGERDUTY_USER_ID
```

After the token is configured, this command confirms which user the token belongs to:

```sh
pd-auto-ack check --env-file ~/.pd-auto-ack.env
```

## Required PagerDuty Access

The token needs permissions equivalent to:

- `oncalls.read`
- `incidents.read`
- `incidents.write`

## Configuration Values

- `PD_API_TOKEN`: PagerDuty REST API token.
- `PD_USER_ID`: PagerDuty user ID for the person who should be checked as on call.
- `PD_FROM_EMAIL`: Email of a valid PagerDuty user. PagerDuty requires this when updating incidents.
- `PD_APPLY=false`: keeps the tool in dry-run mode by default.
- `PD_POLL_SECONDS=30`: polling interval for `--watch` mode.
- `PD_SERVICE_IDS`: optional comma-separated service ID allowlist.
- `PD_TEAM_IDS`: optional comma-separated team ID allowlist.
- `PD_ESCALATION_POLICY_IDS`: optional comma-separated escalation policy ID allowlist for on-call checks.
- `PD_SCHEDULE_IDS`: optional comma-separated schedule ID allowlist for on-call checks.
- `PD_REQUEST_TIMEOUT_SECONDS`: optional PagerDuty API request timeout.
- `PD_MAX_PAGES`: optional safety limit for paginated PagerDuty list calls.

`PD_USER_ID` and `PD_FROM_EMAIL` can often be inferred from `/users/me` if the API token belongs to the same user. Explicit values are still recommended for long-running jobs.

`PD_FROM_EMAIL` must be a valid PagerDuty user email for the account because PagerDuty requires the `From` header when updating incidents.

## How It Works

Every poll cycle follows this decision flow:

1. Load configuration from `--env-file`.
2. Resolve the PagerDuty user from `PD_USER_ID` or `/users/me`.
3. Call `GET /oncalls` for that user at the current time.
4. Stop immediately if the user is not currently on call.
5. Call `GET /incidents` for incidents assigned to that user with `statuses[]=triggered`.
6. Stop if there are no matching triggered incidents.
7. In dry-run mode, print what would be acknowledged.
8. In live mode, call `PUT /incidents/{id}` with `status: acknowledged`.

The CLI only acknowledges incidents when:

- the configured user is currently on call
- the incident is `triggered`
- the incident is assigned to that user

The CLI does not acknowledge incidents assigned to someone else. It does not acknowledge already acknowledged incidents. It does not resolve incidents, reassign incidents, edit titles, or add notes.

## API Call Volume And Limits

For `pd-auto-ack run --watch --interval 30`, each running user makes calls independently.

Startup calls:

- If `PD_USER_ID` and `PD_FROM_EMAIL` are both set, startup makes no identity lookup call.
- If either value is omitted or left as a placeholder, startup calls `GET /users/me` once to infer the user.

Per poll cycle:

- User is not on call: usually 1 call, `GET /oncalls`.
- User is on call with no triggered incidents: usually 2 calls, `GET /oncalls` and `GET /incidents`.
- User is on call with `N` triggered incidents in live mode: usually `2 + N` calls, because each incident acknowledgement is one `PUT /incidents/{id}` call.

With the default 30 second interval, that is approximately:

- Not on call: 2 calls per minute per running user.
- On call, no incidents: 4 calls per minute per running user.
- On call, live mode with new incidents: 4 calls per minute plus one write call for each incident acknowledged.

List calls are paginated with `limit=100`. If PagerDuty returns more pages, the CLI will make additional page requests up to `PD_MAX_PAGES`, which defaults to `10`.

For a team rollout, total call volume scales linearly with the number of people running the tool. For example, 50 people running at a 30 second interval while not on call is about 100 PagerDuty API calls per minute. If 5 of those people are on call, add about 10 more calls per minute for incident checks.

PagerDuty REST API responses include rate-limit headers such as `ratelimit-limit`, `ratelimit-remaining`, and `ratelimit-reset`, and PagerDuty may return HTTP `429` when rate limited. See PagerDuty's [REST API rate limit documentation](https://support.pagerduty.com/main/docs/rest-api-rate-limits).

Recommended rollout practices:

- Prefer one user token per person instead of sharing one account-wide token.
- Use the minimum required permissions: `oncalls.read`, `incidents.read`, and `incidents.write`.
- Keep `PD_APPLY=false` until dry-run output is trusted.
- Increase `PD_POLL_SECONDS` to `60` or `120` for broad team rollouts if near rate limits.
- Use optional filters like `PD_SERVICE_IDS`, `PD_TEAM_IDS`, `PD_ESCALATION_POLICY_IDS`, and `PD_SCHEDULE_IDS` to reduce the incidents and on-call data queried.

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

## Command Reference

Use `pd-auto-ack --help` to see all commands.

### `pd-auto-ack init`

Creates a starter configuration file.

```sh
pd-auto-ack init --env-file ~/.pd-auto-ack.env
```

What it does:

- Creates the env file if it does not exist.
- Writes placeholders for `PD_API_TOKEN`, `PD_USER_ID`, `PD_FROM_EMAIL`, and optional filters.
- Sets file permissions to `0600` where supported, so only the current user can read/write it.
- Does not call PagerDuty.

Useful flags:

- `--env-file PATH`: choose where to create the config file.
- `--force`: overwrite an existing config file.

### `pd-auto-ack doctor`

Validate local configuration without calling PagerDuty:

```sh
pd-auto-ack doctor --env-file ~/.pd-auto-ack.env
```

What it does:

- Loads the env file.
- Verifies local config parsing.
- Shows whether key values are configured.
- Does not call PagerDuty.
- Does not acknowledge anything.

Use this first when you are debugging a config file.

### `pd-auto-ack check`

Validate PagerDuty API access and show current on-call/incident state without acknowledging anything:

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

### `pd-auto-ack run`

Dry-run is the default. It prints what would be acknowledged without changing PagerDuty:

```sh
pd-auto-ack run --env-file ~/.pd-auto-ack.env --once
```

Continuous dry-run polling:

```sh
pd-auto-ack run --env-file ~/.pd-auto-ack.env --watch --interval 30
```

Run continuously and actually acknowledge matching incidents:

```sh
pd-auto-ack run --env-file ~/.pd-auto-ack.env --watch --interval 30 --apply
```

Run once, useful from cron or another local scheduler:

```sh
pd-auto-ack run --env-file ~/.pd-auto-ack.env --once --apply
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

### Common Flags

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

### Examples

Example cron entry for once-per-minute local polling:

```cron
* * * * * /usr/bin/env pd-auto-ack run --env-file ~/.pd-auto-ack.env --once --apply >> ~/pagerduty-auto-ack.log 2>&1
```

## Extra Safety Filters

You can limit the script to specific PagerDuty objects:

```sh
PD_SERVICE_IDS=P123ABC,P456DEF
PD_TEAM_IDS=PTEAM123
PD_ESCALATION_POLICY_IDS=PEP123
PD_SCHEDULE_IDS=PSCHED123
```

The script still requires the configured user to be actively on call before it looks for incidents.

## Local Development

Run tests:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests
```

Compile-check the package:

```sh
PYTHONPYCACHEPREFIX=/private/tmp/pagerduty-pycache python3 -m py_compile pagerduty_auto_ack.py src/pagerduty_auto_ack/*.py tests/*.py
```
