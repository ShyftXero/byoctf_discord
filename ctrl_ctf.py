import click

from settings import SETTINGS

@click.command()
def pause_ctf():
    SETTINGS['ctf_paused'] = True

@click.command()
def unpause_ctf():
    SETTINGS['ctf_paused'] = False

@click.command()
def status()
    SETTINGS['status'] = "external message"
