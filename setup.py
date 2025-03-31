#!/usr/bin/env python3
from setuptools import setup, find_packages

# Read the contents of README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read version from the package
__version__ = ""
exec(open('src/transcribe_meeting/__init__.py').read().split('__version__ = ')[1].split('\n')[0].strip())

setup(
    name="transcribe-meeting",
    version=__version__,
    description="A tool for transcribing and diarizing meeting recordings",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/home-ai",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "whisper",
        "pyannote.audio>=2.1.1",
        "torch>=2.0.0",
        "torchaudio>=2.0.0",
        "ffmpeg-python>=0.2.0",
        "numpy>=1.22.0",
        "pandas>=1.4.0",
        "tqdm>=4.64.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
    },
    entry_points={
        "console_scripts": [
            "transcribe-meeting=transcribe_meeting.transcribe_meeting:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
    ],
)