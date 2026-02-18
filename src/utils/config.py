import os
import re
import shutil
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


def get_env_bool(key: str, default: bool) -> bool:
    value = get_env(key, "true" if default else "false").strip().lower()
    return value in {"1", "true", "yes", "on"}


def parse_int_csv(value: str) -> List[int]:
    tokens = [token.strip() for token in value.split(",") if token.strip()]
    return [int(token) for token in tokens]


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

    # Motor Control
    motor_enabled: bool
    motor_type: str
    motor_can_channel: str
    motor_ids: List[int]
    motor_directions: List[int]
    motor_command_hz: float
    motor_max_step_speed: int
    motor_max_speed: int
    motor_max_temp_c: float

    _storage_path: Path

    @classmethod
    def load(cls) -> "Config":
        """
        Load configuration from the storage file, initializing the singleton.
        """
        is_frozen = getattr(sys, "frozen", False)

        if is_frozen:
            # Bundle directory (contains assets and templates)
            bundle_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))

            if sys.platform.startswith("linux"):
                # Linux XDG Standard: ~/.config/tango_motors_control/data
                config_home = Path(
                    os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
                )
                storage_path = config_home / "tango_motors_control" / "data"
            else:
                # Other OS builds: store in a 'storage' folder next to the executable
                storage_path = Path(sys.executable).parent / "storage" / "data"

            if not storage_path.exists():
                storage_path.parent.mkdir(parents=True, exist_ok=True)
                # Try to find a pre-configured 'data' or the 'data.template' in the bundle
                for source_name in ["data", "data.template"]:
                    source_path = bundle_dir / "storage" / source_name
                    if source_path.exists():
                        shutil.copy(source_path, storage_path)
                        break
        else:
            project_root = Path(__file__).resolve().parents[2]
            storage_path = project_root / "storage" / "data"
            storage_path.parent.mkdir(parents=True, exist_ok=True)

        if storage_path.exists():
            load_dotenv(dotenv_path=storage_path, override=True)

        return cls(
            _storage_path=storage_path,
            **cls._load_identity(),
            **cls._load_preferences(),
            **cls._load_assets(),
            **cls._load_behavior(),
            **cls._load_motor_control(),
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
            "default_speed": int(get_env("DEFAULT_SPEED", "0")),
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

    @staticmethod
    def _load_motor_control() -> Dict[str, Any]:
        motor_ids = parse_int_csv(get_env("MOTOR_IDS", "1,2"))
        motor_directions = parse_int_csv(get_env("MOTOR_DIRECTIONS", "1,-1"))

        if not motor_ids:
            motor_ids = [1]

        return {
            "motor_enabled": get_env_bool("MOTOR_ENABLED", False),
            "motor_type": get_env("MOTOR_TYPE", "AK40-10"),
            "motor_can_channel": get_env("MOTOR_CAN_CHANNEL", "can0"),
            "motor_ids": motor_ids,
            "motor_directions": motor_directions,
            "motor_command_hz": float(get_env("MOTOR_COMMAND_HZ", "2.0")),
            "motor_max_step_speed": int(get_env("MOTOR_MAX_STEP_SPEED", "10")),
            "motor_max_speed": int(get_env("MOTOR_MAX_SPEED", "100")),
            "motor_max_temp_c": float(get_env("MOTOR_MAX_TEMP_C", "70.0")),
        }

    def set(self, key: str, value: Any) -> None:
        """
        Updates a configuration value in memory and persists it to the storage file.
        """
        str_value: str = str(value)
        attr_name: str = key.lower()
        if hasattr(self, attr_name):
            current_val: Any = getattr(self, attr_name)
            if isinstance(current_val, bool):
                setattr(
                    self,
                    attr_name,
                    str_value.strip().lower() in {"1", "true", "yes", "on"},
                )
            elif isinstance(current_val, list):
                setattr(self, attr_name, parse_int_csv(str_value))
            elif isinstance(current_val, int):
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
