import os
import subprocess
import PyInstaller.__main__
import toml
import argparse
from rich.console import Console

console = Console()

def get_pyproject():
    with open("pyproject.toml", "r") as f:
        return toml.load(f)

def build_local():
    print("getting pyproject")
    pyproject = get_pyproject()

    print("getting dev packages")
    dev_packages = [
        package
        for package in pyproject["tool"]["poetry"]["group"]["dev"]["dependencies"]
        if package != "textual"
    ]
    print(f"found {len(dev_packages)} dev packages")

    print("run pyinstaller")
    PyInstaller.__main__.run(
        [
            "--name=app",
            "--add-data=dyna_cli/components/css:dyna_cli/components/css",
            *[f"--exclude-module={package}" for package in dev_packages],
            os.path.join("dyna_cli", "__main__.py"),
        ]
    )


def build_flatpak():
    parser = argparse.ArgumentParser(description="script to build flatpak image")
    parser.add_argument(
        "-g",
        "--gpg",
        help="the gpg key for signing",
    )
    parser.add_argument(
        "-gh",
        "--gpg-homedir",
        help="path to the custom gpg key home dir",
        dest="gpg_homedir",
    )
    parser.add_argument(
        "-i",
        "--install",
        action="store_true",
        help="will install built flatpak locally",
    )
    args = parser.parse_args()
    console.print(":clipboard: exporting requirements.txt from lockfile")

    if not os.path.exists('build'):
        os.mkdir('build')

    subprocess.run(
            [
                "poetry",
                "export",
                "-f",
                "requirements.txt",
                "-o",
                "build/requirements.txt",
            ]
    )
    
    console.print(":white_check_mark: exported to build/requirements.txt")

    console.print(":package: build flatpak in .flatpak folder")

    extra_args = []

    if args.gpg:
        extra_args.append(f"--gpg-sign={args.gpg}")

    if args.gpg_homedir:
        extra_args.append(f"--gpg-homedir={args.gpg_homedir}")

    if args.install:
        extra_args.append("--install")
    else:
        extra_args.extend(
            [
                "--repo",
                ".repo",
            ]
        )
    subprocess.run(
        [
            "flatpak-builder",
            "--force-clean",
            *extra_args,
            ".flatpak",
            "org.flatpak.dyna_cli.yaml",
        ]
    )
    console.print(":white_check_mark: built flatpak")
    if args.install:
        console.print("installed locally run \"flatpak run org.flatpak.dyna-cli\" to run app")
    else:
        with console.status("exporting flatpak to single file"):
            subprocess.run(
                ["flatpak", "build-bundle", ".repo", "dyna_cli.flatpak", "org.flatpak.dyna_cli"]
            )

        console.print(":white_check_mark: exported to single file in root directory")
