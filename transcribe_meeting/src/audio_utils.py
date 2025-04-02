# audio_utils.py
"""Audio extraction and processing utilities."""
import subprocess
import os
import logging


def extract_audio(video_path: str, audio_output_path: str) -> bool:
    """Extract audio from video using ffmpeg.
    
    Args:
        video_path: Path to input video file
        audio_output_path: Path to output audio file
        
    Returns:
        bool: True if extraction succeeded, False otherwise
    """
    logging.info(f"Extracting audio from {os.path.basename(video_path)}...")
    ffmpeg_command = [
        "ffmpeg",
        "-i", video_path,
        "-vn",  # No video
        "-acodec", "pcm_s16le",  # Audio Codec WAV
        "-ar", "16000",  # Sample rate
        "-y",  # Overwrite output file if it exists
        audio_output_path
    ]
    
    try:
        subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
        logging.info("FFmpeg audio extraction successful.")
        return True
    except FileNotFoundError:
        logging.error("Error: ffmpeg command not found. Make sure ffmpeg is installed and in your system's PATH.")
        return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during FFmpeg execution: {e}")
        logging.error(f"FFmpeg stderr:\n{e.stderr}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during audio extraction: {e}")
        return False