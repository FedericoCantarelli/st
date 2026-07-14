"""Reference for DSL attributes used in theme elements."""

from enum import Enum


class Border(Enum):
    """Available border styles for DSL elements."""

    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"


class Shape(Enum):
    """Available shape for DSL elements."""

    BOX = "Box"
    CIRCLE = "Circle"
    ELLIPSE = "Ellipse"
    HEXAGON = "Hexagon"
    DIAMOND_CYLINDER = "DiamondCylinder"
    BUCKET = "Bucket"
    PIPE = "Pipe"
    PERSON = "Person"
    ROBOT = "Robot"
    FOLDER = "Folder"
    WEB_BROWSER = "WebBrowser"
    WINDOW = "Window"
    TERMINAL = "Terminal"
    SHELL = "Shell"
    MOBILE_DEVICE_PORTRAIT = "MobileDevicePortrait"
    MOBILE_DEVICE_LANDSCAPE = "MobileDeviceLandscape"
    COMPONENT = "Component"
    ROUDED_BOX = "RoundedBox"
