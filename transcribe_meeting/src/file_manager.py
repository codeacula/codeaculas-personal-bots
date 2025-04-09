# file_manager.py
"""File and directory management utilities."""
import datetime
import shutil
import logging
from pathlib import Path
from typing import Dict, Union


def calculate_paths(
    video_path: Union[str, Path],
    repo_root: Union[str, Path],
    transcript_base_dir_name: str,
    processed_video_dir: Union[str, Path]
) -> Dict[str, Path]:
    """Calculate all necessary file paths for processing.
    
    Args:
        video_path: Path to the input video file
        repo_root: Root directory of the repository
        transcript_base_dir_name: Base directory name for transcripts
        processed_video_dir: Directory to move processed videos to
        
    Returns:
        Dictionary containing all calculated paths
    """
    paths = {}
    video_path = Path(video_path)
    paths['video_path'] = video_path
    paths['base_name'] = video_path.stem
    paths['video_dir'] = video_path.parent
    paths['audio_file'] = paths['video_dir'] / f"{paths['base_name']}_audio.wav"
    
    transcript_base_dir = Path(repo_root) / transcript_base_dir_name
    now = datetime.datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    paths['transcript_subdir'] = transcript_base_dir / year / month
    paths['output_txt_file'] = paths['transcript_subdir'] / f"{paths['base_name']}_transcript_speakers.txt"
    
    # Add processed video path
    processed_dir = Path(processed_video_dir)
    paths['processed_video_path'] = processed_dir / f"{paths['base_name']}{video_path.suffix}"
    
    return paths


def create_directories(paths: Dict[str, Path]) -> None:
    """Create necessary directories for output files.
    
    Args:
        paths: Dictionary of paths from calculate_paths()
    """
    try:
        paths['transcript_subdir'].mkdir(parents=True, exist_ok=True)
        logging.info(f"Created transcript directory: {paths['transcript_subdir']}")
    except Exception as e:
        logging.error(f"Failed to create transcript directory: {e}")
        raise


def delete_temp_audio(audio_file_path: Union[str, Path]) -> None:
    """Delete temporary audio file after processing.
    
    Args:
        audio_file_path: Path to the audio file to delete
    """
    try:
        audio_path = Path(audio_file_path)
        if audio_path.exists():
            audio_path.unlink()
            logging.info(f"Cleaned up intermediate audio file: {audio_file_path}")
    except Exception as e:
        logging.warning(f"Could not delete intermediate audio file {audio_file_path}. Error: {e}")


def move_video(
    video_source_path: Union[str, Path],
    video_dest_path: Union[str, Path]
) -> bool:
    """Move processed video file to archive location.
    
    Args:
        video_source_path: Source path of the video file
        video_dest_path: Destination path for the video file
        
    Returns:
        True if successful, False otherwise
    """
    source_path = Path(video_source_path)
    dest_path = Path(video_dest_path)
    
    if not dest_path or not dest_path.parent.exists():
        logging.warning("Skipping video move: destination path/dir invalid.")
        return False
    
    logging.info(f"Moving processed video to: {dest_path}")
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), str(dest_path))
        logging.info(f"Successfully moved video to: {dest_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to move video file: {e}")
        return False