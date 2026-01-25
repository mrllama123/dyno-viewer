from rich.console import Console
from dyno_viewer.constants import CONFIG_DIR_NAME
from dyno_viewer.util.path import get_user_config_dir
console = Console()


def get_app_path() -> None:
    """
    Get the path to the application directory.
    """
    console.print(f"User config path: {get_user_config_dir(CONFIG_DIR_NAME)}")


