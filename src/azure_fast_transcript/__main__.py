import click

from . import Transcript, DEFAULT_ENDPOINT

@click.command
@click.argument("file", type=click.STRING)
@click.option("-e", "endpoint", type=click.STRING, default=DEFAULT_ENDPOINT)
def app(**kwargs):
    transcript = Transcript.get_subtitles(**kwargs)

    click.echo(transcript)

if __name__ == "__main__":
    app()
