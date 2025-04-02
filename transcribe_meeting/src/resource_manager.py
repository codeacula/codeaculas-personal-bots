"""
Resource management utilities for GPU and CPU resources.

This module provides functions to check available GPU memory,
manage device selection, and handle resource allocation.
"""

import logging
import os
from typing import Dict, Optional, Tuple, Union

# Conditional import for torch
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from . import config

class ResourceError(Exception):
    """Exception raised for resource-related issues."""
    pass

def check_gpu_availability() -> bool:
    """
    Check if a CUDA-compatible GPU is available.
    
    Returns:
        True if a GPU is available, False otherwise
    """
    if not TORCH_AVAILABLE:
        logging.warning("PyTorch not available, defaulting to CPU")
        return False
    
    return torch.cuda.is_available()

def get_gpu_memory() -> Dict[int, int]:
    """
    Get available memory for each GPU device.
    
    Returns:
        Dictionary mapping GPU device IDs to available memory in megabytes
    """
    if not TORCH_AVAILABLE or not torch.cuda.is_available():
        return {}
    
    available_memory = {}
    for i in range(torch.cuda.device_count()):
        free_memory = torch.cuda.get_device_properties(i).total_memory
        # Reserve some memory for the system
        free_memory = int(free_memory * 0.9 / (1024 * 1024))  # Convert to MB
        
        # Get currently allocated memory
        if hasattr(torch.cuda, 'memory_reserved'):
            allocated = torch.cuda.memory_reserved(i) / (1024 * 1024)
            free_memory -= int(allocated)
        
        available_memory[i] = free_memory
    
    return available_memory

def select_device() -> str:
    """
    Select the appropriate device based on available resources.
    
    Returns:
        Device string ('cuda:X' or 'cpu')
    
    Raises:
        ResourceError: If insufficient GPU memory is available
    """
    # Use configuration preference first
    preferred_device = config.WHISPER_DEVICE
    
    # If CPU is preferred, return it
    if preferred_device == "cpu":
        logging.info("Using CPU as configured")
        return "cpu"
    
    # Check if GPU is available
    if not check_gpu_availability():
        logging.warning("No GPU available, falling back to CPU")
        return "cpu"
    
    # Check available GPU memory
    memory_threshold = config.GPU_MEMORY_THRESHOLD_MB
    gpu_memory = get_gpu_memory()
    
    if not gpu_memory:
        logging.warning("Could not determine GPU memory, falling back to CPU")
        return "cpu"
    
    # Select the GPU with the most available memory
    best_gpu = max(gpu_memory.items(), key=lambda x: x[1])
    
    if best_gpu[1] < memory_threshold:
        logging.warning(f"Insufficient GPU memory: {best_gpu[1]}MB available, "
                       f"{memory_threshold}MB required. Falling back to CPU")
        return "cpu"
    
    device = f"cuda:{best_gpu[0]}"
    logging.info(f"Selected {device} with {best_gpu[1]}MB available memory")
    return device

def cleanup_gpu_memory() -> None:
    """
    Release GPU memory allocations.
    """
    if TORCH_AVAILABLE and torch.cuda.is_available():
        try:
            torch.cuda.empty_cache()
            logging.debug("GPU memory cache cleared")
        except Exception as e:
            logging.warning(f"Failed to clear GPU memory: {e}")

def get_torch_dtype(compute_type: str) -> 'torch.dtype':
    """
    Get the torch dtype corresponding to the requested compute type.
    
    Args:
        compute_type: The compute type string ('float16', 'float32', 'int8')
        
    Returns:
        torch.dtype object
    
    Raises:
        ValueError: If an unsupported compute type is specified
    """
    if not TORCH_AVAILABLE:
        raise ImportError("PyTorch is not available")
    
    dtype_map = {
        "float16": torch.float16,
        "float32": torch.float32,
        "int8": torch.int8,
    }
    
    if compute_type not in dtype_map:
        raise ValueError(f"Unsupported compute type: {compute_type}")
    
    return dtype_map[compute_type]