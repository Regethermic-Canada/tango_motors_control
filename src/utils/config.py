import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
from dotenv import load_dotenv


def get_env(key: str, default: str) -> str:
    val = os.getenv(key)
    if val is None:
        return default
    return val


@dataclass
class Config:
    """
    Configuration object populated from the 'data' file in storage.
    Includes persistence logic for user preferences.
    """

    # App
    app_title: str
    app_version: str
    app_admin_default_passcode: str

    # User Preferences
    theme_mode: str
    theme_color: str
    locale: str
    default_speed: int
    admin_passcode_hash: str

    # Assets
    asset_logo: str
    asset_screensaver: str

    # Behavior
    inactivity_timeout: float
    log_level: str

    _storage_path: Path

    @classmethod
    def load(cls) -> "Config":
        """
        Load configuration from the storage file, initializing the singleton.
        """
        if getattr(sys, "frozen", False):
            # Running as a packaged executable
            # Use the directory where the executable is located for persistent data
            project_root = Path(sys.executable).parent
        else:
            # Running in normal development environment
            project_root = Path(__file__).resolve().parent.parent.parent

        storage_path: Path = project_root / "storage" / "data"

        # Create storage directory if it doesn't exist (important for packaged apps)
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        if storage_path.exists():
            load_dotenv(dotenv_path=storage_path, override=True)

        return cls(
            _storage_path=storage_path,
            **cls._load_identity(),
            **cls._load_preferences(),
            **cls._load_assets(),
            **cls._load_behavior(),
        )

    @staticmethod
    def _load_identity() -> Dict[str, Any]:
        return {
            "app_title": get_env("APP_TITLE", "Tango Motors Control"),
            "app_version": get_env("APP_VERSION", "0.1.0"),
            "app_admin_default_passcode": get_env("APP_ADMIN_DEFAULT_PASSCODE", "1010"),
        }

    @staticmethod
    def _load_preferences() -> Dict[str, Any]:
        return {
            "theme_mode": get_env("THEME_MODE", "DARK").upper(),
            "theme_color": get_env("THEME_COLOR", "BLUE").upper(),
            "locale": get_env("LOCALE", "fr").lower(),
            "default_speed": int(get_env("DEFAULT_SPEED", "50")),
            "admin_passcode_hash": get_env("ADMIN_PASSCODE_HASH", ""),
        }

    @staticmethod
    def _load_assets() -> Dict[str, Any]:
        return {
            "asset_logo": get_env("ASSET_LOGO", "tango_logo.png"),
            "asset_screensaver": get_env(
                "ASSET_SCREENSAVER", "regethermic_screensaver.png"
            ),
        }

    @staticmethod
    def _load_behavior() -> Dict[str, Any]:
        return {
            "inactivity_timeout": float(get_env("INACTIVITY_TIMEOUT", "30.0")),
            "log_level": get_env("LOG_LEVEL", "INFO").upper(),
        }

    def set(self, key: str, value: Any) -> None:
        """
        Updates a configuration value in memory and persists it to the storage file.
        """
        str_value: str = str(value)
        attr_name: str = key.lower()
        if hasattr(self, attr_name):
            current_val: Any = getattr(self, attr_name)
            if isinstance(current_val, int):
                setattr(self, attr_name, int(value))
            elif isinstance(current_val, float):
                setattr(self, attr_name, float(value))
            else:
                setattr(self, attr_name, str_value)

        os.environ[key] = str_value
        self._write_to_file(key, str_value)

    def _write_to_file(self, key: str, value: str) -> None:
        if not self._storage_path.exists():
            with open(self._storage_path, "w") as f:
                f.write(f"{key}={value}\n")
            return

        with open(self._storage_path, "r") as f:
            lines = f.readlines()

        new_lines: List[str] = []
        key_found = False
        pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")

        for line in lines:
            if pattern.match(line):
                new_lines.append(f"{key}={value}\n")
                key_found = True
            else:
                new_lines.append(line)

        if not key_found:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines[-1] += "\n"
            new_lines.append(f"{key}={value}\n")

        with open(self._storage_path, "w") as f:
            f.writelines(new_lines)


config: Config = Config.load()
