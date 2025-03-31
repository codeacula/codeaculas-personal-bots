# Transcribe Meeting

A Python package for automatically transcribing and diarizing meeting recordings.

## Features

- Extract audio from video files
- Transcribe speech to text using OpenAI's Whisper model
- Identify speakers through diarization using Pyannote
- Generate readable transcripts with speaker attribution
- Manage resources efficiently on GPU and CPU
- Process and organize transcript files by date

## Installation

### Prerequisites

- Python 3.8 or higher
- FFmpeg (for audio extraction)
- CUDA-compatible GPU (optional but recommended)

### Installing from source

```bash
# Clone the repository
git clone https://github.com/yourusername/home-ai.git
cd home-ai

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package in development mode
pip install -e ".[dev]"
```

### Environment Variables

Set the following environment variables to configure the tool:

```
TRANSCRIBE_HUGGINGFACE_AUTH_TOKEN=your_huggingface_token_here
TRANSCRIBE_WHISPER_MODEL_SIZE=medium  # tiny, base, small, medium, large
TRANSCRIBE_WHISPER_DEVICE=cuda  # cuda or cpu
```

## Usage

### Command Line

```bash
# Basic usage
transcribe-meeting path/to/your/video_file.mp4

# With verbose logging
transcribe-meeting path/to/your/video_file.mp4 --verbose
```

### As a Library

```python
from transcribe_meeting import extract_audio, transcriber, diarizer, alignment, output_utils

# Extract audio from video
audio_path = "path/to/audio.wav"
extract_audio("path/to/video.mp4", audio_path)

# Load models
whisper_model = transcriber.ModelManager("medium", "cuda", "float16").load_model()
diarization_pipeline = diarizer.load_diarization_pipeline()

# Run processing
raw_segments, _ = transcriber.run_transcription(whisper_model, audio_path)
segments_list = list(raw_segments)  # Materialize generator
diarization_result = diarizer.run_diarization(diarization_pipeline, audio_path)
speaker_turns = diarizer.extract_speaker_turns(diarization_result)

# Align speakers with transcription
aligned_words = alignment.align_words_with_speakers(segments_list, speaker_turns)

# Save output
output_utils.save_transcript_with_speakers(aligned_words, "output_transcript.txt")
```

## Project Structure

```
home-ai/
├── docs/                   # Documentation files
├── logs/                   # Log files (generated at runtime)
├── scripts/                # Helper scripts
├── src/                    # Source code 
│   └── transcribe_meeting/ # Main package
│       ├── __init__.py     # Package exports
│       ├── alignment.py    # Speaker/word alignment
│       ├── audio_utils.py  # Audio extraction and processing
│       ├── config.py       # Configuration management
│       ├── diarizer.py     # Speaker diarization
│       ├── file_manager.py # File and directory management
│       ├── output_utils.py # Output formatting
│       ├── resource_manager.py # GPU/CPU resource management
│       ├── transcriber.py  # Whisper transcription
│       └── transcribe_meeting.py # Main entry point
├── tests/                  # Test suite
│   └── test_*.py           # Test modules
├── .gitignore              # Git ignore file
├── LICENSE                 # Project license
├── pyproject.toml          # Project configuration for tools
├── README.md               # This file
└── setup.py                # Package installation configuration
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/transcribe_meeting
```

### Code Formatting and Linting

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Run linter
flake8 src tests

# Type checking
mypy src
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for the speech recognition model
- [Pyannote Audio](https://github.com/pyannote/pyannote-audio) for the speaker diarization
