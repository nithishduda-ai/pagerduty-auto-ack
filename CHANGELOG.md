# Changelog

All notable user-facing changes to `pagerduty-oncall-ack` are documented here.

## Unreleased

## 0.6.0 - 2026-09-21

### Added

- Added a Homebrew tap for macOS and Linux installation, including terminal dashboard support.
- Added Homebrew install, upgrade, uninstall, and troubleshooting documentation.

### Removed

- Removed legacy compatibility wrappers from the source distribution.

## 0.5.0 - 2026-09-21

### Added

- Added an optional Textual-powered `pd-auto-ack tui` terminal dashboard.

## 0.4.1 - 2026-09-21

### Changed

- Updated install docs to use the published PyPI package.
- Removed maintainer-only publishing and release pages from the public documentation site.
- Updated PyPI project links to point users to documentation, changelog, issue reporting, and the security policy.

## 0.4.0 - 2026-09-20

### Changed

- Standardized the project and install package name as `pagerduty-oncall-ack`.
- Standardized the Python import package as `pagerduty_oncall_ack`.
- Kept the CLI command as `pd-auto-ack`.
- Updated repository, documentation, GitHub Pages, and release links for the new project name.
- Existing `pd-auto-ack` env files continue to work.

## 0.3.0 - 2026-09-20

First published CLI release.

### Added

- `pd-auto-ack` CLI for local PagerDuty incident acknowledgement.
- `init`, `doctor`, `check`, and `run` commands.
- Dry-run mode by default.
- Live acknowledgement mode with `--apply` or `PD_APPLY=true`.
- On-call check before any incident acknowledgement.
- Open incident display for incidents assigned to the configured user.
- Triggered-only acknowledgement behavior.
- Incident status and PagerDuty URL in CLI incident output when available.
- Optional filters for services, teams, escalation policies, and schedules.
- Local env-file configuration with private `0600` permissions where supported.
- GitHub Pages documentation site.
- CI, CodeQL, Dependabot, secret scanning, and security policy for the public repository.

### Safety

- The CLI acknowledges only incidents that are `triggered`, assigned to the configured user, and only while that user is currently on call.
- Already `acknowledged` incidents are shown for awareness but are not updated.
- The CLI does not resolve, reassign, rename, or add notes to incidents.

### Documentation

- Added quick start, configuration, command reference, rollout, and development guides.
- Added API call volume and rate limit guidance for team rollouts.
- Added first-time `pipx` installation instructions for macOS and Linux.
