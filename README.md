# Indico Toolkit for Intake and Insights

**This repository contains software that is not officially supported by Indico. It may
  be outdated or contain bugs. The operations it performs are potentially destructive.
  Use at your own risk.**

Classes, functions, and abstractions for building workflows and workspaces using the Indico platform.

- [Polling Classes](https://github.com/IndicoDataSolutions/indico-toolkit-python/tree/main/indico_toolkit/polling/__init__.py)
  that implement best-practices polling behavior for Intake Auto Review and Downstream
  processes. Easily plug in business logic without the boilerplate.
- [Result File](https://github.com/IndicoDataSolutions/indico-toolkit-python/blob/main/indico_toolkit/results/__init__.py)
  and [Etl Output](https://github.com/IndicoDataSolutions/indico-toolkit-python/blob/main/indico_toolkit/etloutput/__init__.py)
  Data Classes that parse standard Intake JSON output into idiomatic, type-safe Python dataclasses.

...and more in the [Examples](https://github.com/IndicoDataSolutions/indico-toolkit-python/tree/main/examples) folder.


## Installation

**Indico Toolkit uses semantic versioning.**

Indico Toolkit versions do not match the Intake or Insights versions they are compatible with.
See the [Changelog](./CHANGELOG.md) for the minimum required platform version for each toolkit version.

```bash
pip install indico-toolkit
poetry add indico-toolkit
uv add indico-toolkit
```


## Contributing

Indico Toolkit uses UV for package and dependency management.


### Setup

Clone the source repository with Git.

```bash
git clone git@github.com:IndicoDelivery/indico-toolkit-python.git
```

Install dependencies with UV.

```bash
uv sync
```

Formatting, linting, type checking, and tests are defined as
[Poe](https://poethepoet.natn.io/) tasks in `pyproject.toml`.

```bash
uv run poe {format,check,test,all}
```

Code changes or additions should pass `uv run poe all` before opening a PR.
