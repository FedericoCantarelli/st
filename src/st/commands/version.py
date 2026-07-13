import click

from st.utils.pretty_print import print_version


@click.command()
def version():
    """Get CLI version."""
    print_version()
