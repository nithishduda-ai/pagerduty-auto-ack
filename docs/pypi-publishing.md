# PyPI Publishing

This project is prepared to publish `pagerduty-oncall-ack` to TestPyPI and PyPI using Trusted Publishing.

Trusted Publishing lets GitHub Actions publish without storing a long-lived PyPI API token in repository secrets.

## One-Time Setup

Create accounts if needed:

- <https://test.pypi.org/>
- <https://pypi.org/>

In both TestPyPI and PyPI, configure a pending Trusted Publisher for this project:

- PyPI project name: `pagerduty-oncall-ack`
- Owner: `nithishduda-ai`
- Repository: `pagerduty-oncall-ack`
- Workflow filename: `release.yml`
- Environment for TestPyPI: `testpypi`
- Environment for PyPI: `pypi`

The environment names must match the GitHub Actions workflow.

Confirm the GitHub repository has environments named:

- `testpypi`
- `pypi`

For the `pypi` environment, require manual approval before deployment so a real PyPI release cannot happen by accident.

## Publish To TestPyPI

Use this first for every packaging setup change.

1. Open the GitHub Actions tab.
2. Select `Publish Python Package`.
3. Choose `Run workflow`.
4. Set `repository` to `testpypi`.
5. Run the workflow.

After it passes, test install from TestPyPI:

```sh
pipx install --pip-args "--index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/" pagerduty-oncall-ack
pd-auto-ack --version
```

## Publish To PyPI

After TestPyPI works, publish to PyPI with one of these paths:

- Create a GitHub Release for the version.
- Or manually run `Publish Python Package` with `repository` set to `pypi`.

After it publishes, users can install with:

```sh
pipx install pagerduty-oncall-ack
pd-auto-ack --version
```

## Important Notes

- PyPI package versions are immutable. If publishing fails after upload, bump the version before retrying a changed package.
- `pagerduty-auto-ack` is already used on PyPI by another maintainer, so this project publishes as `pagerduty-oncall-ack`.
- The CLI command remains `pd-auto-ack`.
