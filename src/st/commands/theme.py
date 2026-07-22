import os
import pathlib

import click

from st.core.model import Theme
from st.core.model import ThemeElement
from st.core.model import go_through_fs_tree
from st.core.rule_parser import RuleSet
from st.core.rule_parser import filter_elements
from st.utils.config import CONFIG_FILE
from st.utils.config import init_config
from st.utils.config import load_config
from st.utils.pretty_print import print_done
from st.utils.pretty_print import print_verbose
from st.utils.pretty_print import print_warning
from st.utils.str_utils import to_snake_case


@click.group()
def theme():
    """Create a DSL theme."""


@theme.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--output", type=click.Path(), required=False, default=None)
@click.option(
    "--rules",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
    default=None,
    help="Path to a rules file (e.g. rules.st) filtering which icons to process.",
)
def clean(path, output, rules):
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
        full_path=full_path, include_top_parent_directory=False
    )
    if rules is not None:
        elements = filter_elements(elements, RuleSet.from_file(pathlib.Path(rules)))
    for element in elements:
        element.copy(
            output_path=output_path
            / element.top_parent_directory
            / element.cleaned_file_name
            if element.top_parent_directory
            else output_path / element.cleaned_file_name
        )
    print_done("Cleaning done!")


@theme.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--name", type=str, required=True)
@click.option("--description", type=str, required=False, default=None)
@click.option("--color", type=str, required=False, default=None)
@click.option("--add", type=click.Path(exists=True), required=False)
@click.option(
    "--rules",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
    default=None,
    help="Path to a rules file (e.g. rules.st) filtering which icons to process.",
)
def create(
    path, name: str, description: str | None, color: str, add: str, rules: str
) -> None:
    if not CONFIG_FILE.exists():
        print_warning("Configuration file not found. Creating one with default values.")
        init_config(config_path=CONFIG_FILE)
    config = load_config(config_path=CONFIG_FILE)
    full_path = pathlib.Path(path).resolve()
    output_path = full_path.parent / "-".join(name.lower().split(" "))

    name = name.replace("'", "").replace('"', "")
    description = (
        description.replace("'", "").replace('"', "")
        if description is not None
        else None
    )
    os.makedirs(os.path.join(output_path), exist_ok=True)
    theme = Theme(
        name="Name here" if name is None else name,
        description="Description here" if description is None else description,
    )

    elements = go_through_fs_tree(
        full_path=full_path,
        include_top_parent_directory=False,
    )
    if rules is not None:
        elements = filter_elements(elements, RuleSet.from_file(pathlib.Path(rules)))

    for element in elements:
        element.copy(
            output_path=output_path / (name + "_" + element.theme_name),
        )
        element.load_properties_from_json()

        theme_element = ThemeElement(
            tag=element.get_theme_tag("gcp"),
            # stroke=color
            # if color is not None
            # else config["defaults.theme"]["stroke"],
            # color=color if color is not None else config["defaults.theme"]["color"],
            stroke="#FF0000",
            color="#00FF00",
            icon=name + "_" + element.theme_name,
        )
        theme.add_element(theme_element)

    theme.export(pathlib.Path(output_path) / "theme.json")

    print_done("Theme created!")


# TODO: keep this for future releases maybe >^.^<
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
