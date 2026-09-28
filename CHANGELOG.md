# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [v10.0.0] - 2026-10-01

Minimum Platform Version: `Intake v7.2`, `Insights v2.5`

### Added

- Added `orm`, `microclient`, and `router` modules for Insights.
- Added `asyncstdlib`, `httpx`, and `tenacity` as package dependencies.

### Changed

- Migrated from `poetry` to `uv` for package management.
    - Moved source code into `src/` directory.
- Migrated from `black` to `ruff` for code formatting.
    - Reformatted codebase.
- Migrated from `mypy` to `ty` for static type checking.
    - Corrected some type annotations and object types.
- Updated GitHub Actions workflow.
- Made `indico_toolkit.__version__` use pyproject.toml project metadata.
- Replaced `indico-client` with `microclient` for `polling` API calls.

### Fixed

- Fixed some unit test assertions.

### Removed

- Removed `auto_review`, `errors`, `indico_wrapper`, `metrics`, `ocr`, `pipelines`, `snapshots`, and `structure` modules.
- Removed associated units tests.
- Removed `indico-client` dependency.
- Support for EOL Python 3.10.
- Removed Python <=3.10 type hint quoting.


## [v7.2.3] - 2026-01-30

Minimum Platform Version: `Intake v7.2`

### Added

- Filter out deleted and retrieved submissions when polling in `AutoReviewPoller` and
  `DownstreamPoller`. This makes submissions that can't be processed automatically drop
  off (deleted submsissions), and provides an API-based mechanism to force a
  problematic submission to drop off Auto Review without failing it in the DB
  (marking retrieved).
- Normalize edge cases where Form Extraction bounding boxes are `float`s.
- Support idiomatic `copy.deepcopy()` and `copy.replace()` of `Prediction`s and
  `PredicitonList`s via `__deepcopy__` and `__replace__`.

### Changed

- Simplify type annotations for `retry()` decorator.

### Removed

- `Prediction.copy()` in favor of `copy.deepcopy()` and `copy.replace()`.


## [v7.2.2] - 2025-10-14

Minimum Platform Version: `Intake v7.2`

### Added

- Parse table spans from ETL Output as `Table.spans`.
- `NULL_CELL`, `NULL_RANGE`, `NULL_TABLE`, and `NULL_TOKEN` constants.
- Document Extraction attributes for assigning tokens, tables, and cells from OCR:
    - `DocumentExtraction.tokens`, `DocumentExtraction.tables`, `DocumentExtraction.cells`
- Document Extraction convenience properties for singular token, table, and cell access:
    - `DocumentExtraction.token`, `DocumentExtraction.table`, `DocumentExtraction.cell`
- `PredictionList.assign_ocr(etl_outputs, tokens=True, tables=True)` method.
- Custom `__hash__` methods for tables and cells to speed up `.groupby(...)`.
- Prediction `.copy()` methods that only copy mutable state.

### Changed

- Move `Box` and `Span` from results to etloutput to avoid circular imports.
  (Both can still be imported from either module.)
- Return `NULL_TOKEN` instead of raising an exception from `EtlOutput.token_for(span)`.
- Rewrite table cell lookup `EtlOutput.table_cells_for(span)` using a fast, span-based,
  binary search algorithm that can return multiple overlapped table cells.

### Removed

- Custom `results` and `etloutput` error classes that are nearly never used.
  (Replaced with idiomatic Python error classes.)


## [v7.2.1] - 2025-09-09

Minimum Platform Version: `Intake v7.2`

### Fixed

- Account for row spans and column spans in ETL output tables.
  Affects `Table.from_dict()`, `Range.from_dict()`, and `EtlOutput.table_cell_for()`.
- Narrow `AutoReviewed.changes` type to v3 result file changes,
  as that's the only version supported by `results` and `polling` modules.


## [v7.2.0] - 2025-06-17

Minimum Platform Version: `Intake v7.2`

### Added

- Unified support for `dict`, JSON `str`, and JSON `bytes` as loadable types in
  `results.load()`, `results.load_async()`, `etloutput.load()`, and
  `etloutput.load_async()`.

### Changed

- Rename `model`, `ModelGroup`, and `ModelGroupType` to `task`, `Task`, and `TaskType`
  in the `results` module.
- Table OCR is automatically loaded when present
  (`AutoReviewPoller(..., load_tables=True)` and `etloutput.load(..., tables=True)` are
  now the default).

### Removed

- v1 result file support and code paths in the `results` module.
- v1 ETL output support and code paths in the `etloutput` module.
- IPA 6.X support and edge cases in the `results` and `etloutput` modules.


## [v6.14.2] - 2025-05-08

Minimum Platform Version: `Intake v6.14`

### Added

- Support for imported models using IPA 7.2 `component_metadata` section.
- Parse and preserve full span information for `Unbundling` predictions.
- `group = next(group)` idiom.

### Removed

- `AutoPopulator`, `CustomOcr`, `Datasets`, `DocExtraction`, `Reviewer` classes.

### Fixed

- Mypy configuration.


## [v6.14.1] - 2025-03-20

Minimum Platform Version: `Intake v6.14`

### Changed

- Improve Poetry and Poe configuration.
- Update more attributes when prediction text changes to avoid TAK normalization issues.


