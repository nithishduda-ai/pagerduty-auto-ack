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

## Configure

Create a starter config file:

```sh
pd-auto-ack init --env-file ~/.pd-auto-ack.env
```

Then edit it:

```sh
nano ~/.pd-auto-ack.env
```

Fill in:

```sh
PD_API_TOKEN=...
PD_USER_ID=...
PD_FROM_EMAIL=...
PD_APPLY=false
PD_POLL_SECONDS=30
```

The token needs permissions equivalent to:

- `oncalls.read`
- `incidents.read`
- `incidents.write`

Required values:

- `PD_API_TOKEN`: PagerDuty REST API token.
- `PD_USER_ID`: PagerDuty user ID for the person who should be checked as on call.
- `PD_FROM_EMAIL`: Email of a valid PagerDuty user. PagerDuty requires this when updating incidents.

Recommended values:

- `PD_APPLY=false`: keeps the tool in dry-run mode by default.
- `PD_POLL_SECONDS=30`: polling interval for `--watch` mode.

`PD_FROM_EMAIL` must be a valid PagerDuty user email for the account because PagerDuty requires the `From` header when updating incidents.

The CLI only acknowledges incidents when:

- the configured user is currently on call
- the incident is `triggered`
- the incident is assigned to that user

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
