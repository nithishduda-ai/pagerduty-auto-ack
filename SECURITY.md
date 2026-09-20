# Security Policy

## Supported Versions

This project is early-stage. Security fixes are applied to the latest version on the `main` branch.

## Reporting a Vulnerability

Use GitHub's private vulnerability reporting flow from the repository Security tab.

Please do not open a public issue for suspected secrets, token exposure, authentication bypasses, or behavior that could acknowledge incidents unexpectedly.

When reporting, include:

- affected version or commit
- steps to reproduce
- expected behavior
- observed behavior
- any relevant logs with secrets removed

## Token Handling

`pd-auto-ack` reads PagerDuty tokens from local environment variables or an env file. Do not commit real `.env` files or PagerDuty API tokens.

Use a token with only the minimum permissions needed:

- `oncalls.read`
- `incidents.read`
- `incidents.write`

