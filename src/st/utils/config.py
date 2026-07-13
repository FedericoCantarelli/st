"""Module to handle configuration.

Configuration priority is the following:
    1. Environment variables
    2. Configuration file
    3. Default values
"""

import configparser
import pathlib
from typing import Any


CONFIG_FILE: pathlib.Path = pathlib.Path.home() / ".st" / "config.ini"
DEFAULTS: dict[str, Any] = {"theme_stroke": "#232f3d", "theme_color": "#232f3d"}


def init_config(config_path: pathlib.Path) -> None:
    """Initialize configuration file with default values.

    Args:
        config_path (pathlib.Path): Path to the configuration file.
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = configparser.ConfigParser()
    config["theme"] = {
        "stroke": DEFAULTS["theme_stroke"],
        "color": DEFAULTS["theme_color"],
    }
    with open(config_path, "w") as config_file:
        config.write(config_file)


def load_config(config_path: pathlib.Path) -> configparser.ConfigParser:
    """Load configuration from a file.

    Args:
        config_path (pathlib.Path): Path to the configuration file.

    Returns:
        configparser.ConfigParser: The loaded configuration object.
    """
    config = configparser.ConfigParser()
    config.read(config_path)
    return config
