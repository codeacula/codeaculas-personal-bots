import pytest
from unittest.mock import patch, MagicMock
from transcribe_meeting.git_utils import run_git_command, add_commit_push

@patch("subprocess.run")
def test_run_git_command_success(mock_run):
    mock_run.return_value.returncode = 0
    result = run_git_command(["git", "status"], "test_repo")
    assert result is True

@patch("subprocess.run")
def test_run_git_command_failure(mock_run):
    mock_run.side_effect = Exception("Git command failed")
    result = run_git_command(["git", "status"], "test_repo")
    assert result is False

@patch("os.path.isdir", return_value=True)
@patch("transcribe_meeting.git_utils.run_git_command")
def test_add_commit_push_success(mock_run_git_command, mock_isdir):
    mock_run_git_command.return_value = True
    result = add_commit_push("test_repo", ["file1.txt", "file2.txt"], "Test commit")
    assert result is True

@patch("os.path.isdir", return_value=True)
@patch("transcribe_meeting.git_utils.run_git_command")
def test_add_commit_push_failure(mock_run_git_command, mock_isdir):
    mock_run_git_command.return_value = False
    result = add_commit_push("test_repo", ["file1.txt", "file2.txt"], "Test commit")
    assert result is False