import argparse
import logging
import sys
from . import Transcript, DEFAULT_ENDPOINT, ProfanityFilter, logger


class Args(argparse.Namespace):
    file: str
    endpoint: str
    raw: bool
    locale: str
    profanity_filter: ProfanityFilter
    verbose: bool
    output: str


app = argparse.ArgumentParser(
    prog="Azure Fast Transcript",
    description="Use MS Azure's Fast Transcript REST API to quickly generate subtitles and transcripts",
)

app.add_argument("file", type=str, help="Path to the audio/video file to transcribe")
app.add_argument(
    "--endpoint",
    default=DEFAULT_ENDPOINT,
    help=f"The Azure Fast Transcript API REST endpoint. Default is: {DEFAULT_ENDPOINT}",
)
app.add_argument(
    "-l",
    "--locale",
    type=str,
    help="Language of the input audio. Default is 'en-US'",
    default="en-US",
)
app.add_argument(
    "-p",
    "--profanity-filter",
    type=str,
    help="Level of profanity filtering. Options are 'None' (no filter), 'Masked' (asterisks), 'Removed' (removed from transcript), or 'Tags' (profanity tags added). Default is 'None'",
    default="None",
)
app.add_argument(
    "--raw",
    action="store_true",
    help="Dump transcript as plain text instead of subtitles",
    default=False,
)

# TODO
app.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Enable verbose logging",
    default=False,
)

app.add_argument(
    "output",
    type=str,
    help="Path to output file. If not specified, prints to stdout",
    default="",
)


def main(*args) -> None:
    args = app.parse_args(*args, namespace=Args())

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.debug(args)

    if not args.file:
        sys.stdout.write(app.usage)  # type: ignore
        sys.exit(0)

    try:
        if args.raw:
            logger.debug("Getting raw transcript")
            transcript = Transcript.get_raw(args.file, endpoint=args.endpoint)
        else:
            logger.debug("Getting VTT subtitles")
            transcript = Transcript.get_subtitles(args.file, endpoint=args.endpoint)

        outfile = sys.stdout
        if args.output:
            outfile = open(args.output, "w+")

        outfile.write(transcript)

        outfile.close()

    except Exception as err:
        sys.stderr.write(f"{err}\n")


if __name__ == "__main__":
    main()
