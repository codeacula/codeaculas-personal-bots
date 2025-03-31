# Video Meeting Transcription & Diarization Pipeline

A Python-based tool to automatically transcribe video files, identify speakers (diarization), and generate timestamped transcripts in TXT and SRT formats. It also includes features for file management and optional Git integration.

Built using powerful open-source libraries like `faster-whisper` for efficient transcription and `pyannote.audio` for speaker diarization, designed to run locally on capable hardware.

## Features

* **Audio Extraction:** Automatically extracts audio from video files using `ffmpeg`.
* **Speaker Diarization:** Identifies different speakers and assigns labels (SPEAKER_00, SPEAKER_01, etc.) using `pyannote.audio`.
* **Accurate Transcription:** Generates text transcripts with word-level timestamps using `faster-whisper` (leveraging Whisper large-v3 by default).
* **Speaker Alignment:** Assigns speaker labels to the corresponding words in the transcript using optimized parallel processing.
* **Output Formats:** Saves transcripts as both plain TXT and timestamped SRT files with configurable formatting options.
* **Organized Output:** Sorts transcript files into `YYYY/MM` subdirectories within a configurable output path.
* **Optimized Performance:** Uses batched inference (configurable) for faster processing and dynamic CPU core allocation based on workload.
* **Git Integration:** Automatically stages, commits, and pushes the generated transcript files to a specified Git repository.
* **File Management:** Cleans up temporary audio files and moves the original processed video to a designated folder.
* **Configurable:** Key settings like model size, paths, batch size, beam size, and feature toggles are managed in `config.py`.

## Requirements & Prerequisites

* **System:**
  * Python 3.11 (recommended due to library compatibility)
  * `ffmpeg`: Must be installed and accessible via the system PATH. ([Download](https://ffmpeg.org/download.html))
  * `git`: Must be installed and accessible via the system PATH if Git integration is enabled.
* **Hardware:**
  * NVIDIA GPU with CUDA support is **highly recommended** for reasonable performance. Tested on RTX 3080 (10GB VRAM).
  * Sufficient RAM (32GB recommended, especially for large models/long files).
* **Python Packages:** See `requirements.txt`. Install using `pip install -r requirements.txt`.
* **External Accounts:**
  * **Hugging Face Hub Account:** Required for downloading `pyannote.audio` models. You *must* accept the user conditions for `pyannote/speaker-diarization-3.1` and `pyannote/segmentation-3.0` (or equivalent) on the Hugging Face website. You need to be logged in via the CLI: `huggingface-cli login`.

## Setup & Installation

1. **Clone/Download:** Get the script files into your project directory.
2. **Create Virtual Environment:**

    ```bash
    cd path/to/project
    python -m venv .venv
    .\.venv\Scripts\activate  # Windows
    source .venv/bin/activate  # Linux/Mac
    ```

3. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Install `ffmpeg`:** Download from the official website and ensure it's in your system PATH.
5. **Install/Configure `git`:** If using Git integration, ensure credentials are set up to push without interactive prompts.
6. **Hugging Face Login:** Run `huggingface-cli login` and follow the prompts (after accepting model terms on the website).

## Configuration

Edit the `config.py` file to customize:

* **Models & Performance:**
  * `WHISPER_MODEL_SIZE`, `WHISPER_DEVICE`, `WHISPER_COMPUTE_TYPE`: Control transcription model.
  * `WHISPER_BEAM_SIZE`, `WHISPER_BATCH_SIZE`: Adjust transcription quality/performance.
  * `DIARIZATION_PIPELINE_NAME`: Select the speaker diarization model.

* **File Management:**
  * `REPO_ROOT`: Path to your Git repository root for storing transcripts.
  * `TRANSCRIPT_BASE_DIR_NAME`: Subfolder name for transcripts.
  * `PROCESSED_VIDEO_DIR`: Directory where processed videos will be moved.
  * `DELETE_TEMP_AUDIO`, `MOVE_PROCESSED_VIDEO`: Toggle cleanup actions.

* **Output Format:**
  * `SRT_OPTIONS`: Control SRT subtitle formatting options.

* **Git Integration:**
  * `GIT_ENABLED`: Toggle Git operations.
  * `GIT_COMMIT_MESSAGE_PREFIX`: Control Git commit message format.

* **Performance Tuning:**
  * `ALIGNMENT_TARGET_WORDS_PER_CHUNK`, `ALIGNMENT_MAX_WORKERS`: Control parallelism.

## Usage

Run the main script from your activated virtual environment:

```bash
python transcribe_meeting.py "path/to/your/video/file.mkv"
```

The script will:

1. Extract audio to a temporary `.wav` file.
2. Load models (downloads may occur on first run).
3. Perform diarization and transcription.
4. Align speakers with words.
5. Save `.txt` and `.srt` transcripts to `{REPO_ROOT}/Transcripts/{YYYY}/{MM}/`.
6. Clean up temporary files (if enabled).
7. Commit and push transcripts to Git (if enabled).
8. Move the original video file to `PROCESSED_VIDEO_DIR` (if enabled).

## Modules Overview

* `transcribe_meeting.py`: Main entry point, orchestrates the workflow.
* `config.py`: Stores configuration settings.
* `audio_utils.py`: Handles `ffmpeg` audio extraction.
* `transcriber.py`: Manages `faster-whisper` model loading and transcription.
* `diarizer.py`: Manages `pyannote.audio` pipeline loading and diarization.
* `alignment.py`: Performs parallel alignment of words to speakers.
* `output_utils.py`: Formats and saves TXT and SRT files.
* `file_manager.py`: Handles path calculations and file operations.
* `git_utils.py`: Handles Git command execution.
* `checkcuda.py`: Utility to verify CUDA/GPU availability.

## Known Limitations

* **Speaker Diarization Accuracy:** Performance varies depending on audio quality and number of speakers.
* **Materialization Time:** Iterating Whisper results to get word timestamps can take significant time for longer videos.
* **GPU Memory:** Large models require significant VRAM, especially for longer videos.

## Tests

To run the tests, ensure you have `pytest` installed. Then, execute the following command in the project root:

```
pytest
```
