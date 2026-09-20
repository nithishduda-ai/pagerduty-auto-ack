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

From this checkout:

```sh
python3 -m pip install .
```

Or with `pipx`:

```sh
pipx install .
```

From GitHub:

```sh
pipx install git+https://github.com/nithishduda-ai/pagerduty-auto-ack.git
```

After install, verify:

```sh
pd-auto-ack --version
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

Create a local `.env` based on `.env.example` and fill in:

```sh
PD_API_TOKEN=...
PD_USER_ID=...
PD_FROM_EMAIL=...
```

The token needs permissions equivalent to:

- `oncalls.read`
- `incidents.read`
- `incidents.write`

`PD_FROM_EMAIL` must be a valid PagerDuty user email for the account because PagerDuty requires the `From` header when updating incidents.

## Commands

Validate local configuration without calling PagerDuty:

```sh
pd-auto-ack doctor --env-file .env
```

Validate PagerDuty API access and show current on-call/incident state without acknowledging anything:

```sh
pd-auto-ack check --env-file .env
```

Dry-run is the default. It prints what would be acknowledged without changing PagerDuty:

```sh
pd-auto-ack run --env-file .env --once
```

Continuous dry-run polling:

```sh
pd-auto-ack run --env-file .env --watch --interval 30
```

Run continuously and actually acknowledge matching incidents:

```sh
pd-auto-ack run --env-file .env --watch --interval 30 --apply
```

Run once, useful from cron or another local scheduler:

```sh
pd-auto-ack run --env-file .env --once --apply
```

Example cron entry for once-per-minute local polling:

```cron
* * * * * cd /Users/nithish/Documents/Pagerduty && /usr/bin/env pd-auto-ack run --env-file .env --once --apply >> pagerduty-auto-ack.log 2>&1
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
PYTHONPATH=src python3 -m unittest
```

Compile-check the package:

```sh
PYTHONPYCACHEPREFIX=/private/tmp/pagerduty-pycache python3 -m py_compile pagerduty_auto_ack.py src/pagerduty_auto_ack/*.py tests/*.py
```
