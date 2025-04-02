# git_utils.py
"""Git utility functions for managing repository operations."""
import subprocess
import logging
import os


def run_git_command(command_list, cwd):
    """Run a Git command and handle errors gracefully."""
    logging.info(f"Running Git command: {' '.join(command_list)} in {cwd}")
    try:
        result = subprocess.run(
            command_list,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            shell=(os.name != 'nt')
        )
        logging.info("Git command successful.")
        return True
    except FileNotFoundError:
        logging.error("Error: 'git' command not found...")
        return False
    except subprocess.CalledProcessError as e:
        if any(msg in e.stderr.lower() for msg in [
            "nothing to commit",
            "no changes added to commit",
            "nothing added to commit"
        ]):
            logging.info("Git: Nothing to commit.")
            return True
        logging.error(
            f"Error during Git execution: {e}\n"
            f"Git stdout:\n{e.stdout}\n"
            f"Git stderr:\n{e.stderr}"
        )
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred running Git command: {e}")
        return False


def add_commit_push(repo_path, files_to_add_relative, commit_message):
    """Add, commit, and push changes to the Git repository.

    Args:
        repo_path: Path to the Git repository
        files_to_add_relative: List of files to add (relative paths)
        commit_message: Commit message

    Returns:
        bool: True if all operations succeeded, False otherwise
    """
    if not files_to_add_relative:
        logging.warning("Git: No files specified to add.")
        return False

    logging.info("-" * 50)
    logging.info("Attempting Git operations...")

    if not os.path.isdir(repo_path):
        logging.error(f"Error: Git repository path does not exist: {repo_path}")
        return False

    # Pull latest changes
    logging.info("Pulling latest changes...")
    if not run_git_command(["git", "pull"], cwd=repo_path):
        logging.error("Git pull failed.")
        return False

    # Stage files
    logging.info(f"Staging files: {', '.join(files_to_add_relative)}")
    if not run_git_command(["git", "add"] + files_to_add_relative, cwd=repo_path):
        logging.error("Git add failed.")
        return False

    # Commit changes
    logging.info(f"Committing with message: {commit_message}")
    commit_success = run_git_command(
        ["git", "commit", "-m", commit_message],
        cwd=repo_path
    )
    if not commit_success:
        logging.warning("Git commit failed or nothing to commit.")

    # Push changes
    logging.info("Pushing changes...")
    if not run_git_command(["git", "push"], cwd=repo_path):
        logging.error("Git push failed.")
    else:
        logging.info("Git operations completed successfully.")

    logging.info("-" * 50)
    return True