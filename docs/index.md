# pd-auto-ack

`pagerduty-oncall-ack` installs the `pd-auto-ack` CLI, a small local tool that acknowledges PagerDuty incidents only when the configured user is currently on call.

## Start Here

- [Quick start](quick-start.md)
- [Configuration](configuration.md)
- [Command reference](commands.md)
- [How it works](how-it-works.md)
- [Rollout, rate limits, and operations](rollout.md)
- [Local development](development.md)
- [Changelog](https://github.com/nithishduda-ai/pagerduty-oncall-ack/blob/main/CHANGELOG.md)
- [PyPI publishing](pypi-publishing.md)
- [Releasing](releasing.md)

## What It Does

- Checks whether the configured PagerDuty user is on call.
- Displays open incidents assigned to that user.
- Acknowledges only `triggered` incidents in live mode.
- Leaves all other incident fields alone.

Dry-run mode is the default. Live acknowledgement requires `--apply` or `PD_APPLY=true`.

## Install

```sh
pipx install git+https://github.com/nithishduda-ai/pagerduty-oncall-ack.git
pd-auto-ack --version
```

New to `pipx`? Use the [quick start](quick-start.md) for macOS and Linux setup steps.

## Repository

- [GitHub repository](https://github.com/nithishduda-ai/pagerduty-oncall-ack)
- [PagerDuty API reference](https://developer.pagerduty.com/api-reference/)
