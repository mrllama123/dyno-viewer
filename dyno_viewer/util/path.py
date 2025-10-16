import os
import platform
from pathlib import Path


def get_user_config_dir(app_name: str, app_author: str = None) -> Path:
    """
    Return a path to store user-specific configuration files for the given application,
    following platform conventions, without using any external dependency.

    :param app_name: name of the application (e.g. "MyApp")
    :param app_author: optional vendor/author name (on Windows, this helps to put under e.g. Author\\AppName)
    :return: Path object pointing to the config directory
    """

    home = Path.home()

    system = platform.system()
    system = system.lower()

    if system == "windows":
        # On Windows, prefer %LOCALAPPDATA% or %APPDATA%
        local_appdata = os.getenv("LOCALAPPDATA")
        roaming_appdata = os.getenv("APPDATA")

        # if app_author is given, we can namespace under it
        if local_appdata:
            base = Path(local_appdata)
        elif roaming_appdata:
            base = Path(roaming_appdata)
        else:
            # fallback to home
            base = home / "AppData" / "Local"

        if app_author:
            return base / app_author / app_name

        return base / app_name

    if system == "darwin":  # macOS
        # On macOS, commonly use ~/Library/Application Support/...
        library = home / "Library" / "Application Support"
        return library / app_name

    # treat everything else as Unix / Linux / BSD etc
    # Follow XDG Base Directory Spec:
    # Use $XDG_CONFIG_HOME if set, else default to ~/.config
    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_config_home and xdg_config_home.strip():
        base = Path(xdg_config_home)
    else:
        base = home / ".config"
    return base / app_name


def ensure_config_dir(app_name: str, app_author: str = None) -> Path:
    """
    Get the user config dir for the app and make sure it exists (mkdir).

    :param app_name: name of the application (e.g. "MyApp")
    :param app_author: optional vendor/author name (on Windows, this helps to put under e.g. Author\\AppName)
    :return: Path object pointing to the config directory
    """
    path = get_user_config_dir(app_name, app_author)
    path.mkdir(parents=True, exist_ok=True)
    return path
