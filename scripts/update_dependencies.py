#!/usr/bin/env python3
import subprocess
import os
import datetime


def setup_git_user(env=None) -> None:
    if env is None:
        env = os.environ.copy()

    github_actor = os.environ.get("GITHUB_ACTOR", "github-actions[bot]")
    # Fallback for local testing if GITHUB_ACTOR is not set
    if github_actor == "github-actions[bot]" and "GITHUB_ACTIONS" not in env:
        github_user_email = "actions@github.com"
    else:
        github_user_email = f"{github_actor}@users.noreply.github.com"

    print(f"Configuring git user as {github_actor} <{github_user_email}>")
    print(f"Running command: git config user.name {github_actor}")
    subprocess.run(
        ["git", "config", "user.name", github_actor],
        check=True,
        env=env,
    )
    print(f"Running command: git config user.email {github_user_email}")
    subprocess.run(
        ["git", "config", "user.email", github_user_email],
        check=True,
        env=env,
    )


def update_poetry_dependencies(env=None) -> None:
    if env is None:
        env = os.environ.copy()
    subprocess.run(
        ["poetry", "update"],
        check=True,
        env=env,
    )


def stage_and_commit_changes(commit_message: str, env=None) -> None:
    if env is None:
        env = os.environ.copy()
    subprocess.run(
        ["git", "add", "poetry.lock", "pyproject.toml"],
        check=True,
        env=env,
    )

    print(f"Running command: git commit -m {commit_message}")
    subprocess.run(
        ["git", "commit", "-m", commit_message],
        check=True,
        env=env,
    )


def git_diff(poetry_files: bool = False, env=None) -> subprocess.CompletedProcess:
    if env is None:
        env = os.environ.copy()
    files = ["poetry.lock", "pyproject.toml"] if poetry_files else []
    return subprocess.run(
        ["git", "status", "--porcelain", *files],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )


def create_branch(branch_name):
    print(f"Creating and switching to new branch: {branch_name}")
    print(f"Running command: git checkout -b {branch_name}")
    subprocess.run(
        ["git", "checkout", "-b", branch_name],
        check=True,
        env=os.environ.copy(),
    )
    # 5. Push the branch
    print(f"Pushing branch {branch_name} to origin...")
    print(f"Running command: git push origin {branch_name} --set-upstream")
    subprocess.run(
        ["git", "push", "origin", branch_name, "--set-upstream"],
        check=True,
        env=os.environ.copy(),
    )


def create_gh_pr(branch_name, pr_title, pr_body, default_branch="master", env=None):
    if env is None:
        env = os.environ.copy()
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
    token_env_dict = {}
    if "GITHUB_TOKEN" in env:
        token_env_dict["GH_TOKEN"] = env["GITHUB_TOKEN"]

    if token_env_dict:
        env.update(token_env_dict)

    print(f"Running command: {' '.join(gh_command)}")
    subprocess.run(gh_command, check=True, env=env)


def main():
    print("Starting dependency update process...")

    # Ensure Poetry is using the correct Python environment and not creating a venv if managed by workflow
    # This might be configured globally in the workflow already.
    # print("Running command: poetry config virtualenvs.create false")
    # subprocess.run(["poetry", "config", "virtualenvs.create", "false"], capture_output=True, text=True, check=True, env=os.environ.copy())

    # 1. Update dependencies
    print("Updating dependencies with 'poetry update'...")
    print("Running command: poetry update")
    update_poetry_dependencies()

    # 2. Check for changes
    print("Checking for changes in poetry.lock and pyproject.toml...")
    print("Running command: git status --porcelain poetry.lock pyproject.toml")
    status_result = git_diff(poetry_files=True)

    if not status_result.stdout.strip():
        print("No changes in poetry.lock or pyproject.toml. Exiting.")
        return

    print("Changes detected:")
    print(status_result.stdout)

    # 3. Configure git
    setup_git_user()

    # 4. Create a new branch
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    branch_name = f"chore/update-deps-{timestamp}"
    create_branch(branch_name)

    # 6. Add and commit changes
    print("Adding and committing poetry.lock and pyproject.toml...")
    print("Running command: git add poetry.lock pyproject.toml")
    stage_and_commit_changes(commit_message="chore: update python dependencies")

    # 7. Create a Pull Request
    pr_title = "chore: Update Python dependencies"
    pr_body = (
        "This PR was automatically created by a GitHub Action to update Python dependencies "
        "using `poetry update`. Please review the changes before merging."
    )

    default_branch = os.environ.get("DEFAULT_BRANCH", "master")
    print(f"Creating Pull Request from {branch_name} to {default_branch}...")
    create_gh_pr(branch_name, pr_title, pr_body, default_branch)
    print(f"Pull Request created for branch {branch_name} against {default_branch}.")


if __name__ == "__main__":
    main()
