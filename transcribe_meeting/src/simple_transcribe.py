"""Simple command-line interface for transcribing videos."""
import sys
import logging
from pathlib import Path
from typing import Optional

from faster_whisper import WhisperModel

from transcribe_meeting.core import process_video
from transcribe_meeting.file_manager import calculate_paths
from transcribe_meeting.config import (
    WHISPER_MODEL_SIZE,
    WHISPER_DEVICE,
    WHISPER_COMPUTE_TYPE,
    REPO_ROOT,
    TRANSCRIPT_BASE_DIR_NAME,
    PROCESSED_VIDEO_DIR
)


def setup_logging() -> None:
    """Configure logging for the CLI application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("transcribe.log"),
        ]
    )


def init_whisper_model() -> Optional[WhisperModel]:
    """Initialize the Whisper model for transcription.

    Returns:
        Initialized WhisperModel or None if initialization fails
    """
    try:
        logging.info(f"Loading Whisper model ({WHISPER_MODEL_SIZE})...")
        model = WhisperModel(
            model_size_or_path=WHISPER_MODEL_SIZE,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE
        )
        logging.info("Whisper model loaded successfully.")
        return model
    except Exception as e:
        logging.error(f"Error loading Whisper model: {e}")
        return None


def validate_input(video_path: Optional[str] = None) -> Optional[Path]:
    """Validate the input video file path.

    Args:
        video_path: Path to the input video file

    Returns:
        Path object if valid, None otherwise
    """
    if not video_path:
        logging.error("No video file path provided.")
        print("Usage: python -m transcribe_meeting.simple_transcribe <video_file>")
        return None

    path = Path(video_path)
    if not path.exists():
        logging.error(f"Video file not found: {video_path}")
        return None

    if not path.is_file():
        logging.error(f"Path is not a file: {video_path}")
        return None

    return path


def main() -> int:
    """Main entry point for the CLI application.

    Returns:
        0 on success, 1 on failure
    """
    # Setup logging
    setup_logging()

    # Validate input
    if len(sys.argv) < 2:
        logging.error("No video file path provided.")
        print("Usage: python -m transcribe_meeting.simple_transcribe <video_file>")
        return 1

    video_path = validate_input(sys.argv[1])
    if not video_path:
        return 1

    # Calculate paths
    try:
        paths = calculate_paths(
            video_path,
            REPO_ROOT,
            TRANSCRIPT_BASE_DIR_NAME,
            PROCESSED_VIDEO_DIR
        )
    except Exception as e:
        logging.error(f"Error calculating paths: {e}")
        return 1

    # Process video
    try:
        process_video(
            job_id="cli",
            video_path=paths["video_path"],
            jobs={},  # Not used in CLI mode
            transcript_base_dir=paths["transcript_subdir"]
        )
        logging.info(f"Transcription saved to: {paths['output_txt_file']}")
        return 0
    except Exception as e:
        logging.error(f"Error during video processing: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())