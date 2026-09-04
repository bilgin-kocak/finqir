# Contributing to FinQIR

Thank you for helping build an open, auditable quantum-finance toolkit.

## Development setup

```bash
git clone https://github.com/bilgin-kocak/finqir.git
cd finqir
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test,dev,docs]"
```

On Windows, activate the environment with `.venv\Scripts\activate`.

## Before opening a pull request

Run the relevant focused tests while developing, then run:

```bash
python -m unittest discover -s test -v
python -m black --check finqir test tools docs
python -m pylint --persistent=n -rn finqir test tools
python -m mypy finqir test tools
python tools/verify_headers.py finqir test tools
env LC_ALL=C LANG=C sphinx-build -E -a -b html docs docs/_build/html -W -T --keep-going
python -m build
python -m twine check dist/*
```

Every behavioral change needs tests. User-facing changes also need updated
documentation and a release note under `releasenotes/notes/`.

## Style and API principles

- Use Black with a maximum line length of 100 characters.
- Use Google-style docstrings for public APIs.
- Keep financial concepts identifiable through mapping and compilation.
- Prefer immutable models, deterministic output, and explicit validation.
- Do not claim financial performance or quantum advantage without reproducible evidence.
- Preserve inherited copyright and Apache-2.0 notices in derived files.

## Pull requests

Keep pull requests focused and explain the financial and quantum-computing
impact. Include the commands used to verify the change. By participating, you
agree to follow the project [Code of Conduct](CODE_OF_CONDUCT.md).
