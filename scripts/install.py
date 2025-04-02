#!/usr/bin/env python3
"""
Installation script for the transcribe-meeting package.

This script sets up the environment, installs dependencies, and prepares the models.
"""

import sys
import subprocess
import argparse
import platform
from pathlib import Path
import shutil
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("install")

# Path to the repository root
REPO_ROOT = Path(__file__).resolve().parent.parent


def check_python_version():
    """Check that the Python version is at least 3.8."""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required.")
        sys.exit(1)
    logger.info(f"Python version {platform.python_version()} detected.")


def create_virtual_env(venv_path: Path, force: bool = False):
    """
    Create a virtual environment.
    
    Args:
        venv_path: Path to create the virtual environment
        force: Whether to force creation if it already exists
    """
    if venv_path.exists() and force:
        logger.info(f"Removing existing virtual environment at {venv_path}")
        shutil.rmtree(venv_path)
    
    if not venv_path.exists():
        logger.info(f"Creating virtual environment at {venv_path}")
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
    else:
        logger.info(f"Virtual environment already exists at {venv_path}")


def get_pip_path(venv_path: Path):
    """Get the path to pip in the virtual environment."""
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"


def install_dependencies(venv_path: Path, dev_mode: bool = False):
    """
    Install package dependencies.
    
    Args:
        venv_path: Path to the virtual environment
        dev_mode: Whether to install development dependencies
    """
    pip = get_pip_path(venv_path)
    
    if not pip.exists():
        logger.error(f"Could not find pip at {pip}")
        sys.exit(1)
    
    # Update pip
    logger.info("Upgrading pip...")
    subprocess.run([str(pip), "install", "--upgrade", "pip"], check=True)
    
    # Install the package
    package_dir = REPO_ROOT
    install_args = [str(pip), "install", "-e"]
    
    if dev_mode:
        install_args.append(".[dev]")
    else:
        install_args.append(".")
    
    logger.info(f"Installing package {'with dev dependencies' if dev_mode else ''}...")
    subprocess.run(install_args, cwd=str(package_dir), check=True)

    try:
        logger.info("Successfully installed the transcribe_meeting package.")
    except ImportError as e:
        logger.error(f"Failed to import transcribe_meeting after installation: {e}")
        logger.error("Please check your virtual environment and installation.")
        sys.exit(1)


def check_ffmpeg():
    """Check if FFmpeg is installed."""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        logger.info("FFmpeg is installed.")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.warning("FFmpeg is not installed. Audio extraction will not work.")
        if platform.system() == "Windows":
            logger.info("Download FFmpeg from https://ffmpeg.org/download.html and add it to your PATH.")
        elif platform.system() == "Darwin":  # macOS
            logger.info("Install FFmpeg using Homebrew: brew install ffmpeg")
        else:  # Linux
            logger.info("Install FFmpeg using your package manager, e.g., sudo apt install ffmpeg")
        return False


def download_whisper_model(model_size: str = "medium"):
    """
    Pre-download the Whisper model.
    
    Args:
        model_size: Size of the Whisper model to download
    """
    valid_sizes = ["tiny", "base", "small", "medium", "large"]
    if model_size not in valid_sizes:
        logger.error(f"Invalid model size: {model_size}. Must be one of {valid_sizes}.")
        return
    
    logger.info(f"Downloading Whisper {model_size} model...")
    
    try:
        import whisper
        whisper.load_model(model_size)
        logger.info(f"Successfully downloaded Whisper {model_size} model.")
    except ImportError:
        logger.error("Whisper package not installed. Run the installation step first.")
    except Exception as e:
        logger.error(f"Error downloading Whisper model: {e}")


def main():
    """Main installation function."""
    parser = argparse.ArgumentParser(description="Install the transcribe-meeting package.")
    parser.add_argument("--venv", default="venv", help="Path to virtual environment")
    parser.add_argument("--dev", action="store_true", help="Install development dependencies")
    parser.add_argument("--force", action="store_true", help="Force recreation of virtual environment")
    parser.add_argument("--whisper-model", default="medium",
                       choices=["tiny", "base", "small", "medium", "large"],
                       help="Whisper model size to download")
    args = parser.parse_args()
    
    # Check Python version
    check_python_version()
    
    # Create virtual environment
    venv_path = Path(args.venv)
    if not venv_path.is_absolute():
        venv_path = REPO_ROOT / venv_path
    
    create_virtual_env(venv_path, args.force)
    
    # Install dependencies
    install_dependencies(venv_path, args.dev)
    
    # Check for FFmpeg
    check_ffmpeg()
    
    # Download Whisper model
    download_whisper_model(args.whisper_model)
    
    logger.info("Installation complete!")
    
    # Print activation instructions
    if platform.system() == "Windows":
        activate_cmd = f"{venv_path}\\Scripts\\activate.bat"
    else:
        activate_cmd = f"source {venv_path}/bin/activate"
    
    logger.info(f"Activate the virtual environment with: {activate_cmd}")
    logger.info("Run the transcription with: transcribe-meeting <video_file>")


if __name__ == "__main__":
    main()