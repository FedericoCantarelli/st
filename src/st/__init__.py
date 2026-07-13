import click

from st.commands.version import version


@click.group()
def main():
    """ST: A command line tool for creating Structurizr themes easily."""


main.add_command(version)

if __name__ == "main":
    main()
