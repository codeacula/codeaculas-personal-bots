# git_utils.py
import subprocess
import os

def run_git_command(command_list, cwd):
    """ Runs a Git command using subprocess, checks for errors, returns True/False """
    print(f"Running Git command: {' '.join(command_list)} in {cwd}")
    try:
        process = subprocess.run(
            command_list, cwd=cwd, check=True, capture_output=True, text=True, shell=(os.name != 'nt') # Use shell=True cautiously if needed, maybe not here
        )
        print("Git command successful.")
        # Optional: print(process.stdout)
        # Optional: print(process.stderr)
        return True
    except FileNotFoundError:
        print(f"Error: 'git' command not found. Make sure Git is installed and in your system's PATH.")
        return False
    except subprocess.CalledProcessError as e:
        # Handle common "nothing to commit" case gracefully
        if "nothing to commit" in e.stderr.lower() or \
           "no changes added to commit" in e.stderr.lower() or \
           "nothing added to commit" in e.stdout.lower():
             print("Git: Nothing to commit.")
             return True # Treat as success for workflow continuation
        print(f"Error during Git execution: {e}")
        print(f"Git stdout:\n{e.stdout}")
        print(f"Git stderr:\n{e.stderr}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred running Git command: {e}")
        return False

def add_commit_push(repo_path, files_to_add_relative, commit_message):
    """ Stages, commits, and pushes specified files to the Git repository. """
    if not files_to_add_relative:
        print("Git: No files specified to add.")
        return False

    print("-" * 50)
    print("Attempting Git operations...")
    # Ensure repo path exists
    if not os.path.isdir(repo_path):
         print(f"Error: Git repository path does not exist: {repo_path}")
         return False

    # Stage files
    git_add_command = ["git", "add"] + files_to_add_relative
    print(f"Staging files: {', '.join(files_to_add_relative)}")
    if not run_git_command(git_add_command, cwd=repo_path):
        print("Git add failed.")
        return False

    # Commit
    print(f"Committing with message: {commit_message}")
    git_commit_command = ["git", "commit", "-m", commit_message]
    # Commit might fail if 'git add' didn't actually stage changes (e.g., file unchanged)
    # run_git_command handles the "nothing to commit" case now.
    if not run_git_command(git_commit_command, cwd=repo_path):
        print("Git commit failed or nothing to commit.")
        # Decide if workflow should continue if nothing was committed
        # For now, we'll allow it to proceed to push attempt,
        # as maybe only one file changed, or maybe upstream changed.
        # return False # Uncomment if commit *must* succeed to proceed

    # Push
    print("Pushing changes...")
    git_push_command = ["git", "push"]
    if not run_git_command(git_push_command, cwd=repo_path):
        print("Git push failed.")
        # Decide if this is critical - maybe network is down?
        # return False # Uncomment if push *must* succeed
    else:
        print("Git operations completed successfully.")

    print("-" * 50)
    return True # Indicate Git sequence was attempted/completed (even if nothing pushed)