# Releasing

Use this checklist for every public release.

## Release Checklist

1. Update the version in `pyproject.toml`.
2. Update `VERSION` in `src/pagerduty_auto_ack/cli.py`.
3. Update `CHANGELOG.md` with user-facing changes.
4. Run local checks:

   ```sh
   python3 -m unittest discover -s tests
   python3 -m compileall -q src pagerduty_auto_ack.py tests
   ```

5. Commit and push the release changes.
6. Tag the release:

   ```sh
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

7. Create a GitHub Release using the matching changelog entry.
8. Confirm GitHub CI, CodeQL, Pages, and Dependabot jobs pass.

## Release Notes

Release notes should tell users:

- what changed
- whether they need to upgrade
- whether behavior changed
- whether configuration changed
- whether any safety behavior changed

For this project, always call out acknowledgement behavior explicitly. Users should never have to guess what the CLI will update in PagerDuty.

