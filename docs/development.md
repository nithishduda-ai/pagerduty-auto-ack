# Local Development

## Install From Checkout

```sh
python3 -m pip install .
```

Or with `pipx`:

```sh
pipx install .
```

Run without installing:

```sh
PYTHONPATH=src python3 -m pagerduty_oncall_ack --help
```

## Tests

Run tests:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests
```

Compile-check:

```sh
PYTHONPYCACHEPREFIX=/private/tmp/pagerduty-pycache python3 -m compileall -q src tests
```
