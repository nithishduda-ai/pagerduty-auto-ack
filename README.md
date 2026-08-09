# PagerDuty Local Auto-Ack

Small local script that acknowledges PagerDuty incidents only when the configured user is currently on call.

It does only this:

- Checks whether the user is actively on call with `GET /oncalls`.
- Lists only `triggered` incidents assigned to that user with `GET /incidents`.
- Acknowledges those incidents with `PUT /incidents/{id}` and the minimal `status: acknowledged` payload.
- Does not resolve incidents, reassign incidents, edit titles, or create notes.

The endpoint behavior was checked against PagerDuty's official API reference and published OpenAPI schema:

- <https://developer.pagerduty.com/api-reference/>
- <https://github.com/PagerDuty/api-schema>

## Setup

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

## Dry Run

Dry-run is the default. It prints what would be acknowledged without changing PagerDuty:

```sh
python3 pagerduty_auto_ack.py --env-file .env --once
```

Continuous dry-run polling:

```sh
python3 pagerduty_auto_ack.py --env-file .env --watch --interval 30
```

## Live Mode

Run continuously and actually acknowledge matching incidents:

```sh
python3 pagerduty_auto_ack.py --env-file .env --watch --interval 30 --apply
```

Run once, useful from cron or another local scheduler:

```sh
python3 pagerduty_auto_ack.py --env-file .env --once --apply
```

Example cron entry for once-per-minute local polling:

```cron
* * * * * cd /Users/nithish/Documents/Pagerduty && /usr/bin/env python3 pagerduty_auto_ack.py --env-file .env --once --apply >> pagerduty-auto-ack.log 2>&1
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
