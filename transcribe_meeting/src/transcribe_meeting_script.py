"""CLI script for transcribing videos with speaker diarization."""
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from transcribe_meeting.core import process_video
from transcribe_meeting.file_manager import calculate_paths
from transcribe_meeting.config import (
    REPO_ROOT,
    TRANSCRIPT_BASE_DIR_NAME,
    PROCESSED_VIDEO_DIR
)


def setup_logging(log_file: Optional[str] = None) -> None:
    """Configure logging for the CLI script.
    
    Args:
        log_file: Optional path to the log file
    """
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers
    )


def validate_paths(
    video_path: str,
    output_dir: Optional[str] = None
) -> Dict[str, Path]:
    """Validate and calculate necessary paths.
    
    Args:
        video_path: Path to the input video file
        output_dir: Optional custom output directory
        
    Returns:
        Dictionary of validated paths
        
    Raises:
        ValueError: If paths are invalid
    """
    video_file = Path(video_path)
    if not video_file.exists():
        raise ValueError(f"Video file not found: {video_path}")

    if output_dir:
        transcript_dir = Path(output_dir)
    else:
        transcript_dir = Path(TRANSCRIPT_BASE_DIR_NAME)

    paths = calculate_paths(
        video_path=video_file,
        repo_root=REPO_ROOT,
        transcript_base_dir_name=str(transcript_dir),
        processed_video_dir=PROCESSED_VIDEO_DIR
    )

    return paths


def main() -> int:
    """Main entry point for the CLI script.
    
    Returns:
        0 on success, 1 on failure
    """
    parser = argparse.ArgumentParser(
        description="Transcribe video with speaker diarization"
    )
    parser.add_argument(
        "video_path",
        help="Path to the video file to transcribe"
    )
    parser.add_argument(
        "--output-dir",
        help="Custom output directory for transcripts"
    )
    parser.add_argument(
        "--log-file",
        help="Path to the log file",
        default="transcribe.log"
    )
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_file)

    try:
        # Validate paths
        paths = validate_paths(args.video_path, args.output_dir)

        # Process video
        process_video(
            job_id="cli",
            video_path=paths["video_path"],
            jobs={},  # Not used in CLI mode
            transcript_base_dir=paths["transcript_subdir"]
        )

        logging.info(f"Transcription complete. Output saved to: {paths['output_txt_file']}")
        return 0

    except Exception as e:
        logging.error(f"Error during transcription: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())