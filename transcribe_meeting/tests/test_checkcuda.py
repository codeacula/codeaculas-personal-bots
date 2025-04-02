import pytest
from unittest.mock import patch
import transcribe_meeting.checkcuda as checkcuda
import torch

@patch("torch.cuda.is_available", return_value=True)
@patch("torch.cuda.device_count", return_value=1)
@patch("torch.cuda.get_device_name", return_value="NVIDIA Test GPU")
@patch("torch.backends.cudnn.is_available", return_value=True)
@patch("torch.backends.cudnn.version", return_value=8000)
def test_check_cuda(mock_is_available, mock_device_count, mock_get_device_name, mock_cudnn_available, mock_cudnn_version):
    with patch("builtins.print") as mock_print:
        import transcribe_meeting.checkcuda as checkcuda
        mock_print.assert_any_call("PyTorch version: 2.5.1+cu121")
        mock_print.assert_any_call("Is CUDA available? True")
        mock_print.assert_any_call("Number of GPUs available: 1")
        mock_print.assert_any_call("Current GPU name: NVIDIA Test GPU")
        mock_print.assert_any_call("Is cuDNN available? True")
        mock_print.assert_any_call("cuDNN version: 8000")