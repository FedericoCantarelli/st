import os
import pathlib

from st.core.model import IconElement
from st.utils.pretty_print import print_verbose
from st.utils.pretty_print import print_warning


def go_through_fs_tree(
    full_path: pathlib.Path,
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
            # TODO: remove the check on .svg icon
            # Used only for test purposes here
            if item_path.suffix == ".svg":
                element_list.append(IconElement(item_path))

        elif os.path.isdir(item_path):
            element_list.extend(
                go_through_fs_tree(
                    full_path=item_path,
                )
            )

    return element_list
