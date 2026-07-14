import os
import pathlib

import click

from st.utils import go_through_fs_tree
from st.utils.pretty_print import print_done
from st.utils.pretty_print import print_verbose
from st.utils.str_utils import to_snake_case


@click.group()
def theme():
    """Create a DSL theme."""


@theme.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--output", type=click.Path(), required=False, default=None)
def clean(path, output):
    """Prepare a directory of icons for theme creation."""
    full_path = pathlib.Path(path)
    output_path = full_path.parent / (output if output else "cleaned")
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
    first_level = [item for item in os.listdir(full_path) if not item.startswith(".")]
    first_level_dict = {item: to_snake_case(item) for item in first_level}
    for item in first_level_dict.values():
        if item.startswith("."):
            print_verbose(f"Skipping hidden directory: {item}")
        else:
            if item is not None:
                os.makedirs(os.path.join(output_path, item), exist_ok=True)
    elements = go_through_fs_tree(
        full_path=full_path,
    )
    for element in elements:
        element.copy(output_path=output_path)
    print_done("Cleaning done!")


# @click.command()
# @click.argument("path", type=click.Path(exists=True))
# @click.option("--name", type=str, required=True)
# @click.option("--description", type=str, required=False, default=None)
# @click.option("--color", type=str, required=False, default=None)
# @click.option("--add", type=click.Path(exists=True), required=False)
# def create(path, name, description, color, add) -> None:
#     home_path = pathlib.Path.home()
#     config_path = (
#         home_path / pathlib.Path(".config") / pathlib.Path("stc") / CONFIG_FILE
#     )
#     if not config_path.exists():
#         print_warning("Configuration file not found. Creating one with default values.")
#         init_config(config_path=config_path)
#     config = load_config(config_path=config_path)
#     full_path = pathlib.Path(path).resolve()
#     output_path = full_path.parent / "-".join(name.lower().split(" "))

#     name = name.replace("'", "").replace('"', "") if name else None
#     description = description.replace("'", "").replace('"', "") if description else None
#     os.makedirs(os.path.join(output_path), exist_ok=True)
#     theme = Theme(
#         name=name,
#         description="description here" if description is None else description,
#     )

#     elements = go_through_fs_tree(
#         full_path=full_path,
#         output_path=pathlib.Path(output_path),
#     )

#     for element in elements:
#         if element.has_extension("svg"):
#             element.copy(
#                 output_path=output_path
#                 / element.get_theme_name(
#                     theme.prefix
#                     if config["defaults.theme"].getboolean("prefix")
#                     else None
#                 ),
#             )
#             element.load_properties_from_json()

#             theme_element = ThemeElement(
#                 tag=element.get_theme_tag(
#                     theme.prefix
#                     if config["defaults.theme"].getboolean("prefix")
#                     else None
#                 ),
#                 stroke=color
#                 if color is not None
#                 else config["defaults.theme"]["stroke"],
#                 color=color if color is not None else config["defaults.theme"]["color"],
#                 icon=element.get_theme_name(
#                     theme.prefix
#                     if config["defaults.theme"].getboolean("prefix")
#                     else None
#                 ),
#             )
#             theme.add_element(theme_element)
#     if add is not None:
#         added_theme_element: list[ThemeElement] = read_element_from_json(add)
#         print_warning(f"Adding additional {len(added_theme_element)}.")
#         theme.extend(added_theme_element)

#     theme.create(pathlib.Path(output_path) / "theme.json")

#     print_done("Theme created!")


# @click.command()
# @click.option("--output", type=click.Path(), required=True)
# def scrape(output) -> None:
#     print(f"Scraping icons from {TECH_ICON_URL}\n")
#     time.sleep(1)
#     if download_blob_image(
#         base_url=TECH_ICON_URL, output_dir=pathlib.Path(output).resolve()
#     ):
#         print_done("\nAll images downloaded successfully!")
#     else:
#         print_warning("\nDownload failed")
