from setuptools import setup, find_packages

setup(
    name="transcribe_meeting",
    version="0.1.0",
    description="Video meeting transcription and diarization pipeline",
    author="Your Name",
    author_email="your.email@example.com",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.11",
    install_requires=[
        "faster-whisper>=1.1.1",
        "pyannote.audio>=3.3.2",
        "torch>=2.5.1",
        "torchaudio>=2.5.1",
    ],
    entry_points={
        "console_scripts": [
            "transcribe-meeting=transcribe_meeting.transcribe_meeting:main",
        ],
    },
)