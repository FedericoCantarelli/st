"""Utility functions for pretty printing messages to the console."""

import os


class Styles:
    """Class to define styles for pretty printing.

    It supports different colors.
    """

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_ok(message: str, **kwargs) -> None:
    """Print an ok message.

    Args:
        message (str): message to print
        **kwargs: additional arguments to pass to print
    """
    print(f"{Styles.OKGREEN}{message}{Styles.ENDC}", **kwargs)  # noqa: T201


def print_warning(message: str, **kwargs) -> None:
    """Print a warning message.

    Args:
        message (str): message to print
        **kwargs: additional arguments to pass to print
    """
    print(f"{Styles.WARNING}{message}{Styles.ENDC}", **kwargs)  # noqa: T201


def print_fail(message: str, **kwargs) -> None:
    """Print an error message.

    Args:
        message (str): message to print
        **kwargs: additional arguments to pass to print
    """
    print(f"{Styles.FAIL}{message}{Styles.ENDC}", **kwargs)  # noqa: T201


def print_done(message: str, **kwargs) -> None:
    """Print a done message.

    Args:
        message (str): message to print
        **kwargs: additional arguments to pass to print
    """
    print(f"{Styles.OKCYAN}{message}{Styles.ENDC}", **kwargs)  # noqa: T201


def print_verbose(message: str, **kwargs) -> None:
    """Print a debug message.

    The message is printed only if the environment variable VERBOSE is set to True.

    Args:
        message (str): message to print
        **kwargs: additional arguments to pass to print
    """
    if os.getenv("VERBOSE"):
        print(message, **kwargs)  # noqa: T201
