# Homebrew

The official project tap provides `pagerduty-oncall-ack` for macOS and Linux. The Homebrew package includes both the `pd-auto-ack` CLI and the optional terminal dashboard.

## Install

```sh
brew install nithishduda-ai/tap/pagerduty-oncall-ack
pd-auto-ack --version
```

Homebrew adds the project tap automatically when you use the full formula name. You do not need to install Python, `pipx`, or Textual separately.

## Configure and Run

Create and edit the same local configuration used by every installation method:

```sh
pd-auto-ack init --env-file ~/.pd-auto-ack.env
nano ~/.pd-auto-ack.env
```

Validate the configuration before enabling live acknowledgement:

```sh
pd-auto-ack doctor --env-file ~/.pd-auto-ack.env
pd-auto-ack check --env-file ~/.pd-auto-ack.env
```

Open the terminal dashboard:

```sh
pd-auto-ack tui --env-file ~/.pd-auto-ack.env
```

See the [quick start](quick-start.md) for dry-run and live-mode commands.

## Upgrade

```sh
brew update
brew upgrade pagerduty-oncall-ack
pd-auto-ack --version
```

## Uninstall

```sh
brew uninstall pagerduty-oncall-ack
brew untap nithishduda-ai/tap
```

The `brew untap` command is optional. Uninstalling the formula does not remove `~/.pd-auto-ack.env`; delete that file separately only when you no longer need its PagerDuty configuration.

## Switching from pipx

Use one installation method at a time so that your shell does not find an older copy of `pd-auto-ack` first:

```sh
pipx uninstall pagerduty-oncall-ack
brew install nithishduda-ai/tap/pagerduty-oncall-ack
which pd-auto-ack
pd-auto-ack --version
```

If `which pd-auto-ack` still points to an unexpected location, start a new shell and run the command again.

## Formula Source

The formula is maintained in the public [nithishduda-ai/homebrew-tap](https://github.com/nithishduda-ai/homebrew-tap) repository. Homebrew installs the released package from PyPI and verifies its checksum before installation.
