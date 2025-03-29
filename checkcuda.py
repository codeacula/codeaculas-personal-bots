import torch

print(f"PyTorch version: {torch.__version__}")

# Check 1: Is CUDA available to PyTorch?
cuda_available = torch.cuda.is_available()
print(f"Is CUDA available? {cuda_available}")

if cuda_available:
    # Check 2: Which CUDA version was PyTorch built with? (Should match installer)
    print(f"PyTorch CUDA version: {torch.version.cuda}")

    # Check 3: How many GPUs can PyTorch see?
    gpu_count = torch.cuda.device_count()
    print(f"Number of GPUs available: {gpu_count}")
    if gpu_count > 0:
        print(f"Current GPU name: {torch.cuda.get_device_name(0)}")

    # Check 4: Is cuDNN available? (This is the key check for your cuDNN install)
    cudnn_available = torch.backends.cudnn.is_available()
    print(f"Is cuDNN available? {cudnn_available}")

    if cudnn_available:
        # Check 5: Which cuDNN version does PyTorch detect? (Should be 9xxxx)
        print(f"cuDNN version: {torch.backends.cudnn.version()}")
else:
    print("CUDA not available to PyTorch. Check installation and PATH.")