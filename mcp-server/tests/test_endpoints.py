import sys
import tempfile
from pathlib import Path

# Add the MCP server src directory to PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from fastapi.testclient import TestClient
from mcp_server.src.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "version": "0.1.0"}


def test_transcribe_endpoint():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file_path = Path(temp_dir) / "test_video.mp4"
        with open(test_file_path, "wb") as f:
            f.write(b"dummy video content")

        with open(test_file_path, "rb") as f:
            response = client.post("/mcp/transcribe", files={"file": ("test_video.mp4", f)})

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"


def test_get_job_status():
    job_id = "dummy-job-id"
    response = client.get(f"/mcp/jobs/{job_id}")
    assert response.status_code == 200 or response.status_code == 404


def test_delete_job():
    job_id = "dummy-job-id"
    response = client.delete(f"/mcp/jobs/{job_id}")
    assert response.status_code == 200 or response.status_code == 404