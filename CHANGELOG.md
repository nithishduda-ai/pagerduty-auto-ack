# Changelog

All notable user-facing changes to `pagerduty-auto-ack` are documented here.

## 0.3.0 - 2026-09-20

First published release.

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

