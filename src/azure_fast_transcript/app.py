import click

# try:
from . import Transcript, DEFAULT_ENDPOINT
# except ImportError:

@click.command
@click.argument("file", type=click.STRING, nargs=1)
@click.option("--raw", is_flag=True, default=False, type=click.BOOL)
@click.option("-e", "endpoint", type=click.STRING, default=DEFAULT_ENDPOINT)
def app(**kwargs):
    raw = kwargs.pop("raw")
    if raw:
        transcript = Transcript.get_raw(**kwargs)
    else:
        transcript = Transcript.get_subtitles(**kwargs)

    click.echo(transcript)
