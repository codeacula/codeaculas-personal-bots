#!/usr/bin/env python3
from setuptools import setup

setup(
    name="transcribe-meeting",
    version="0.1.0",
    description="A tool for transcribing and diarizing meeting recordings",
    packages=["transcribe_meeting"],
    package_dir={"transcribe_meeting": "src"},
    python_requires=">=3.11",
)
