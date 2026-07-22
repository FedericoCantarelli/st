# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`st` is a CLI (built with `click`) that turns a directory tree of icon files (SVG/PNG, e.g. exported from an icon library like GCP's) into a [Structurizr](https://structurizr.com/) DSL theme JSON file. The tool name in commands is `st`.

## Commands

This project uses `uv` for dependency management and packaging.

```bash
# Install dependencies / sync the venv
uv sync

# Run the CLI locally
uv run st --help
uv run st version
uv run st theme clean <path> [--output <dir>] [--rules <rules.st>]
uv run st theme create <path> --name "My Theme" [--description ...] [--color ...] [--rules <rules.st>]

# Lint / format (ruff config lives in ruff.toml at repo root)
uv run ruff check .
uv run ruff format .
```

There is currently no test suite in the repository.

## Architecture

The CLI has two layers:

- **`src/st/commands/`** — click command groups/entry points (`theme.py`, `version.py`). These parse CLI args, read/write files, and call into `st.core` and `st.utils`. `src/st/__init__.py` wires everything into the `main` click group.
- **`src/st/core/`** — the domain model:
  - `model.py` defines `IconElement` (wraps a single icon file on disk), `ThemeElement` (a single entry in the exported theme), and `Theme` (the collection of `ThemeElement`s, serialized to `theme.json`). `go_through_fs_tree()` recursively walks an input directory and returns a flat list of `IconElement`s, skipping dotfiles.
  - `rule_parser.py` implements the `.st` rules DSL used to filter which `IconElement`s a command processes (see below).
  - `theme_attributes.py` holds the `Border` and `Shape` enums that mirror Structurizr DSL's allowed values.
- **`src/st/utils/`** — cross-cutting helpers: `str_utils.py` (case conversion, string similarity metrics), `colors.py` (WCAG contrast ratio calculations), `pretty_print.py` (colored terminal output helpers: `print_ok`, `print_warning`, `print_fail`, `print_done`, `print_verbose`), `config.py` (INI config at `~/.st/config.ini`, with env vars > config file > defaults as the intended precedence).

### The two `theme` subcommands

- **`clean`**: normalizes a raw icon export (e.g. from a design tool) into a directory of `snake_case`-named files/dirs, ready for `create`. Directory names get flattened/snake_cased per the naming convention below; hidden files/dirs are skipped.
- **`create`**: walks a (typically already-cleaned) icon directory via `go_through_fs_tree`, builds one `ThemeElement` per `.svg` found (tag/icon name derived from the file's parent directory and filename), and exports a `theme.json` compatible with Structurizr's custom theme format.

Both subcommands accept `--rules <path>` to filter the walked `IconElement`s through a rules file before processing them (via `filter_elements()` in `rule_parser.py`).

### Rules DSL (`rule_parser.py`)

An optional `--rules` file (conventionally named `rules.st`, see `example/*.st`) is a sequence of `INCLUDE(<expr>)` / `EXCLUDE(<expr>)` statements. `<expr>` is a boolean expression (`AND`, `OR`, `NOT`, parentheses) over two leaf predicate forms:

- `ATTRIBUTE=value` — glob-matches (`*`, `?`, `[...]`, hand-rolled in `glob_match()`, no `fnmatch` dependency) `value` against an `IconElement` attribute.
- `CONTAIN(ATTRIBUTE, "substring")` — literal substring test against an attribute.

`ATTRIBUTE` is one of `NAME`, `EXTENSION`, `PATH` (registered in `_ATTRIBUTE_GETTERS` — add an entry there to expose a new `IconElement` attribute to rules). Matching is always case-sensitive. Example:

```
INCLUDE(NAME="file_name" AND EXTENSION=".svg")
EXCLUDE(CONTAIN(PATH, "Unique Icons"))
```

**Decision rule**: an element is dropped if it matches any `EXCLUDE` expression, *unless* it also matches an `INCLUDE` expression — `INCLUDE` overrides `EXCLUDE` on conflict. An element matching neither is kept. If a rules file has `INCLUDE` statements but no `EXCLUDE` statements, `INCLUDE` acts as a standalone whitelist: only elements matching an `INCLUDE` expression are kept. This is implemented as a hand-written lexer (`_tokenize`) + recursive-descent parser (`_Parser`) producing a Composite/Interpreter-pattern expression tree (`AttributeExpr`, `ContainExpr`, `AndExpr`, `OrExpr`, `NotExpr`), evaluated per-element by `RuleSet.keep()`.

### Naming convention (from README)

Given a top-level input directory containing first-level subdirectories (e.g. `Category Icons/`, `Unique Icons/`), exported/cleaned icon filenames follow:

```
<prefix>_<first_level_dir>_<snake_case_filename>
```

`<prefix>` is set via `--prefix`/derived per command, `<first_level_dir>` is the snake_cased first-level directory name, and `<snake_case_filename>` is the original filename snake_cased with non-alphanumeric characters stripped. This logic lives in `IconElement._output_file_name` and `IconElement.get_theme_name`/`get_theme_tag` in `core/model.py`.

## Code style

- Ruff is configured (`ruff.toml`) with an extensive lint rule set including `D` (pydocstyle, Google convention) and `T20` (no `print` outside of the dedicated `pretty_print` helpers — use `print_ok`/`print_warning`/`print_fail`/`print_done`/`print_verbose` instead of bare `print()`).
- Imports: one import per line, sorted (`isort` with `force-single-line = true`), and relative imports are banned (`ban-relative-imports = "all"`) — always import via the full `st.<subpackage>.<module>` path.
- Quote style is double quotes; line length is 88.
