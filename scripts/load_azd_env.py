import json
import logging
import subprocess

from dotenv import load_dotenv

logger = logging.getLogger("scripts")


def load_azd_env():
    """Get path to current azd env file and load file using python-dotenv.

    Gracefully handles missing azd configuration and falls back to .env file.
    """
    result = subprocess.run("azd env list -o json", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logger.warning(
            "azd env not configured. To set up Azure deployment, run: azd env new\n"
            "For development without Azure, environment variables will be loaded from .env file instead."
        )
        # Fall back to loading .env from current directory
        from pathlib import Path

        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            logger.info(f"Loading environment variables from {env_file}")
            load_dotenv(env_file, override=True)
        return

    try:
        env_json = json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.warning(
            "Failed to parse azd env output. Using .env file instead.\n"
            "Run 'azd env new' to create an Azure environment."
        )
        from pathlib import Path

        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            logger.info(f"Loading environment variables from {env_file}")
            load_dotenv(env_file, override=True)
        return

    env_file_path = None
    for entry in env_json:
        if entry.get("IsDefault"):
            env_file_path = entry.get("DotEnvPath")
            break

    if not env_file_path:
        logger.warning(
            "No default azd env file found. Using .env file instead.\n"
            "Run 'azd env new' to create an Azure environment."
        )
        from pathlib import Path

        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            logger.info(f"Loading environment variables from {env_file}")
            load_dotenv(env_file, override=True)
        return

    logger.info(f"Loading azd env from {env_file_path}")
    load_dotenv(env_file_path, override=True)
