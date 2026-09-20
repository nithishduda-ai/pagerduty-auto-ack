# Changelog

All notable user-facing changes to `pagerduty-oncall-ack` are documented here.

## Unreleased

### Added

- Added GitHub Actions workflow for TestPyPI and PyPI publishing with Trusted Publishing.
- Added PyPI publishing setup documentation.

## 0.4.0 - 2026-09-20

### Changed

- Renamed the project and install package from `pagerduty-auto-ack` to `pagerduty-oncall-ack`.
- The rename avoids confusion with the existing `pagerduty-auto-ack` project name already published on PyPI by another maintainer.
- Renamed the primary Python import package from `pagerduty_auto_ack` to `pagerduty_oncall_ack`.
- Kept the CLI command as `pd-auto-ack`.
- Updated repository, documentation, GitHub Pages, and release links for the new project name.

### Compatibility

- Kept `pagerduty_auto_ack` as a compatibility import wrapper.
- Kept `pagerduty_auto_ack.py` as a compatibility script wrapper.
- Existing `pd-auto-ack` env files continue to work.

### Upgrade Notes

- Users who installed the older GitHub package name should reinstall once:

  ```sh
  pipx uninstall pagerduty-auto-ack
  pipx install git+https://github.com/nithishduda-ai/pagerduty-oncall-ack.git
  ```

## 0.3.0 - 2026-09-20

First published release under the previous `pagerduty-auto-ack` project name.

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
