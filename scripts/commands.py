import os

import PyInstaller.__main__
import toml
from rich.console import Console

console = Console()


def get_pyproject():
    with open("pyproject.toml") as f:
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
            "--add-data=dyno_viewer/components/css:dyno_viewer/components/css",
            *[f"--exclude-module={package}" for package in dev_packages],
            os.path.join("dyno_viewer", "__main__.py"),
        ]
    )
