"""
Initialize the transcribe_meeting package.

This module re-exports key components for easier imports.
"""

__version__ = "0.1.0"

# Re-export only what's needed by the core API
from .core import process_video, cleanup_job_files
# Other imports should be done directly from their modules as needed
