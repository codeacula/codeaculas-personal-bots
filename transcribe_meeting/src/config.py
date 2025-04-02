"""
Configuration management for the transcribe-meeting package.

This module handles loading configuration from environment variables,
configuration files, and default values, with validation.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, Literal
import torch

# Define types
ComputeType = Literal["float16", "float32", "int8"]
DeviceType = Literal["cuda", "cpu"]

# Base configuration with defaults
DEFAULT_CONFIG = {
    # Repository configuration
    "REPO_ROOT": str(Path(__file__).parent.parent.parent),
    "TRANSCRIPT_BASE_DIR_NAME": "transcripts",
    "PROCESSED_VIDEO_DIR": "processed",
    
    # Whisper model configuration
    "WHISPER_MODEL_SIZE": "large",  # tiny, base, small, medium, large
    "WHISPER_DEVICE": "cuda" if torch.cuda.is_available() else "cpu",
    "WHISPER_COMPUTE_TYPE": "int8",  # float16, float32, int8
    "WHISPER_BATCH_SIZE": 16,       # Batch size for inference
    "WHISPER_BEAM_SIZE": 5,         # Beam size for inference
    
    # Diarization configuration
    "DIARIZATION_PIPELINE_NAME": "pyannote/speaker-diarization@2.1",
    "HUGGINGFACE_AUTH_TOKEN": os.environ.get("HUGGINGFACE_AUTH_TOKEN", ""),
    
    # Resource management
    "GPU_MEMORY_THRESHOLD_MB": 2000,  # Minimum required GPU memory in MB
    "CPU_THREADS": os.cpu_count() or 4,  # Default to available cores or 4
    
    # Alignment configuration
    "ALIGNMENT_MAX_WORKERS": max(1, (os.cpu_count() or 4) - 1),  # Keep one CPU core free
    "ALIGNMENT_TARGET_WORDS_PER_CHUNK": 500,  # Target words per chunk for parallel alignment
}

# Configuration loaded from environment will be stored here
_loaded_config: Dict[str, Any] = {}

def _validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the configuration values.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Validated configuration dictionary
    
    Raises:
        ValueError: If a configuration value is invalid
    """
    # Validate WHISPER_MODEL_SIZE
    valid_model_sizes = ["tiny", "base", "small", "medium", "large"]
    if config["WHISPER_MODEL_SIZE"] not in valid_model_sizes:
        raise ValueError(f"WHISPER_MODEL_SIZE must be one of {valid_model_sizes}")
    
    # Validate WHISPER_DEVICE
    valid_devices = ["cuda", "cpu"]
    if config["WHISPER_DEVICE"] not in valid_devices:
        raise ValueError(f"WHISPER_DEVICE must be one of {valid_devices}")
    
    # Validate WHISPER_COMPUTE_TYPE
    valid_compute_types = ["float16", "float32", "int8"]
    if config["WHISPER_COMPUTE_TYPE"] not in valid_compute_types:
        raise ValueError(f"WHISPER_COMPUTE_TYPE must be one of {valid_compute_types}")
    
    # Create paths as Path objects
    config["REPO_ROOT"] = Path(config["REPO_ROOT"])
    
    # Convert numeric values
    config["GPU_MEMORY_THRESHOLD_MB"] = int(config["GPU_MEMORY_THRESHOLD_MB"])
    config["CPU_THREADS"] = int(config["CPU_THREADS"])
    config["WHISPER_BATCH_SIZE"] = int(config["WHISPER_BATCH_SIZE"])
    config["WHISPER_BEAM_SIZE"] = int(config["WHISPER_BEAM_SIZE"])
    config["ALIGNMENT_MAX_WORKERS"] = int(config["ALIGNMENT_MAX_WORKERS"])
    config["ALIGNMENT_TARGET_WORDS_PER_CHUNK"] = int(config["ALIGNMENT_TARGET_WORDS_PER_CHUNK"])
    
    return config

def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables and default values.
    
    Environment variables take precedence over default values.
    
    Returns:
        Complete configuration dictionary
    """
    global _loaded_config
    
    # Start with default config
    config = DEFAULT_CONFIG.copy()
    
    # Override with environment variables
    for key in DEFAULT_CONFIG:
        env_value = os.environ.get(f"TRANSCRIBE_{key}")
        if env_value is not None:
            config[key] = env_value
    
    # Validate the configuration
    config = _validate_config(config)
    
    # Cache the loaded config
    _loaded_config = config
    
    return config

def get_config() -> Dict[str, Any]:
    """
    Get the current configuration.
    
    If configuration has not been loaded yet, load it first.
    
    Returns:
        Complete configuration dictionary
    """
    global _loaded_config
    if not _loaded_config:
        return load_config()
    return _loaded_config

# Load the configuration at module import time
_loaded_config = load_config()

# Export all config values as module-level constants
REPO_ROOT = _loaded_config["REPO_ROOT"]
TRANSCRIPT_BASE_DIR_NAME = _loaded_config["TRANSCRIPT_BASE_DIR_NAME"]
PROCESSED_VIDEO_DIR = _loaded_config["PROCESSED_VIDEO_DIR"]
WHISPER_MODEL_SIZE = _loaded_config["WHISPER_MODEL_SIZE"]
WHISPER_DEVICE = _loaded_config["WHISPER_DEVICE"]
WHISPER_COMPUTE_TYPE = _loaded_config["WHISPER_COMPUTE_TYPE"]
WHISPER_BATCH_SIZE = _loaded_config["WHISPER_BATCH_SIZE"]
WHISPER_BEAM_SIZE = _loaded_config["WHISPER_BEAM_SIZE"]
DIARIZATION_PIPELINE_NAME = _loaded_config["DIARIZATION_PIPELINE_NAME"]
HUGGINGFACE_AUTH_TOKEN = _loaded_config["HUGGINGFACE_AUTH_TOKEN"]
GPU_MEMORY_THRESHOLD_MB = _loaded_config["GPU_MEMORY_THRESHOLD_MB"]
CPU_THREADS = _loaded_config["CPU_THREADS"]
ALIGNMENT_MAX_WORKERS = _loaded_config["ALIGNMENT_MAX_WORKERS"]
ALIGNMENT_TARGET_WORDS_PER_CHUNK = _loaded_config["ALIGNMENT_TARGET_WORDS_PER_CHUNK"]