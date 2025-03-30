# Video Meeting Transcription & Diarization Pipeline

A Python-based tool to automatically transcribe video files, identify speakers (diarization), and generate timestamped transcripts in TXT and SRT formats. It also includes features for file management and optional Git integration.

Built using powerful open-source libraries like `faster-whisper` for efficient transcription and `pyannote.audio` for speaker diarization, designed to run locally on capable hardware.

## Features

* **Audio Extraction:** Automatically extracts audio from video files using `ffmpeg`.
* **Speaker Diarization:** Identifies different speakers and assigns labels (SPEAKER_00, SPEAKER_01, etc.) using `pyannote.audio`.
* **Accurate Transcription:** Generates text transcripts with word-level timestamps using `faster-whisper` (leveraging Whisper large-v3 by default).
* **Speaker Alignment:** Assigns speaker labels to the corresponding words in the transcript.
* **Output Formats:** Saves transcripts as both plain TXT and timestamped SRT files.
* **Organized Output:** Sorts transcript files into `YYYY/MM` subdirectories within a configurable output path.
* **Optimized Performance:** Uses optimized alignment algorithms and batched inference (configurable) for faster processing. Dynamic CPU core usage for alignment step based on workload.
* **Git Integration:** Automatically stages, commits, and pushes the generated transcript files to a specified Git repository (configurable).
* **File Management:** Cleans up temporary audio files and moves the original processed video to a designated folder (configurable).
* **Configurable:** Key settings like model names, paths, batch size, beam size, and feature toggles are managed in `config.py`.
* **Modular Code:** Refactored into separate Python modules for better organization and maintainability.

## Requirements & Prerequisites

* **System:**
  * Python 3.11 (recommended due to library compatibility observed during development)
  * `ffmpeg`: Must be installed and accessible via the system PATH. ([Download](https://ffmpeg.org/download.html))
  * `git`: Must be installed and accessible via the system PATH. Credentials must be configured for pushing to your remote repository without interactive prompts (e.g., SSH key, credential manager).
* **Hardware:**
  * NVIDIA GPU with CUDA support is **highly recommended** for reasonable performance. Tested on RTX 3080 (10GB VRAM).
  * Sufficient RAM (32GB recommended, especially for large models/long files).
* **Python Packages:** See `requirements.txt`. Install using `pip install -r requirements.txt`.
* **External Accounts:**
  * **Hugging Face Hub Account:** Required for downloading `pyannote.audio` models. You *must* accept the user conditions for `pyannote/speaker-diarization-3.1` and `pyannote/segmentation-3.0` (or equivalent) on the Hugging Face website. You need to be logged in via the CLI: `huggingface-cli login`.

## Setup & Installation

1. **Clone/Download:** Get the script files into your project directory (e.g., `D:\Projects\home-ai`).
2. **Create Virtual Environment:**

    ```bash
    cd D:\Projects\home-ai
    python -m venv .venv
    .\.venv\Scripts\activate
    ```

    *(Adjust python command/activation based on your OS/Python version)*
3. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    *(Remember to generate `requirements.txt` first using `pip freeze > requirements.txt` within the activated venv)*
4. **Install `ffmpeg`:** Download from the official website and ensure the `ffmpeg.exe` location is added to your system's PATH environment variable.
5. **Install/Configure `git`:** Install Git if you haven't already, and ensure your user name, email, and push credentials (SSH/HTTPS) are configured. Initialize the output directory (`D:\Projects\work-notes` in the default config) as a Git repository if it isn't already (`git init`).
6. **Hugging Face Login:** Run `huggingface-cli login` in your terminal and follow the prompts to log in with your Hugging Face account token (after accepting model terms on the website).

## Configuration

Most settings are controlled via the `config.py` file. Key options include:

* `WHISPER_MODEL_SIZE`, `WHISPER_DEVICE`, `WHISPER_COMPUTE_TYPE`, `WHISPER_BEAM_SIZE`, `WHISPER_BATCH_SIZE`: Control transcription model and performance.
* `DIARIZATION_PIPELINE_NAME`: Selects the speaker diarization model.
* `HUGGINGFACE_AUTH_TOKEN`: Can optionally store your HF token here (use `None` to rely on CLI login).
* `REPO_ROOT`: Path to the root of your Git repository where transcripts will be stored.
* `TRANSCRIPT_BASE_DIR_NAME`: Subfolder name for transcripts within the repo root.
* `PROCESSED_VIDEO_DIR`: Fixed path where processed videos will be moved.
* `DELETE_TEMP_AUDIO`, `MOVE_PROCESSED_VIDEO`: Toggle cleanup actions.
* `SRT_OPTIONS`: Control SRT file formatting.
* `GIT_ENABLED`, `GIT_COMMIT_MESSAGE_PREFIX`: Control Git integration.
* `ALIGNMENT_TARGET_WORDS_PER_CHUNK`, `ALIGNMENT_MAX_WORKERS`: Tune alignment parallelism.

## Usage

Run the main script from your activated virtual environment, providing the path to the video file as a command-line argument:

```bash
python transcribe_meeting.py "C:\path\to\your\video\file.mkv"
```

(Remember to use quotes if the path contains spaces)

The script will:

1. Extract audio to a temporary `.wav` file next to the video.
2. Load models (downloads may occur on first run).
3. Perform diarization and transcription.
4. Align speakers with words.
5. Save `.txt` and `.srt` transcripts to `{REPO_ROOT}/Transcripts/{YYYY}/{MM}/`.
6. Clean up the temporary `.wav` file (if enabled).
7. Commit and push transcripts to Git (if enabled).
8. Move the original video file to `PROCESSED_VIDEO_DIR` (if enabled and previous steps succeeded).

## Modules Overview

The tool is structured into several Python modules:

* `transcribe_meeting.py`: Main entry point, orchestrates the workflow.
* `config.py`: Stores configuration settings.
* `audio_utils.py`: Handles `ffmpeg` audio extraction.
* `transcriber.py`: Manages `faster-whisper` model loading and transcription.
* `diarizer.py`: Manages `pyannote.audio` pipeline loading and diarization.
* `alignment.py`: Performs alignment of words to speakers (optimized).
* `output_utils.py`: Formats and saves TXT and SRT files.
* `file_manager.py`: Handles path calculations, directory creation, file moving/deletion.
* `git_utils.py`: Handles Git command execution.

## Known Issues / Limitations

* **Speaker Diarization Accuracy:** `pyannote.audio` performance can vary depending on audio quality, number of speakers, crosstalk, etc. Speaker labels might sometimes be incorrect or fragmented.
* **Punctuation/Capitalization:** Output from Whisper models often lacks sophisticated punctuation and consistent capitalization. Manual editing may be needed for formal documents.
* **Materialization Time:** The step involving iterating Whisper results to get word timestamps ("Materializing segments...") can be time-consuming (~4-5 mins for a 1hr video observed in testing), though faster with batching enabled.
