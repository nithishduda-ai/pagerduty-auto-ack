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

## Commands

Validate local configuration without calling PagerDuty:

```sh
pd-auto-ack doctor --env-file ~/.pd-auto-ack.env
```

Validate PagerDuty API access and show current on-call/incident state without acknowledging anything:

```sh
pd-auto-ack check --env-file ~/.pd-auto-ack.env
```

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
