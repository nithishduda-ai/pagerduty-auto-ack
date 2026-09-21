# Quick Start

## Install

Recommended install uses `pipx`.

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

Install from PyPI:

```sh
pipx install pagerduty-oncall-ack
pd-auto-ack --version
```

Install with the optional terminal dashboard:

```sh
pipx install "pagerduty-oncall-ack[tui]"
pd-auto-ack tui --env-file ~/.pd-auto-ack.env
```

For an existing `pipx` install:

```sh
pipx inject pagerduty-oncall-ack textual
```

Upgrade:

```sh
pipx upgrade pagerduty-oncall-ack
```

If you installed an older release when the package was named `pagerduty-auto-ack`, reinstall once under the new package name:

```sh
pipx uninstall pagerduty-auto-ack
pipx install pagerduty-oncall-ack
```

The CLI command remains `pd-auto-ack`.

## Create Config

Create a starter config file:

```sh
pd-auto-ack init --env-file ~/.pd-auto-ack.env
```

Edit it:

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

Keep `PD_APPLY=false` until dry-run output looks right.

## Validate

Check local config parsing:

```sh
pd-auto-ack doctor --env-file ~/.pd-auto-ack.env
```

Check PagerDuty access and current state:

```sh
pd-auto-ack check --env-file ~/.pd-auto-ack.env
```

Example healthy output:

```text
PagerDuty API token is valid for user@example.com.
On call now: EU Support Escalation Policy / EU Support Escalation / level 1
Open incidents assigned to user: 0
Triggered incidents eligible for acknowledgement: 0
```

That means the token works, the CLI identified the PagerDuty user, the user is currently on call, and there are no open incidents assigned to them right now.

## Run

One dry-run cycle:

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

Optional terminal dashboard:

```sh
pd-auto-ack tui --env-file ~/.pd-auto-ack.env
```
