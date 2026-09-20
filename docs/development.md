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

Backward-compatible script wrapper:

```sh
python3 pagerduty_auto_ack.py --help
```

## Tests

Run tests:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests
```

Compile-check:

```sh
PYTHONPYCACHEPREFIX=/private/tmp/pagerduty-pycache python3 -m py_compile pagerduty_auto_ack.py src/pagerduty_oncall_ack/*.py src/pagerduty_auto_ack/*.py tests/*.py
```
