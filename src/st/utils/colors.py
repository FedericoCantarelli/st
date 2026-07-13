"""Module for color utilities."""


class ContrastRatio:
    """Class for storing contrast ratios between colors."""

    AA = 4.5
    AAA = 7.0


def get_luminance_from_rgb(rgb: tuple[int, int, int]) -> float:
    """Calculate the luminance of an RGB color.

    Args:
        rgb (tuple): A tuple of three integers representing the RGB color (R, G, B).

    Returns:
        float: The luminance value of the color.
    """
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def get_contrast_ratio(rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]) -> float:
    """Calculate the contrast ratio between two RGB colors.

    Args:
        rgb1 (tuple): A tuple of three integers representing the first RGB color (R, G, B).
        rgb2 (tuple): A tuple of three integers representing the second RGB color (R, G, B).

    Returns:
        float: The contrast ratio between the two colors.
    """
    lum1 = get_luminance_from_rgb(rgb1)
    lum2 = get_luminance_from_rgb(rgb2)

    if lum1 > lum2:
        return (lum1 + 0.05) / (lum2 + 0.05)
    else:
        return (lum2 + 0.05) / (lum1 + 0.05)
