import json
import os
import pathlib
import shutil
from typing import Any

from st.core.theme_attributes import Border
from st.core.theme_attributes import Shape
from st.utils.pretty_print import print_ok
from st.utils.pretty_print import print_verbose
from st.utils.pretty_print import print_warning
from st.utils.str_utils import from_snake_to_camel_case
from st.utils.str_utils import to_snake_case


class IconElement:
    """Class representing a icon in the file system.

    The entire CLI is based on the file system structure and the icons found.
    This class is the starting point for DSL theme elements, as it represents
    the icons found.
    """

    def __init__(self, path: pathlib.Path, include_top_parent_directory: bool = True):
        """Initialize a IconElement instance."""
        self.path = path
        self._include_top_parent_directory = include_top_parent_directory
        self.top_parent_directory = (
            pathlib.Path(to_snake_case(path.parts[1])) if len(path.parts) > 2 else None
        )

        self.metadata: dict[str, Any] = {}

    @property
    def name(self) -> str:
        """Get the name of the icon element without the file extension.

        Returns:
            str: The name of the icon element without the file extension.
        """
        return self.path.stem

    @property
    def full_name(self) -> str:
        """Get the full name of the icon element with the file extension.

        Returns:
            str: The full name of the icon element with the file extension.
        """
        return self.path.name

    @property
    def extension(self) -> str:
        """Get the file extension of the icon element.

        Returns:
            str: The file extension of the icon element.
        """
        return self.path.suffix

    @property
    def cleaned_file_name(self) -> str:
        """Get the output file path for the icon element.

        Returns:
            str: The output file path for the icon element.
        """
        if (
            self.top_parent_directory is not None
        ) and self._include_top_parent_directory:
            return (
                self.top_parent_directory.name
                + "_"
                + to_snake_case(self.name)
                + self.extension
            )
        else:
            return to_snake_case(self.name) + self.extension

    @property
    def theme_name(self) -> str:
        theme_name = self.path.parent.parts[-1].split("_")[0].lower() + "_" + self.name
        return theme_name + self.extension

    def get_theme_tag(self, prefix: str | None = None) -> str:
        theme_name = self.theme_name.split(".")[0]
        tag_name = (
            theme_name.split("_")[0].capitalize()
            + " - "
            + " ".join([word.capitalize() for word in theme_name.split("_")[1:]])
        )
        if prefix is not None:
            tag_name = prefix + " - " + tag_name

        return tag_name

    # TODO: find a way to manage this logic in a more elegant way
    def load_properties_from_json(self):
        """Load propertiers from a JSON file located alongside the element SVG file.

        Args:
            path (str): Path to the JSON file containing metadata.
        """
        try:
            json_file = self.path.resolve().stem + ".json"
            json_file_path = self.path.parent / json_file

            with open(json_file_path) as f:
                self.metadata = json.load(f)
                print_verbose(f"Loaded metadata for {self.name}")
        except FileNotFoundError:
            self.metadata = {}

    def copy(
        self,
        output_path: pathlib.Path,
    ):
        """Copy the icon element to a new location.

        This is particularly to correctly manage icons for the DSL theme.

        Args:
            output_path (pathlib.Path): The path to copy the icon element to.
        """
        shutil.copyfile(
            self.path,
            output_path,
        )
        print_ok("Processed " + self.full_name)

    def __str__(self) -> str:
        """Return a string representation of the IconElement instance.

        Returns:
            str: A string representation of the IconElement instance.
        """
        return f"Element(name={self.name}, path={self.path})"

    def __repr__(self) -> str:
        """Return a string representation of the IconElement instance.

        Returns:
            str: A string representation of the IconElement instance.
        """
        repr_str = "IconElement("
        for key, value in self.__class__.__dict__.items():
            if not key.startswith("__") and not callable(value):
                repr_str += f"{key}={getattr(self, key)}, "
        repr_str = repr_str.rstrip(", ") + ")"
        return repr_str


