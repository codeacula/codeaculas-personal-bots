# =============================================
#  Script to launch llama.cpp server process (PowerShell)
# =============================================
param() # Ensures script doesn't take unexpected parameters

# --- Configuration ---

$lcppServerExe = "G:\llama.cpp\llama-server.exe"
$modelPath = "G:\Models\deepcogito_cogito-v1-preview-qwen-14B-Q4_K_M.gguf"
$gpuLayers = 33  # Adjust this based on testing for 10GB VRAM! Lower if Out Of Memory error.
$contextSize = 4096
$hostIp = "127.0.0.1"
$portNum = 8080
$apiKey = "ThisIsGeorge-HeDoesntKonw-WhasiWQldep" # Set your desired API key
$logFilePath = "G:\llama_server_logs\server.log" # IMPORTANT: Ensure this directory exists or the script can create it!
$parallelSlots = 4 # Number of concurrent requests server can handle

# --- End Configuration ---

# --- Display Configuration ---

Write-Host "Starting llama.cpp server in the background..." -ForegroundColor Green
Write-Host "  Log File: $logFilePath"
Write-Host "  Model: $(Split-Path $modelPath -Leaf)" # Shows just the filename
Write-Host "  GPU Layers (-ngl): $gpuLayers"
Write-Host "  Context Size (-c): $contextSize"
Write-Host "  Parallel Slots (-np): $parallelSlots"
Write-Host "  API Key Configured: $(if ([string]::IsNullOrWhiteSpace($apiKey)) {'NO'} else {'YES'})"
Write-Host "  Server Endpoint: http://$hostIp`:$portNum" # Use backtick ` to escape :
Write-Host ""

# --- Define Server Arguments ---

$arguments = @(
    "-m", $modelPath,
    "-ngl", $gpuLayers,
    "-c", $contextSize,
    "--host", $hostIp,
    "--port", $portNum,
    "-np", $parallelSlots,
    "--log-file", $logFilePath,
    "--flash-attn",
    "--log-timestamps"
)

# Add API key argument only if the key variable is actually set
if (-not [string]::IsNullOrWhiteSpace($apiKey)) {
    $arguments += "--api-key", $apiKey
}

# --- Run Server Hidden ---

try {
    Write-Host "Executing: $lcppServerExe $($arguments -join ' ')" # Show the command being run (optional)
    Start-Process -FilePath $lcppServerExe -ArgumentList $arguments -WindowStyle Hidden -PassThru # -PassThru shows basic process info
    Write-Host "llama-server process started hidden." -ForegroundColor Yellow
    Write-Host "Check log file ('$logFilePath') for details. Use Task Manager or 'Get-Process llama-server | Stop-Process -Force' to stop."
} catch {
    Write-Error "ERROR: Failed to start llama-server hidden: $($_.Exception.Message)"
    Read-Host "Press Enter to exit" # Pause window on error
    Exit 1
}

# --- Script End ---
# The script finishes here, but llama-server.exe continues running in the background.
