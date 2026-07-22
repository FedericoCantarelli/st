import click

from st.commands.theme import create
from st.commands.theme import theme
from st.commands.version import version


@click.group()
def main():
    """ST: A command line tool for creating Structurizr themes easily."""


main.add_command(version)
main.add_command(theme)

if __name__ == "__main__":
    main()
