# FinQIR Independent Package Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Convert the existing fork into an independently installable `finqir` Python distribution and import namespace without implementing the later structured-finance feature roadmap.

**Architecture:** Preserve the inherited Apache-2.0 implementation as the initial compatibility foundation, but publish it under the distinct `finqir` distribution and module namespace. Consolidate package metadata in `pyproject.toml`, make CI run in the independent repository, and publish tagged releases through PyPI Trusted Publishing.

**Tech Stack:** Python 3.10+, setuptools, build, twine, unittest, GitHub Actions, Qiskit 2.5.2+.

**Spec:** `docs/superpowers/specs/2026-09-04-structured-quantum-finance-design.md`

## Global Constraints

- Distribution name and import namespace are both `finqir`.
- Initial version is `0.1.0`.
- Support Python `>=3.10` and Qiskit `>=2.5.2,<3`.
- Keep Apache-2.0 licensing and inherited copyright notices intact.
- Do not provide a `qiskit_finance` compatibility namespace because it would collide with the official package.
- Publishing uses GitHub Actions OIDC Trusted Publishing; no long-lived PyPI token is stored.
- The structured portfolio/compiler APIs remain roadmap work and are not falsely advertised as implemented.

---

### Task 1: Define and test the independent package identity

**Files:**
- Create: `test/test_package_identity.py`
- Rename: `qiskit_finance/` to `finqir/`
- Modify: imports in `finqir/`, `test/`, documentation, and tooling

**Interfaces:**
- Produces: `import finqir`, `finqir.__version__`, and no local `qiskit_finance` package.

- [x] Write a test that imports `finqir`, verifies the public version, and confirms package discovery excludes `qiskit_finance`.
- [x] Run the test and observe failure because `finqir` does not exist.
- [x] Rename the package directory and replace internal/test/documentation imports.
- [x] Run the identity test and affected unit tests.

### Task 2: Modernize build metadata

**Files:**
- Modify: `pyproject.toml`
- Delete: `setup.py`
- Modify: `MANIFEST.in`
- Modify: `requirements.txt`
- Modify: `requirements-dev.txt`
- Modify: `tox.ini`
- Modify: `Makefile`

**Interfaces:**
- Produces: standards-based `finqir==0.1.0` wheel and source distribution with optional dependency groups.

- [x] Add a packaging test that builds a wheel and inspects its distribution name and contents.
- [x] Run it against the old metadata and observe the identity failure.
- [x] Move metadata to `[project]` and setuptools configuration in `pyproject.toml`.
- [x] Build and validate both artifacts with `python -m build` and `twine check`.

### Task 3: Rebrand user-facing documentation and project automation

**Files:**
- Modify: `README.md`
- Modify: `docs/`
- Modify: `.github/actions/`
- Modify: `.github/workflows/main.yml`
- Modify: `.github/workflows/deploy-code.yml`
- Modify: GitHub templates and contributor documentation where they identify the project

**Interfaces:**
- Produces: accurate `pip install finqir` documentation and independent CI/release behavior.

- [x] Replace FinQIR project identity while retaining references that describe upstream history or dependencies.
- [x] Remove the upstream-owner-only CI guard.
- [x] Build releases with `python -m build` and publish through the existing OIDC permission boundary.
- [x] Scan tracked files for stale package/import/project URLs and classify intentional historical references.

### Task 4: Verify, commit, and integrate

**Files:**
- Verify all changed files and generated distributions; generated `dist/` files remain untracked.

**Interfaces:**
- Produces: a committed FinQIR foundation merged into local `main`.

- [x] Install the wheel into a clean virtual environment.
- [x] Verify `import finqir`, distribution metadata, and representative public imports.
- [x] Run the full available unit suite and formatting/package checks.
- [x] Commit the conversion on `docs/structured-finance-design`.
- [x] Merge the branch into local `main` as explicitly requested.
- [x] Re-run package identity and build verification on the merged result.
