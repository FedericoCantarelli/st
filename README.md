# Structurizr Theme Creator

A very stupid CLI to create Structurizr themes starting from icons.

<b>:warning: This is super work in progress. Will be completed soon.</b>

## Installation

`st` is not published to PyPI yet, so you can install it directly from the repository using [`uv`](https://docs.astral.sh/uv/).

```bash
# Clone the repository
git clone https://github.com/FedericoCantarelli/st.git
cd st

# Install dependencies and create the virtual environment
uv sync

# Run the CLI using uv
uv run st --help
```

If you want to have `st` command available directly from CLI, you can install the tool running the following command from the root of the repository:

```bash
uv tool install .
st --help
```

## Usage
The CLI is enterile based on `click` module. To get CLI help you can run the following command:

```bash
st --help
```

### Version
Print the CLI version

```bash
st version
```

### Clean
Normalizes a raw icon export (e.g. downloaded from an icon library) into a directory of `cleaned_string`-named files and directories, ready to be fed into `st theme create`. See [Naming Convention](#naming-convention-of-exported-icons) for how output names are derived. Hidden files and directories (starting with `.`) are <u>skipped</u>.

```bash
st theme clean <path> [--output <dir>] [--rules <rules.st>]
```

| Argument / Option | Required | Description |
| --- | --- | --- |
| `path` | Yes | Path to the input directory containing the raw icon export. Must exist. |
| `--output` | No | Name of the output directory, created as a sibling of `path`. Defaults to `cleaned`. |
| `--rules` | No | Path to a [rules file](#rules-dsl) used to filter which icons are processed. |

Example:

```bash
st theme clean ./raw-icons --output cleaned --rules ./rules.st
```

### Create

Create a theme from a cleaned icon directory, builds one theme element per `.svg` file found, and exports a `theme.json` compatible with Structurizr's [custom theme](https://docs.structurizr.com/dsl/themes) format. The output is written to a new directory named after `--name` (lowercased, spaces replaced with `-`), placed as a sibling of `path`.

```bash
st theme create <path> --name "My Theme" [--description <text>] [--rules <rules.st>]
```

| Argument / Option | Required | Description |
| --- | --- | --- |
| `path` | Yes | Path to the input directory containing the icons to include in the theme. Must exist. |
| `--name` | Yes | Name of the theme. Also used to derive the file prefix and tag prefix (see [Naming Convention](#naming-convention-of-exported-icons)). |
| `--description` | No | Description of the theme, written into `theme.json`. |
| `--rules` | No | Path to a [rules file](#rules-dsl) used to filter which icons are processed. |

Example:

```bash
st theme create ./cleaned --name "GCP Icons" --description "Google Cloud Platform icon theme" --rules ./rules.st
```

On first run, `st theme create` creates a default configuration file at `~/.st/config.ini` if one does not already exist. For the moment this file is unusued. TODO: implement default configuration options in this file.

## Naming Convention of Exported Icons

The naming convention of exported icons depends on the directory structure of the icons: exported icon names depend on the first-level nested directories inside the input directory.

Given the following project structure:
```text
# First level nested directories are `Category Icons` and `Unique Icons`
.
├── Category Icons
│   └── Agents
│       ├── PNG
│       │   └── Agents-512-color.png
│       └── SVG
│           └── Agents-512-color.svg
└── Unique Icons
    └── AlloyDB
        ├── PNG
        │   └── AlloyDB-512-color.png
        └── SVG
            └── AlloyDB-512-color.svg
```
The naming convention for the exported icons is the following:
```
<prefix>_<first_level_dir>_<snake_case_filename>
```
where `<prefix>` is computed from theme name, `<first_level_dir>` is the name of the first-level nested directory in snake case, and `<snake_case_filename>` is the filename converted to snake case, removing everything else that is not a character (number or non-alphanumeric characters).

For example the file `AlloyDB-512-color.png` will be exported as `gcp_unique_icons_alloydb_color.png` if the theme name is `Google Cloud Platform`.

Only the top-level directory (one level inside the `--path` folder) is used for the naming convention.

For `st theme create`, the `--name` you pass also drives two additional prefixes:
- **Tag prefix**: used to prefix the Structurizr element tag (e.g. `GCP - Category - Agents`). If the theme name has more than two "eligible" words (longer than 2 characters), the prefix is the initials of those words; otherwise it's the whole name in snake case.
- **File prefix**: same derivation logic, used to prefix the icon file name and the theme's output directory.

## Rules DSL
Both `st theme clean` and `st theme create` accept an optional `--rules <path>` argument pointing to a rules file (conventionally named `rules.st`). Rules let you filter which icons get processed without having to restructure your input directory. TODO: eventually this can become a `.txt` for the mental health of everybody.

A rules file is a sequence of `INCLUDE(<expr>)` / `EXCLUDE(<expr>)` statements, one or more per file. `<expr>` is a boolean expression built from `AND`, `OR`, `NOT`, parentheses, and two kinds of leaf predicates:

- `ATTRIBUTE=value` — glob-matches `value` against an icon attribute. Supports `*` (any sequence of characters, including none), `?` (any single character), and `[...]` / `[!...]` character classes (with `-` for ranges, e.g. `[a-z]`).
- `CONTAIN(ATTRIBUTE, "substring")` — true if the attribute's value contains `substring` as a literal substring.

`ATTRIBUTE` is one of:

| Attribute | Description |
| --- | --- |
| `NAME` | The icon's file name without its extension. |
| `EXTENSION` | The icon's file extension, including the leading dot (e.g. `.svg`). |
| `PATH` | The icon's full path, as a POSIX-style string. |

Matching is **case-sensitive**. Values are written either as bare words or quoted strings (`'...'` or `"..."`); quoting is required for values containing spaces or reserved characters. This set of attributes is meant to be extensible and will be expanded (hopefully) in future versions of the CLI to allow more specific rules.

### Decision rule

An icon is dropped if it matches any `EXCLUDE` expression, unless it also matches an `INCLUDE` expression. Thus `INCLUDE` always overrides `EXCLUDE` on conflict. Default is keep: if an icon matches neither an `INCLUDE` nor an `EXCLUDE` expression is kept.

If a rules file has `INCLUDE` statements but **no** `EXCLUDE` statements, `INCLUDE` acts as a standalone whitelist: only icons matching at least one `INCLUDE` expression are kept
- 'INCLUDE' acts as a filter in
- 'EXCLUDE' acts as a filter out
Thus 'EXCLUDE(NOT NAME="file_name.svg") will include the file_name.svg and exclude all the others.

I'm not sure if this is the best approach, but i wrote it like this.

### Examples

Keep only `.svg` files, and drop anything under a directory called `Unique Icons`, unless its file name starts with `Alloy`:

```
INCLUDE(NAME="Alloy*" AND EXTENSION=".svg")
EXCLUDE(CONTAIN(PATH, "Unique Icons"))
EXCLUDE(NOT EXTENSION=".svg")
```

Whitelist a single file, dropping everything else:

```
INCLUDE(NAME="filename")
EXCLUDE(NAME="*")
```

Exclude every file whose name contains 'deprecated'
```
EXCLUDE(CONTAIN(NAME, "deprecated"))
```