## [v6.14.0] - 2025-03-10

Minimum Platform Version: `Intake v6.14`

### Added

- `results` module.
- `etloutput` module.
- Async coroutine support in the `retry` decorator.

### Changed

- Switch to Poetry for packaging and dependency management.


## v6.1.0 - 2024-05-06

### Removed

- Staggered loop support.
- Highlighting support.


## v6.0.1 - 2023-11-22

### Added

- Original filename to the workflow result object.


## v6.0.0 - 2023-10-30

This is the first major version release tested to work on Indico 6.X.

### Added

- Support for unbundling metrics.
- `Structure` class to support building out workflows, datasets, teach tasks, and
  copying workflows.

### Changed

- Refactor `AutoReview` to simplify setup.
- Replace `AutoClassifier` with `AutoPopulator` to make on-document classification
  model training simple. This class also includes a "copy_teach_task" method that is a
  frequently needed standalone method.
- Simplify `StaggeredLoop` implementation to inject labeled samples into a development
  workflow (deprecated previous version).


## v2.0.2 - 2022-08-31

### Added

- Support for staggered looped learning.
- Ground truth compare feature to compare a snapshot against model predictions and
  receive analytics.

### Changed

- Upgrade client to 5.1.4.
- Modify `IndioWrapper` class to work with Indico 5.x.
- Update `Snapshot` class to account for updated target spans.
- Update Add Model calls to align with 5.1.4 components.


## v2.0.1 - 2022-05-20

### Added

- Feature in `FileProcessing` class to read and return file as JSON.
- Feature in `Highlighter` class to redact and replace highlights with spoofed data.
- `Download` class to support downloading resources from an Indico Cluster.

### Changed

- Upgrade client to 5.1.3.
- Update SDK calls for Indico 5.x compatibility.

### Removed

- `FindRelated` class in `indico_wrapper`.


## v1.2.2 - 2022-03-03

### Added

- Feature in `Positioning` class to calculate overlap between two bounding boxes on the
  same page.

### Changed

- Update metrics plot to order ascending based on latest model.

### Fixed

- Optional dependencies to support M1 installation.


## v1.2.0 - 2022-01-06

### Added

- Distance measurements in the prediction `Positioning` class.
- Features on the `Extractions` class:
  - predictions that are removed by any method are saved in an attribute if they're
    needed for logs, etc.; get all text values for a particular label,
  - get most common text value for a particular label.
- Better exception handling for workflow submissions and more flexibility on format of
  what is returned (allows custom response JSON to avoid the `WorkflowResult` class).


## v1.1.2 - 2021-12-06

### Added

- Update functionality for large dataset creation.
- Batch options allow for more reliable dataset uploads.


## v1.1.1 - 2021-12-06

### Added

- Ability to include metadata with highlighter.
- Ability to split large snapshots into smaller files.


## v1.0.8 - 2021-11-15

### Added

- Line plot for number of samples in metrics class.

### Changed

- Update `Highlighting` class with new flexibility and bookmarks replacing table of
  contents.


## v1.0.7 - 2021-11-09

### Added

- `Positioning` class to assist in relative prediction location validation.
- Number of samples labeled to metrics class.

### Removed

- Teach classes in `indico_wrapper`.


## v1.0.5 - 2021-09-21

### Added

- Classes for model comparison and model improvement.
- Plotting functionality for model comparison.


## v1.0.3 - 2021-08-16

### Added

- Find from questionnaire ID added to finder class.
- ModelGroupPredict support.
- Module to get metrics for all models in a group.
- Multi color highlighting and annotations for PDF highlighting.
- Staggered dataset upload feature for large doc datasets.
- Default retry functionality for certain API calls.
- Additional snapshot features.

### Fixed

- `wait` keyword argument added to submit review method.
- Better support for dataset creation / adding files to teach tasks.


## v1.0.2 - 2021-06-15

### Added

- PDF manipulation features.
- Support for classification predictions.

### Fixed

- Dependency installation.


## v1.0.1 - 2021-06-02

### Added

- Snapshot merging / manipulation.
- Class for highlighting extractions onto source PDFs and adding table of contents.

### Fixed

- Row Association now also sorting on 'bbtop'.


[v10.0.0]: https://github.com/IndicoDataSolutions/indico-toolkit-python/compare/v7.2.3...v10.0.0
[v7.2.3]: https://github.com/IndicoDataSolutions/indico-toolkit-python/compare/v7.2.2...v7.2.3
[v7.2.2]: https://github.com/IndicoDataSolutions/indico-toolkit-python/compare/v7.2.1...v7.2.2
[v7.2.1]: https://github.com/IndicoDataSolutions/indico-toolkit-python/compare/v7.2.0...v7.2.1
[v7.2.0]: https://github.com/IndicoDataSolutions/indico-toolkit-python/compare/v6.14.2...v7.2.0
[v6.14.2]: https://github.com/IndicoDataSolutions/indico-toolkit-python/compare/v6.14.1...v6.14.2
[v6.14.1]: https://github.com/IndicoDataSolutions/indico-toolkit-python/compare/v6.14.0...v6.14.1
[v6.14.0]: https://github.com/IndicoDataSolutions/indico-toolkit-python/tree/v6.14.0
