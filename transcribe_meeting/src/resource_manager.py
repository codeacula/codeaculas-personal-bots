"""Resource management utilities for CPU and GPU resources."""
import gc
import torch
import logging


def check_gpu_availability() -> bool:
    """Check if CUDA-capable GPU is available.

    Returns:
        True if GPU is available, False otherwise
    """
    cuda_available = torch.cuda.is_available()
    if cuda_available:
        logging.info("CUDA GPU is available.")
        device_name = torch.cuda.get_device_name(0)
        logging.info(f"Using GPU: {device_name}")
    else:
        logging.warning("No CUDA GPU available. Using CPU.")
    return cuda_available


def get_gpu_memory_mb() -> int:
    """Get available GPU memory in megabytes.

    Returns:
        Available GPU memory in MB, or 0 if no GPU
    """
    try:
        if torch.cuda.is_available():
            free_mem = torch.cuda.mem_get_info()[0]
            return int(free_mem / (1024 * 1024))
        return 0
    except Exception as e:
        logging.error(f"Error getting GPU memory info: {e}")
        return 0


def select_device(
    prefer_gpu: bool = True,
    min_memory_mb: int = 2000
) -> str:
    """Select compute device based on availability and requirements.

    Args:
        prefer_gpu: Whether to prefer GPU over CPU
        min_memory_mb: Minimum required GPU memory in MB

    Returns:
        'cuda' if GPU is available and meets requirements, 'cpu' otherwise
    """
    if not prefer_gpu:
        logging.info("GPU usage not preferred, using CPU.")
        return "cpu"

    if not torch.cuda.is_available():
        logging.warning("No CUDA GPU available, falling back to CPU.")
        return "cpu"

    available_memory = get_gpu_memory_mb()
    if available_memory < min_memory_mb:
        logging.warning(
            f"Available GPU memory ({available_memory}MB) is below threshold "
            f"({min_memory_mb}MB), falling back to CPU."
        )
        return "cpu"

    logging.info(f"Using GPU with {available_memory}MB available memory.")
    return "cuda"


def cleanup_gpu_memory() -> None:
    """Free up GPU memory by clearing cache and running garbage collection."""
    try:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()
            logging.info("GPU memory cache cleared.")
    except Exception as e:
        logging.error(f"Error clearing GPU memory: {e}")


def monitor_gpu_usage(tag: str = "") -> None:
    """Log current GPU memory usage for monitoring.
    
    Args:
        tag: Optional identifier for the monitoring point
    """
    if not torch.cuda.is_available():
        return

    try:
        free_mem, total_mem = torch.cuda.mem_get_info()
        used_mem = total_mem - free_mem
        free_mb = free_mem / (1024 * 1024)
        used_mb = used_mem / (1024 * 1024)
        total_mb = total_mem / (1024 * 1024)
        
        logging.info(
            f"GPU Memory [{tag}]: "
            f"Used={used_mb:.0f}MB, "
            f"Free={free_mb:.0f}MB, "
            f"Total={total_mb:.0f}MB"
        )
    except Exception as e:
        logging.error(f"Error monitoring GPU usage: {e}")


def get_torch_device(device_str: str = "cuda") -> torch.device:
    """Get a torch.device object for the specified device string.
    
    Args:
        device_str: Device specification ('cuda' or 'cpu')
        
    Returns:
        torch.device object for the specified device
    """
    if device_str == "cuda" and not torch.cuda.is_available():
        logging.warning("CUDA requested but not available, falling back to CPU.")
        device_str = "cpu"
    return torch.device(device_str)