import argparse
import sys
from io import TextIOWrapper
from . import Transcript, DEFAULT_ENDPOINT
# TODO from .logger import app_logger


class Args(argparse.Namespace):
    file: str
    endpoint: str
    raw: bool
    verbose: bool
    output: TextIOWrapper


app = argparse.ArgumentParser(
    prog="Azure Fast Transcript",
    description="""
Use MS Azure's Fast Transcript REST API to quickly generate subtitles and transcripts

""",
)

app.add_argument("file", type=str, help="Path to the audio/video file to transcribe")
app.add_argument(
    "--endpoint",
    default=DEFAULT_ENDPOINT,
    help=f"The Azure Fast Transcript API REST endpoint. Default is: {DEFAULT_ENDPOINT}",
)
app.add_argument(
    "output",
    type=argparse.FileType("w+", encoding="utf8"),
    default=sys.stdout,
    help="Path to output file. Default is stdout",
)
app.add_argument(
    "--raw",
    action="store_true",
    default=False,
    help="Dump transcript as plain text instead of subtitles",
)

# TODO
app.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    default=False,
    help="Enable verbose logging to stdout",
)


def run(*args, **kwargs) -> None:
    cli_args = app.parse_args(*args, namespace=Args())
    print(cli_args)

    if cli_args.verbose:
        # TODO
        pass

    try:
        if cli_args.raw:
            transcript = Transcript.get_raw(cli_args.file)
        else:
            transcript = Transcript.get_subtitles(
                cli_args.file, endpoint=DEFAULT_ENDPOINT
            )

        cli_args.output.write(transcript)

    except Exception as err:
        sys.stderr.write(f"{err}")
