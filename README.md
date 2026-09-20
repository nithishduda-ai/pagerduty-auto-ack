# PagerDuty Auto-Ack

`pagerduty-auto-ack` installs the `pd-auto-ack` CLI. It acknowledges PagerDuty incidents only when the configured user is currently on call.

It is intentionally narrow:

- Checks whether the user is on call.
- Finds only `triggered` incidents assigned to that user.
- Acknowledges those incidents.
- Does not resolve, reassign, rename, or add notes to incidents.

## Install

Recommended install uses `pipx`, which keeps CLI tools in isolated Python environments.

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

Install the CLI:

```sh
pipx install git+https://github.com/nithishduda-ai/pagerduty-auto-ack.git
pd-auto-ack --version
```

Upgrade an existing install:

```sh
pipx upgrade pagerduty-auto-ack
```

## Quick Start

Create a starter config file:

```sh
pd-auto-ack init --env-file ~/.pd-auto-ack.env
nano ~/.pd-auto-ack.env
```

Validate configuration and PagerDuty access:

```sh
pd-auto-ack doctor --env-file ~/.pd-auto-ack.env
pd-auto-ack check --env-file ~/.pd-auto-ack.env
```

Run one dry-run cycle:

```sh
pd-auto-ack run --env-file ~/.pd-auto-ack.env --once
```

Run continuously in dry-run mode:

```sh
pd-auto-ack run --env-file ~/.pd-auto-ack.env --watch --interval 30
```

Run continuously in live mode:

```sh
pd-auto-ack run --env-file ~/.pd-auto-ack.env --watch --interval 30 --apply
```

## Required PagerDuty Access

The PagerDuty token needs permissions equivalent to:

- `oncalls.read`
- `incidents.read`
- `incidents.write`

## Documentation

- [Documentation site](https://nithishduda-ai.github.io/pagerduty-auto-ack/)
- [Quick start](docs/quick-start.md)
- [Configuration](docs/configuration.md)
- [Command reference](docs/commands.md)
- [How it works](docs/how-it-works.md)
- [Rollout, rate limits, and operations](docs/rollout.md)
- [Local development](docs/development.md)

## Security

Please report suspected vulnerabilities through GitHub's private vulnerability reporting flow from the repository Security tab. See [SECURITY.md](SECURITY.md).

## Safety Summary

The CLI only acknowledges incidents when all of these are true:

- the configured user is currently on call
- the incident is `triggered`
- the incident is assigned to that user

Dry-run mode is the default. Live mode requires `--apply` or `PD_APPLY=true`.

## API References

The implementation follows PagerDuty's REST API reference and published OpenAPI schema:

- <https://developer.pagerduty.com/api-reference/>
- <https://github.com/PagerDuty/api-schema>
