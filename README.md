# Overview
Python CLI for the Azure AI Speech Services [fast transcript API](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/fast-transcription-create).

# Prerequisites
You must have an Azure AI Speech Services API key and region present in your environment
```sh
# bash
export SPEECH_REGION="<speech_region>"
export SPEECH_KEY="<speech key>"

# powershell
$env:SPEECH_REGION = "<speech region>"
$env:SPEECH_KEY = "<speech key>"
```

# Installation
```sh
git clone https://github.com/matthew-neavling/azure_fast_transcript.git
cd azure_fast_transcript
pip install .
```
or
```sh
pip install git+https://github.com/matthew-neavling/azure_fast_transcript.git
```

# Usage
## Command Line
```sh
py -m azure_fast_transcript example.wav # Return VTT subtitles with default parameters
py -m azure_fast_transcript --raw example.wav # Return raw transcript
py -m azure_fast_transcript -p Masked example.wav # Return VTT subtitles with profanity masked with asterisks
```

## Programmatic
```py
from azure_fast_transcript import Transcript

subtitles = Transcript.get_subtitles("example.wav")

with open("example.vtt") as vtt_file:
    for line in subtitles:
        vtt_file.write(line)

```
