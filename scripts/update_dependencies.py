#!/usr/bin/env python3
import subprocess
import os
import datetime


def run_command(command, env=None):
    print(f"Running command: {' '.join(command)}")
    process_env = os.environ.copy()
    if env:
        process_env.update(env)

    result = subprocess.run(
        command, capture_output=True, text=True, check=True, env=process_env
    )

    if result.returncode != 0:
        print(f"Error running command: {' '.join(command)}")
        print(f"Return Code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        raise subprocess.CalledProcessError(
            result.returncode, command, result.stdout, result.stderr
        )
    return result


def main():
    print("Starting dependency update process...")

    # Ensure Poetry is using the correct Python environment and not creating a venv if managed by workflow
    # This might be configured globally in the workflow already.
    # run_command(["poetry", "config", "virtualenvs.create", "false"])

    # 1. Update dependencies
    print("Updating dependencies with 'poetry update'...")
    run_command(["poetry", "update"])

    # 2. Check for changes
    print("Checking for changes in poetry.lock and pyproject.toml...")
    status_result = run_command(
        ["git", "status", "--porcelain", "poetry.lock", "pyproject.toml"]
    )

    if not status_result.stdout.strip():
        print("No changes in poetry.lock or pyproject.toml. Exiting.")
        return

    print("Changes detected:")
    print(status_result.stdout)

    # 3. Configure git
    github_actor = os.environ.get("GITHUB_ACTOR", "github-actions[bot]")
    # Fallback for local testing if GITHUB_ACTOR is not set
    if github_actor == "github-actions[bot]" and "GITHUB_ACTIONS" not in os.environ:
        github_user_email = "actions@github.com"
    else:
        github_user_email = f"{github_actor}@users.noreply.github.com"

    print(f"Configuring git user as {github_actor} <{github_user_email}>")
    run_command(["git", "config", "user.name", github_actor])
    run_command(["git", "config", "user.email", github_user_email])

    # 4. Create a new branch
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    branch_name = f"chore/update-deps-{timestamp}"
    print(f"Creating and switching to new branch: {branch_name}")
    run_command(["git", "checkout", "-b", branch_name])

    # 5. Add and commit changes
    print("Adding and committing poetry.lock and pyproject.toml...")
    run_command(["git", "add", "poetry.lock", "pyproject.toml"])
    commit_message = "chore: update python dependencies"
    run_command(["git", "commit", "-m", commit_message])

    # 6. Push the branch
    print(f"Pushing branch {branch_name} to origin...")
    run_command(["git", "push", "origin", branch_name, "--set-upstream"])

    # 7. Create a Pull Request
    pr_title = "chore: Update Python dependencies"
    pr_body = (
        "This PR was automatically created by a GitHub Action to update Python dependencies "
        "using `poetry update`. Please review the changes before merging."
    )

    default_branch = os.environ.get("DEFAULT_BRANCH", "main")
    print(f"Creating Pull Request from {branch_name} to {default_branch}...")

    # GITHUB_TOKEN is automatically used by gh if set in env.
    # The workflow must provide GITHUB_TOKEN with appropriate permissions.
    gh_command = [
        "gh",
        "pr",
        "create",
        "--title",
        pr_title,
        "--body",
        pr_body,
        "--base",
        default_branch,
        "--head",
        branch_name,
    ]

    # Pass GITHUB_TOKEN explicitly to gh via env for this command,
    # ensuring it uses the token from the workflow.
    token_env = {}
    if "GITHUB_TOKEN" in os.environ:
        token_env["GH_TOKEN"] = os.environ["GITHUB_TOKEN"]

    run_command(gh_command, env=token_env)
    print(f"Pull Request created for branch {branch_name} against {default_branch}.")


if __name__ == "__main__":
    main()
