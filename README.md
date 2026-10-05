# Indico Toolkit for Intake and Insights

**This repository contains software that is not officially supported by Indico. It may
  be outdated or contain bugs. The operations it performs are potentially destructive.
  Use at your own risk.**

Classes, functions, and abstractions for building workflows and workspaces using the Indico platform.

- [MicroClient](https://github.com/IndicoDelivery/indico-toolkit-python/blob/main/src/indico_toolkit/microclient.py)
  class that provides async methods for making GraphQL, REST, and Storage calls.
  Includes authentication and best-practices retry. Can be used as a single-file drop-in
  module with few dependencies for other projects.
- [ORM](https://github.com/IndicoDelivery/indico-toolkit-python/blob/main/src/indico_toolkit/orm/__init__.py)
  and [Router](https://github.com/IndicoDelivery/indico-toolkit-python/blob/main/src/indico_toolkit/router/__init__.py)
  classes for writing Insights custom agents using declarative Data Classes and
  automatic load and save of instance attributes.
- [Polling](https://github.com/IndicoDelivery/indico-toolkit-python/blob/main/src/indico_toolkit/polling/__init__.py)
  classes that implement best-practices polling behavior for Intake Auto Review and
  Downstream processes. Easily plug in business logic without the boilerplate.
- [Result File](https://github.com/IndicoDelivery/indico-toolkit-python/blob/main/src/indico_toolkit/results/__init__.py)
  and [Etl Output](https://github.com/IndicoDelivery/indico-toolkit-python/blob/main/src/indico_toolkit/etloutput/__init__.py)
  Data Classes that parse standard Intake JSON output into idiomatic, type-safe Python
  dataclasses.

...and more in the [Examples](https://github.com/IndicoDelivery/indico-toolkit-python/tree/main/examples) folder.


## Installation

**Indico Toolkit uses semantic versioning.**

Indico Toolkit versions do not match the Intake or Insights versions they are compatible with.
See the [Changelog](https://github.com/IndicoDelivery/indico-toolkit-python/blob/main/CHANGELOG.md)
for the minimum platform version required by each toolkit version.

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
