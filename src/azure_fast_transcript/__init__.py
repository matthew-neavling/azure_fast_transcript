from typing import TypedDict, Generator
from datetime import time
import os
import json

import requests

DEFAULT_ENDPOINT = "https://eastus.api.cognitive.microsoft.com/speechtotext/transcriptions:transcribe?api-version=2024-11-15"
MAX_LINE_LENGTH = 25
MAX_LINES = 2


class Word(TypedDict):
    text: str
    offset: int
    duration: int


class Phrase(TypedDict):
    channel: int
    offset: int
    duration: int
    text: str
    words: list[Word]
    locale: str
    confidence: float


class Channel(TypedDict):
    channel: int
    text: str


class FastTranscript(TypedDict):
    duration: int
    combinedPhrases: list[Channel]
    phrases: list[Phrase]


class CaptionLine(TypedDict):
    start: int
    end: int
    text: str


class Transcript:
    def __init__(self, file: str, endpoint: str = DEFAULT_ENDPOINT) -> None:
        """
        :param file: file to transcribe
        :param endpoint: Fast transcription API endpoint
        """
        # Init with endpoint and file
        self.endpoint = endpoint
        """
        Azure Fast Transcript endpoint URL
        """

        self.file = file
        """
        Path of the file to transcribe
        """

        self.transcript = {}
        """
        Transcription result
        """

    def get_transcript(self) -> FastTranscript:
        """POST file to endpoint
        1. Retrieve subscription key
        :returns:
        """

        subscription_key = os.environ.get("SPEECH_KEY")
        if not subscription_key:
            raise Exception("SPEECH_KEY missing from environment.")

        headers = {
            "Accept": "application/json",
            "Ocp-Apim-Subscription-Key": subscription_key,
        }
        definition = json.dumps({"locales": ["en-US"], "profanityFilter": "None"})
        files = {
            "definition": (None, definition, "application/json"),
            "audio": (
                os.path.basename(self.file),
                open(self.file, "rb"),
                "application/octet-stream",
            ),
        }

        resp = requests.post(self.endpoint, headers=headers, files=files)

        if resp.ok:
            data = resp.json()
        else:
            raise Exception(
                f"Response type invalid:\nCode:\t{resp.status_code}\nMsg:\t{resp.content}"
            )

        return data

    def _get_line(
        self,
        words_list: list[Word],
        max_line_length: int = MAX_LINE_LENGTH,
        max_lines: int = MAX_LINES,
    ) -> Generator[CaptionLine, None, None]:
        """
        Turn a transcription result into a line generator with constraints on line length and number of lines per subtitle
        :param words_list: source for lines
        :param max_line_length: maximum number of words per line
        :param max_lines: maximum number of lines per subtitle
        """
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

            start = candidate_words[0]["offset"]
            end = candidate_words[-1]["offset"] + candidate_words[-1]["duration"]
            text = "\n".join(lines)
            yield {"start": start, "end": end, "text": text}

    def _time_from_milliseconds(self, milliseconds: int) -> str:
        """
        Convert a timestamp in milliseconds to a VTT timestamp
        :param milliseconds: timestampt in milliseconds
        """
        seconds = milliseconds / 1000
        microsecond = (milliseconds * 1000) % 10**6
        second = int(seconds) % 60
        minute = int(seconds / 60) % 60
        ts = time(minute=minute, second=second, microsecond=microsecond)

        return "{:02}:{:02}:{:02}.{:03}".format(
            ts.hour, ts.minute, ts.second, ts.microsecond // 1000
        )

    def parse_subtitles(self, response: FastTranscript) -> str:
        """
        Turn a fast transcript result into VTT subtitles
        :param response: JSON result from the transcription API
        """
        enumerator = 1

        vtt = "WEBVTT"
        vtt += "\n"
        for phrase in response["phrases"]:
            words = phrase["words"]

            lines = self._get_line(words)
            while True:
                try:
                    next_line = next(lines)
                    start = next_line["start"]
                    end = next_line["end"]
                    vtt += f"\n{enumerator}"
                    vtt += f"\n{self._time_from_milliseconds(start)} --> {self._time_from_milliseconds(end)}"
                    vtt += f"\n{next_line['text']}"
                    vtt += "\n"
                    enumerator += 1
                except StopIteration:
                    break

        return vtt

    def parse_transcript(self, response: FastTranscript) -> str:
        channels = response["combinedPhrases"]
        if len(channels) > 1:
            # handle multiple speakers
            return "\n".join(t["text"] for t in channels)
        else:
            return channels[0]["text"]

    @staticmethod
    def get_subtitles(file: str, endpoint: str = DEFAULT_ENDPOINT) -> str:
        """
        Submit a file to an Azure Fast Transcription api endpoint and return results as VTT
        https://learn.microsoft.com/en-us/rest/api/speechtotext/transcriptions/transcribe?view=rest-speechtotext-2024-11-15&tabs=HTTP
        :param file: Path to the transcription target
        :param endpoint: default is preconfigured to the East US api
        """
        transcript = Transcript(file=file, endpoint=endpoint)
        response = transcript.get_transcript()
        subtitles = transcript.parse_subtitles(response)
        return subtitles

    @staticmethod
    def get_raw(file, endpoint: str = DEFAULT_ENDPOINT) -> str:
        """
        Submit a file to an Azure Fast Transcription api endpoint and return results as a plaintext file
        https://learn.microsoft.com/en-us/rest/api/speechtotext/transcriptions/transcribe?view=rest-speechtotext-2024-11-15&tabs=HTTP
        :param file: Path to the transcription target
        :param endpoint: default is preconfigured to the East US api
        """
        transcript = Transcript(file=file, endpoint=endpoint)
        response = transcript.get_transcript()
        transcript = transcript.parse_transcript(response)
        return transcript
