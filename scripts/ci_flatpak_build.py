import argparse
import os
import subprocess


def main():
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
    
    print(":white_check_mark: exported to build/requirements.txt")

    print(":package: build flatpak in .flatpak folder")

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
    print(":white_check_mark: built flatpak")
    if args.install:
        print("installed locally run \"flatpak run org.flatpak.dyna-cli\" to run app")
    else:
        subprocess.run(
            ["flatpak", "build-bundle", ".repo", "dyna_cli.flatpak", "org.flatpak.dyna_cli"]
        )

        print(":white_check_mark: exported to single file in root directory")


if __name__ == "__main__":
    main()