class ThemeElement:
    """Class representing a theme element for the DSL theme."""

    def __init__(
        self,
        tag: str | None = None,
        stroke: str | None = None,
        color: str | None = None,
        icon: str | None = None,
        border: Border | None = Border.SOLID,
        shape: Shape | None = Shape.ROUDED_BOX,
        width: int | None = None,
        height: int | None = None,
        background: str | None = None,
        font_size: int | None = None,
        opacity: int | None = None,
        description: str | None = None,
    ):
        """Initialize a ThemeElement instance.

        Args:
            tag (str): The tag for the theme element.
            stroke (str): The stroke color for the theme element.
            color (str): The fill color for the theme element.
            icon (str): The icon for the theme element.
            shape (Shape): The shape of the theme element.
            width (int): The width of the theme element.
            height (int): The height of the theme element.
            background (str): The background color for the theme element.
            font_size (int): The font size for the theme element.
            border (Border): The border style for the theme element.
            opacity (int): The opacity for the theme element.
            description (str): A brief description of the theme element.
        """
        self.tag = tag
        self.stroke = stroke
        self.color = color
        self.icon = icon
        self.shape = shape.value if shape is not None else None
        self.width = width
        self.height = height
        self.background = background
        self.font_size = font_size
        self.border = border.value if border is not None else None
        self.opacity = opacity
        self.description = description

    def as_dict(self) -> dict[str, Any]:
        """Convert the ThemeElement instance to a dictionary. Skip None attribues.

        Dictionary names are the final names used in the DSL theme.
        To do so, snake_case attribute names are converted to camelCase.

        Returns:
            dict: A dictionary representation of the ThemeElement instance.
        """
        dict_representation = {}
        # Iterate over class attributes
        for attribute, value in self.__dict__.items():
            if value is not None:
                dict_representation[from_snake_to_camel_case(attribute)] = value
        return dict_representation

    @classmethod
    def from_json_dict(cls, dict: dict[str, Any]) -> "ThemeElement":
        """Create a ThemeElement instance from a dictionary.

        Args:
            dict (dict): A dictionary of the attributes of the ThemeElement.
            As it is in the theme. Thus, the keys are in camelCase.

        Returns:
            ThemeElement: A new instance of ThemeElement.
        """
        theme_element = cls()
        for key, value in dict.items():
            if hasattr(theme_element, key) and key != "tag":
                setattr(theme_element, key, value)
            else:
                print_warning(f"Unknown attribute {key} in ThemeElement JSON.")
        return theme_element


class Theme:
    """Class representing a theme, which is a collection of theme elements."""

    def __init__(self, name: str, description: str):
        """Initialize a Theme instance.

        Args:
            name (str): The name of the theme.
            description (str): A brief description of the theme.
        """
        self.name = name
        self.description = description
        self.elements: list[ThemeElement] = []

    def add_element(self, element: ThemeElement) -> None:
        """Add a theme element to the theme.

        Args:
            element (ThemeElement): The theme element to add.
        """
        self.elements.append(element)

    def extend(self, elements: list[ThemeElement]) -> None:
        """Extend the theme with a list of theme elements.

        Args:
            elements (list[ThemeElement]): A list of theme elements to add.
        """
        self.elements.extend(elements)

    def export(self, path: pathlib.Path) -> None:
        """Export the theme to a JSON file.

        Args:
            path (pathlib.Path): The path to the JSON file.
        """
        json_dict = {
            "name": self.name,
            "description": self.description,
            "elements": [element.as_dict() for element in self.elements],
        }

        with open(path, "w") as f:
            json.dump(json_dict, f, indent=4)


def go_through_fs_tree(
    full_path: pathlib.Path,
    include_top_parent_directory: bool,
) -> list[IconElement]:
    element_list = []
    for item in os.listdir(full_path):
        item_path = pathlib.Path(full_path) / item
        if os.path.isfile(item_path):
            if item.startswith("."):
                print_verbose(
                    f"Skipping hidden file: {'/'.join(str(item_path).split('/')[-3:])}"
                )
                continue
            element_list.append(IconElement(item_path, include_top_parent_directory))

        elif os.path.isdir(item_path):
            element_list.extend(
                go_through_fs_tree(
                    full_path=item_path,
                    include_top_parent_directory=include_top_parent_directory,
                )
            )

    return element_list
