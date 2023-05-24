import os
import toml
import subprocess
import PyInstaller.__main__


def get_pyproject():
    with open("pyproject.toml", "r") as f:
        return toml.load(f)


def main():
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

