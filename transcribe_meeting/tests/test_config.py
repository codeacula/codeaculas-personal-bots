import pytest
from transcribe_meeting.config import validate_config

def test_validate_config():
    # Mock valid configuration
    issues = validate_config()
    assert len(issues) == 0, f"Expected no issues, but found: {issues}"

    # Mock invalid configuration
    from transcribe_meeting import config
    config.WHISPER_MODEL_SIZE = "invalid-model"
    config.WHISPER_DEVICE = "invalid-device"
    config.WHISPER_COMPUTE_TYPE = "invalid-compute"
    config.REPO_ROOT = "invalid/path"
    config.PROCESSED_VIDEO_DIR = "invalid/path"

    issues = validate_config()
    assert len(issues) > 0, "Expected issues with invalid configuration, but found none."
    assert any("WHISPER_MODEL_SIZE" in issue for issue in issues), "Expected issue with WHISPER_MODEL_SIZE."
    assert any("WHISPER_DEVICE" in issue for issue in issues), "Expected issue with WHISPER_DEVICE."
    assert any("WHISPER_COMPUTE_TYPE" in issue for issue in issues), "Expected issue with WHISPER_COMPUTE_TYPE."
    assert any("REPO_ROOT" in issue for issue in issues), "Expected issue with REPO_ROOT."
    assert any("PROCESSED_VIDEO_DIR" in issue for issue in issues), "Expected issue with PROCESSED_VIDEO_DIR."