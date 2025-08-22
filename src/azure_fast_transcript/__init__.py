from typing import Literal, TypedDict, Generator
from datetime import time
import os
import json
import logging

import requests

DEFAULT_ENDPOINT = "https://eastus.api.cognitive.microsoft.com/speechtotext/transcriptions:transcribe?api-version=2024-11-15"
MAX_LINE_LENGTH = 25
MAX_LINES = 2

logger = logging.getLogger()
logging.basicConfig()

ProfanityFilter = Literal["None", "Masked", "Removed", "Tags"]


class Word(TypedDict):
    text: str
    offsetMilliseconds: int
    durationMilliseconds: int


class Phrase(TypedDict):
    channel: int
    offsetMilliseconds: int
    durationMilliseconds: int
    text: str
    words: list[Word]
    locale: str
    confidence: float


class Channel(TypedDict):
    channel: int
    text: str


class CaptionLine(TypedDict):
    start: int
    end: int
    text: str


def _get_line(
    words_list: list[Word],
    max_line_length: int = MAX_LINE_LENGTH,
    max_lines: int = MAX_LINES,
) -> Generator[CaptionLine, None, None]:
    while len(words_list) > 0:
        candidate_words: list[Word] = []
        lines = []
        while len(lines) < max_lines:
            line = ""
            while len(line) < max_line_length:
                try:
                    new_word = words_list.pop(0)
                    line += new_word["text"] + " "
                    candidate_words.append(new_word)
                except IndexError:
                    break
            if line:
                lines.append(line)
            else:
                break

        start = candidate_words[0]["offsetMilliseconds"]
        end = (
            candidate_words[-1]["offsetMilliseconds"] + candidate_words[-1]["durationMilliseconds"]
        )
        text = "\n".join(lines)
        yield {"start": start, "end": end, "text": text}


def _time_from_milliseconds(milliseconds: int) -> str:
    seconds = milliseconds / 1000
    microsecond = (milliseconds * 1000) % 10**6
    second = int(seconds) % 60
    minute = int(seconds / 60) % 60
    ts = time(minute=minute, second=second, microsecond=microsecond)

    return "{:02}:{:02}:{:02}.{:03}".format(
        ts.hour, ts.minute, ts.second, ts.microsecond // 1000
    )


class FastTranscript:
    duration: int
    combined_phrases: list[Channel]
    phrases: list[Phrase]

    def __init__(
        self, duration: int, combined_phrases: list[Channel], phrases: list[Phrase]
    ) -> None:
        self.duration = duration
        self.combined_phrases = combined_phrases
        self.phrases = phrases

    def to_vtt(self) -> str:
        """Return VTT subtitles"""
        enumerator = 1

        vtt = "WEBVTT"
        vtt += "\n"
        for phrase in self.phrases:
            words = phrase["words"]

            lines = _get_line(words)
            while True:
                try:
                    next_line = next(lines)
                    start = next_line["start"]
                    end = next_line["end"]
                    vtt += f"\n{enumerator}"
                    vtt += f"\n{_time_from_milliseconds(start)} --> {_time_from_milliseconds(end)}"
                    vtt += f"\n{next_line['text']}"
                    vtt += "\n"
                    enumerator += 1
                except StopIteration:
                    break

        return vtt

    def to_raw(self) -> str:
        """Return raw transcript"""
        channels = self.combined_phrases
        if len(channels) > 1:
            # handle multiple speakers
            return "\n".join(t["text"] for t in channels)
        else:
            return channels[0]["text"]

    @staticmethod
    def from_object(data: dict) -> "FastTranscript":
        """JSON decoder hook
        :param data: dictionary to parse as FastTranscript
        :returns: FastTranscript
        """
        logger.debug(f"Input object to FastTranscript.from_object: {data}")
        return FastTranscript(
            data["durationMilliseconds"], data["combinedPhrases"], data["phrases"]
        )


class Transcript:
    def __init__(self, file, endpoint: str = DEFAULT_ENDPOINT) -> None:
        """
        :param file: file to transcribe
        :param endpoint: Fast transcription API endpoint
        """
        self.endpoint = endpoint
        self.file = file
        self.transcript = {}

    def get_transcript(
        self, locales: list[str] = ["en-US"], profanity_filter: ProfanityFilter = "None"
    ) -> FastTranscript:
        """POST file to endpoint
        :returns: FastTranscript
        """

        subscription_key = os.environ.get("SPEECH_KEY")
        if not subscription_key:
            logger.fatal("SPEECH_KEY missing from environment.")
            raise Exception("SPEECH_KEY missing from environment.")

        headers = {
            "Accept": "application/json",
            "Ocp-Apim-Subscription-Key": subscription_key,
        }
        definition = json.dumps(
            {"locales": locales, "profanityFilter": profanity_filter}
        )
        files = {
            "definition": (None, definition, "application/json"),
            "audio": (
                os.path.basename(self.file),
                open(self.file, "rb"),
                "application/octet-stream",
            ),
        }

        session = requests.Session()
        req = requests.Request("POST", url=self.endpoint, headers=headers, files=files)
        req = session.prepare_request(req)
        logger.debug(req)

        # resp = requests.post(self.endpoint, headers=headers, files=files)
        resp = session.send(req)
        if resp.ok:
            resp_body = resp.json()
            logger.debug(resp_body)
            return FastTranscript.from_object(resp_body)
        else:
            err = f"Response type invalid:\nCode:\t{resp.status_code}\nMsg:\t{resp.content}"
            logger.fatal(err)
            raise Exception(err)

    @staticmethod
    def get_subtitles(
        file,
        locales: list[str] = ["en-US"],
        profanity_filter: ProfanityFilter = "None",
        endpoint: str = DEFAULT_ENDPOINT,
    ) -> str:
        transcript = Transcript(file=file, endpoint=endpoint)
        response = transcript.get_transcript(
            locales=locales, profanity_filter=profanity_filter
        )
        return response.to_vtt()

    @staticmethod
    def get_raw(
        file,
        locales: list[str] = ["en-US"],
        profanity_filter: ProfanityFilter = "None",
        endpoint: str = DEFAULT_ENDPOINT,
    ) -> str:
        transcript = Transcript(file=file, endpoint=endpoint)
        response = transcript.get_transcript(
            locales=locales, profanity_filter=profanity_filter
        )
        return response.to_raw()
