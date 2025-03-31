"""Tests for the config module."""

import os
import sys
from pathlib import Path
import pytest

# Add the src directory to path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import the module under test
from transcribe_meeting import config


@pytest.fixture
def reset_config():
    """Reset the configuration after each test."""
    # Store original values
    original_env = os.environ.copy()
    original_config = config._loaded_config.copy()
    
    # Let the test run
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
    
    # Restore original config
    config._loaded_config.clear()
    config._loaded_config.update(original_config)


def test_default_config_values(reset_config):
    """Test that default configuration values are set correctly."""
    # Reset the config to make sure we get defaults
    config._loaded_config = {}
    
    # Load the configuration
    cfg = config.load_config()
    
    # Check that default values are set
    assert cfg["WHISPER_MODEL_SIZE"] == "medium"
    assert cfg["TRANSCRIPT_BASE_DIR_NAME"] == "transcripts"
    assert isinstance(cfg["REPO_ROOT"], Path)
    assert cfg["CPU_THREADS"] > 0


def test_env_var_overrides(reset_config):
    """Test that environment variables override default values."""
    # Reset the config
    config._loaded_config = {}
    
    # Set environment variables
    os.environ["TRANSCRIBE_WHISPER_MODEL_SIZE"] = "small"
    os.environ["TRANSCRIBE_TRANSCRIPT_BASE_DIR_NAME"] = "custom_transcripts"
    os.environ["TRANSCRIBE_GPU_MEMORY_THRESHOLD_MB"] = "3000"
    
    # Load the configuration
    cfg = config.load_config()
    
    # Check that environment variables override defaults
    assert cfg["WHISPER_MODEL_SIZE"] == "small"
    assert cfg["TRANSCRIPT_BASE_DIR_NAME"] == "custom_transcripts"
    assert cfg["GPU_MEMORY_THRESHOLD_MB"] == 3000


def test_config_validation_valid_values(reset_config):
    """Test that valid configurations pass validation."""
    # Valid configurations to test
    valid_configs = [
        {"WHISPER_MODEL_SIZE": "tiny", "WHISPER_DEVICE": "cpu", "WHISPER_COMPUTE_TYPE": "float32"},
        {"WHISPER_MODEL_SIZE": "base", "WHISPER_DEVICE": "cuda", "WHISPER_COMPUTE_TYPE": "float16"},
        {"WHISPER_MODEL_SIZE": "small", "WHISPER_DEVICE": "cpu", "WHISPER_COMPUTE_TYPE": "int8"},
    ]
    
    for valid_config in valid_configs:
        # Start with default config and update with test values
        test_config = config.DEFAULT_CONFIG.copy()
        test_config.update(valid_config)
        
        # Should not raise an exception
        validated = config._validate_config(test_config)
        
        # Check that values are preserved
        for key, value in valid_config.items():
            assert validated[key] == value


def test_config_validation_invalid_values(reset_config):
    """Test that invalid configurations fail validation."""
    # Invalid configurations to test
    invalid_configs = [
        {"WHISPER_MODEL_SIZE": "invalid_size"},
        {"WHISPER_DEVICE": "invalid_device"},
        {"WHISPER_COMPUTE_TYPE": "invalid_type"},
    ]
    
    for invalid_config in invalid_configs:
        # Start with default config and update with test values
        test_config = config.DEFAULT_CONFIG.copy()
        test_config.update(invalid_config)
        
        # Should raise ValueError
        with pytest.raises(ValueError):
            config._validate_config(test_config)


def test_get_config_caching(reset_config):
    """Test that get_config caches the loaded configuration."""
    # Reset the config
    config._loaded_config = {}
    
    # Set environment variables
    os.environ["TRANSCRIBE_WHISPER_MODEL_SIZE"] = "large"
    
    # Get the configuration
    cfg1 = config.get_config()
    assert cfg1["WHISPER_MODEL_SIZE"] == "large"
    
    # Change environment variables
    os.environ["TRANSCRIBE_WHISPER_MODEL_SIZE"] = "small"
    
    # Get the configuration again
    cfg2 = config.get_config()
    
    # Should still have the old value because of caching
    assert cfg2["WHISPER_MODEL_SIZE"] == "large"
    
    # Explicitly reload
    config._loaded_config = {}
    cfg3 = config.load_config()
    
    # Now it should have the new value
    assert cfg3["WHISPER_MODEL_SIZE"] == "small"