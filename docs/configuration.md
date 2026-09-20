# Configuration

Configuration is loaded from an env file passed with `--env-file`.

```sh
pd-auto-ack init --env-file ~/.pd-auto-ack.env
```

The generated file contains placeholders and is created with private file permissions where supported.

## Required Values

- `PD_API_TOKEN`: PagerDuty REST API token.
- `PD_USER_ID`: PagerDuty user ID for the person who should be checked as on call.
- `PD_FROM_EMAIL`: email of a valid PagerDuty user. PagerDuty requires this when updating incidents.

`PD_USER_ID` and `PD_FROM_EMAIL` can often be inferred from `/users/me` when the API token belongs to the same user. Explicit values are still recommended for long-running jobs.

## Recommended Values

- `PD_APPLY=false`: keeps dry-run mode as the default.
- `PD_POLL_SECONDS=30`: polling interval for `--watch` mode.

## Optional Filters

- `PD_SERVICE_IDS`: comma-separated service ID allowlist.
- `PD_TEAM_IDS`: comma-separated team ID allowlist.
- `PD_ESCALATION_POLICY_IDS`: comma-separated escalation policy ID allowlist for on-call checks.
- `PD_SCHEDULE_IDS`: comma-separated schedule ID allowlist for on-call checks.

Filters are optional, but useful for larger accounts.

## Optional Tuning

- `PD_REQUEST_TIMEOUT_SECONDS`: PagerDuty API request timeout.
- `PD_MAX_PAGES`: safety limit for paginated PagerDuty list calls.

## Where To Get Values

`PD_API_TOKEN` is a PagerDuty REST API token. Create one in PagerDuty or ask an admin to create one with:

- `oncalls.read`
- `incidents.read`
- `incidents.write`

`PD_FROM_EMAIL` is the email address you use in PagerDuty.

`PD_USER_ID` is your PagerDuty user ID. If the token belongs to you, you can leave the generated placeholder for a first test:

```sh
PD_USER_ID=PAGERDUTY_USER_ID
```

Then run:

```sh
pd-auto-ack check --env-file ~/.pd-auto-ack.env
```

The command confirms which PagerDuty user the token belongs to.
