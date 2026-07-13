# Structurizr Theme Creator
A very stupid CLI to create Structurizr themes starting from icons.

## Naming Convention of Exported Icon
This section describes the naming convention for the exported icons. The naming convention depends also on the directory structure of the icons. Indeed, the exported icons name will also depend on first level nested directories inside the input directory. 
Given the following project structure:
```bash
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
where `<prefix>` can be set using `--prefix` argument, `<first_level_dir>` is the name of the first level nested directory in snake case, and `<snake_case_filename>` is the filename converted to snake case, removing everything else that is not a character (number or non-alphanumeric characters).
For example the file `AlloyDB-512-color.png` will be exported as `prefix_unique_icons_alloydb_512_color.png` and the file `Agents-512-color.svg` will be exported as `<prefix>_unique_alloy_db,svg`.
