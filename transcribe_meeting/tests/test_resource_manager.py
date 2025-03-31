"""Tests for the resource_manager module."""

import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add the src directory to path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import the module under test
from transcribe_meeting import resource_manager
from transcribe_meeting import config


@pytest.fixture
def mock_torch():
    """Create a mock torch module for testing."""
    with patch.object(resource_manager, "TORCH_AVAILABLE", True):
        mock = MagicMock()
        
        # Setup CUDA mock
        mock.cuda.is_available.return_value = True
        mock.cuda.device_count.return_value = 2
        
        # Setup device properties
        device_props = MagicMock()
        device_props.total_memory = 8 * 1024 * 1024 * 1024  # 8 GB in bytes
        mock.cuda.get_device_properties.return_value = device_props
        
        # Setup memory allocation mocks
        mock.cuda.memory_reserved = lambda device: 1 * 1024 * 1024 * 1024  # 1 GB in bytes
        
        # Setup dtype mocks
        mock.float16 = "float16"
        mock.float32 = "float32"
        mock.int8 = "int8"
        
        with patch.object(resource_manager, "torch", mock):
            yield mock


def test_check_gpu_availability_with_torch(mock_torch):
    """Test GPU availability detection with torch available."""
    assert resource_manager.check_gpu_availability() is True
    mock_torch.cuda.is_available.assert_called_once()


def test_check_gpu_availability_without_torch():
    """Test GPU availability detection without torch."""
    with patch.object(resource_manager, "TORCH_AVAILABLE", False):
        assert resource_manager.check_gpu_availability() is False


def test_get_gpu_memory(mock_torch):
    """Test getting GPU memory."""
    memory_dict = resource_manager.get_gpu_memory()
    
    # Should return memory for 2 GPUs
    assert len(memory_dict) == 2
    assert 0 in memory_dict
    assert 1 in memory_dict
    
    # Memory should be calculated correctly (total * 0.9 - allocated, converted to MB)
    expected_memory = (8 * 0.9 - 1) * 1024  # (8 GB * 0.9 - 1 GB) in MB
    assert memory_dict[0] == int(expected_memory)
    assert memory_dict[1] == int(expected_memory)


def test_get_gpu_memory_no_torch():
    """Test getting GPU memory when torch is not available."""
    with patch.object(resource_manager, "TORCH_AVAILABLE", False):
        memory_dict = resource_manager.get_gpu_memory()
        assert memory_dict == {}


def test_select_device_prefers_config(mock_torch):
    """Test that select_device respects the configuration preference for CPU."""
    with patch.object(config, "WHISPER_DEVICE", "cpu"):
        device = resource_manager.select_device()
        assert device == "cpu"
        # CUDA should not be checked if CPU is preferred
        mock_torch.cuda.is_available.assert_not_called()


def test_select_device_selects_best_gpu(mock_torch):
    """Test that select_device selects the GPU with the most available memory."""
    with patch.object(config, "WHISPER_DEVICE", "cuda"):
        with patch.object(config, "GPU_MEMORY_THRESHOLD_MB", 1000):
            # Mock get_gpu_memory to return different memory for each GPU
            with patch.object(resource_manager, "get_gpu_memory", 
                             return_value={0: 2000, 1: 4000}):
                device = resource_manager.select_device()
                # Should select GPU 1 which has more memory
                assert device == "cuda:1"


def test_select_device_falls_back_to_cpu_when_no_gpu(mock_torch):
    """Test that select_device falls back to CPU when no GPU is available."""
    with patch.object(config, "WHISPER_DEVICE", "cuda"):
        mock_torch.cuda.is_available.return_value = False
        device = resource_manager.select_device()
        assert device == "cpu"


def test_select_device_falls_back_to_cpu_when_insufficient_memory(mock_torch):
    """Test that select_device falls back to CPU when GPU memory is insufficient."""
    with patch.object(config, "WHISPER_DEVICE", "cuda"):
        with patch.object(config, "GPU_MEMORY_THRESHOLD_MB", 10000):
            # Mock get_gpu_memory to return insufficient memory
            with patch.object(resource_manager, "get_gpu_memory", 
                             return_value={0: 2000, 1: 5000}):
                device = resource_manager.select_device()
                # Should fall back to CPU since neither GPU has enough memory
                assert device == "cpu"


def test_cleanup_gpu_memory(mock_torch):
    """Test GPU memory cleanup."""
    resource_manager.cleanup_gpu_memory()
    mock_torch.cuda.empty_cache.assert_called_once()


def test_cleanup_gpu_memory_handles_error(mock_torch):
    """Test that cleanup_gpu_memory handles exceptions gracefully."""
    mock_torch.cuda.empty_cache.side_effect = RuntimeError("Test error")
    # Should not raise an exception
    resource_manager.cleanup_gpu_memory()


def test_get_torch_dtype(mock_torch):
    """Test getting torch dtype based on compute type."""
    assert resource_manager.get_torch_dtype("float16") == "float16"
    assert resource_manager.get_torch_dtype("float32") == "float32"
    assert resource_manager.get_torch_dtype("int8") == "int8"


def test_get_torch_dtype_invalid():
    """Test that get_torch_dtype raises ValueError for invalid compute types."""
    with patch.object(resource_manager, "TORCH_AVAILABLE", True):
        with pytest.raises(ValueError):
            resource_manager.get_torch_dtype("invalid_type")


def test_get_torch_dtype_no_torch():
    """Test that get_torch_dtype raises ImportError when torch is not available."""
    with patch.object(resource_manager, "TORCH_AVAILABLE", False):
        with pytest.raises(ImportError):
            resource_manager.get_torch_dtype("float16")