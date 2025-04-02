# git_utils.py
import subprocess
import logging
import os
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

def run_git_command(command_list, cwd):
    logging.info(f"Running Git command: {' '.join(command_list)} in {cwd}")
    try:
        process = subprocess.run(command_list, cwd=cwd, check=True, capture_output=True, text=True, shell=(os.name != 'nt'))
        logging.info("Git command successful."); return True
    except FileNotFoundError: logging.error(f"Error: 'git' command not found..."); return False
    except subprocess.CalledProcessError as e:
        if "nothing to commit" in e.stderr.lower() or "no changes added to commit" in e.stderr.lower() or "nothing added to commit" in e.stdout.lower(): logging.info("Git: Nothing to commit."); return True
        logging.error(f"Error during Git execution: {e}\nGit stdout:\n{e.stdout}\nGit stderr:\n{e.stderr}"); return False
    except Exception as e: logging.error(f"An unexpected error occurred running Git command: {e}"); return False

def add_commit_push(repo_path, files_to_add_relative, commit_message):
    if not files_to_add_relative: logging.warning("Git: No files specified to add."); return False
    logging.info("-" * 50); logging.info("Attempting Git operations...")
    if not os.path.isdir(repo_path): logging.error(f"Error: Git repository path does not exist: {repo_path}"); return False

    logging.info("Pulling latest changes...")
    git_pull_command = ["git", "pull"]
    if not run_git_command(git_pull_command, cwd=repo_path):
        logging.error("Git pull failed."); return False

    git_add_command = ["git", "add"] + files_to_add_relative; logging.info(f"Staging files: {', '.join(files_to_add_relative)}")
    if not run_git_command(git_add_command, cwd=repo_path): logging.error("Git add failed."); return False
    logging.info(f"Committing with message: {commit_message}"); git_commit_command = ["git", "commit", "-m", commit_message]
    commit_success = run_git_command(git_commit_command, cwd=repo_path)
    if not commit_success: logging.warning("Git commit failed or nothing to commit.")
    logging.info("Pushing changes..."); git_push_command = ["git", "push"]
    if not run_git_command(git_push_command, cwd=repo_path): logging.error("Git push failed.") # Decide if this is critical
    else: logging.info("Git operations completed successfully.")
    logging.info("-" * 50); return True # Indicate Git sequence was attempted/completed

def get_azure_devops_client():
    personal_access_token = os.getenv("AZURE_DEVOPS_PAT")
    organization_url = os.getenv("AZURE_DEVOPS_ORG_URL")
    credentials = BasicAuthentication('', personal_access_token)
    connection = Connection(base_url=organization_url, creds=credentials)
    return connection.clients.get_git_client()

def get_pull_requests(project):
    client = get_azure_devops_client()
    prs = client.get_pull_requests(project)
    return prs

def get_tasks(project):
    client = get_azure_devops_client()
    tasks = client.get_work_items(project)
    return tasks

def get_task_changes(project):
    client = get_azure_devops_client()
    task_changes = client.get_work_item_changes(project)
    return task_changes

def post_pr_comment(project, pr_id, comment):
    client = get_azure_devops_client()
    response = client.create_comment(project, pr_id, comment)
    return response
