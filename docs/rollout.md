# Rollout, Rate Limits, And Operations

## API Call Volume

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

The incident list call requests open incidents using `statuses[]=triggered` and `statuses[]=acknowledged`, but write calls are made only for triggered incidents. List calls are paginated with `limit=100`. If PagerDuty returns more pages, the CLI will make additional page requests up to `PD_MAX_PAGES`, which defaults to `10`.

For a team rollout, total call volume scales linearly with the number of people running the tool. For example, 50 people running at a 30 second interval while not on call is about 100 PagerDuty API calls per minute. If 5 of those people are on call, add about 10 more calls per minute for incident checks.

## Rate Limits

PagerDuty REST API responses include rate-limit headers such as `ratelimit-limit`, `ratelimit-remaining`, and `ratelimit-reset`, and PagerDuty may return HTTP `429` when rate limited.

Reference: <https://support.pagerduty.com/main/docs/rest-api-rate-limits>

## Recommended Rollout Practices

- Prefer one user token per person instead of sharing one account-wide token.
- Use the minimum required permissions: `oncalls.read`, `incidents.read`, and `incidents.write`.
- Keep `PD_APPLY=false` until dry-run output is trusted.
- Increase `PD_POLL_SECONDS` to `60` or `120` for broad team rollouts if near rate limits.
- Use optional filters like `PD_SERVICE_IDS`, `PD_TEAM_IDS`, `PD_ESCALATION_POLICY_IDS`, and `PD_SCHEDULE_IDS` to reduce the incidents and on-call data queried.

## Cron Example

Run once per minute in live mode:

```cron
* * * * * /usr/bin/env pd-auto-ack run --env-file ~/.pd-auto-ack.env --once --apply >> ~/pagerduty-oncall-ack.log 2>&1
```
