import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def get_env(key: str, default: str) -> str:
    val = os.getenv(key)
    if val is None:
        return default
    return val


def get_env_bool(key: str, default: bool) -> bool:
    value = get_env(key, "true" if default else "false").strip().lower()
    if value == "":
        return default
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return default


def parse_int_csv(value: str) -> list[int]:
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
    app_admin_default_passcode: str
    app_fullscreen_mode: bool
    app_screen_width: int
    app_screen_height: int

    # User Preferences
    locale: str
    default_sec_per_plate: float
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
    motor_ids: list[int]
    motor_directions: list[int]
    motor_command_hz: float
    motor_ramp_time_s: float
    motor_hold_release_timeout_s: float
    motor_plate_size_cm: float
    motor_min_sec_per_plate: float
    motor_max_sec_per_plate: float
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

        motor_ids = parse_int_csv(get_env("MOTOR_IDS", "1,2"))
        motor_directions = parse_int_csv(get_env("MOTOR_DIRECTIONS", "1,-1"))

        if not motor_ids:
            motor_ids = [1]

        return cls(
            _storage_path=storage_path,
            app_title=get_env("APP_TITLE", "Tango Motors Control"),
            app_admin_default_passcode=get_env("APP_ADMIN_DEFAULT_PASSCODE", "1010"),
            app_fullscreen_mode=get_env_bool("APP_FULLSCREEN_MODE", True),
            app_screen_width=max(320, int(get_env("APP_SCREEN_WIDTH", "800"))),
            app_screen_height=max(240, int(get_env("APP_SCREEN_HEIGHT", "480"))),
            locale=get_env("LOCALE", "fr").lower(),
            default_sec_per_plate=float(get_env("DEFAULT_SEC_PER_PLATE", "15")),
            admin_passcode_hash=get_env("ADMIN_PASSCODE_HASH", ""),
            asset_logo=get_env("ASSET_LOGO", "tango_logo.png"),
            asset_screensaver=get_env(
                "ASSET_SCREENSAVER", "regethermic_screensaver.png"
            ),
            inactivity_timeout=float(get_env("INACTIVITY_TIMEOUT", "30.0")),
            log_level=get_env("LOG_LEVEL", "INFO").upper(),
            motor_enabled=get_env_bool("MOTOR_ENABLED", False),
            motor_type=get_env("MOTOR_TYPE", "AK40-10"),
            motor_can_channel=get_env("MOTOR_CAN_CHANNEL", "can0"),
            motor_ids=motor_ids,
            motor_directions=motor_directions,
            motor_command_hz=float(get_env("MOTOR_COMMAND_HZ", "2.0")),
            motor_ramp_time_s=max(0.0, float(get_env("MOTOR_RAMP_TIME_S", "0.5"))),
            motor_hold_release_timeout_s=max(
                0.0, float(get_env("MOTOR_HOLD_RELEASE_TIMEOUT_S", "5.0"))
            ),
            motor_plate_size_cm=max(0.1, float(get_env("MOTOR_PLATE_SIZE_CM", "53"))),
            motor_min_sec_per_plate=float(get_env("MOTOR_MIN_SEC_PER_PLATE", "15")),
            motor_max_sec_per_plate=float(get_env("MOTOR_MAX_SEC_PER_PLATE", "40")),
            motor_max_temp_c=float(get_env("MOTOR_MAX_TEMP_C", "70.0")),
        )

    def set(self, key: str, value: object) -> None:
        """
        Updates a configuration value in memory and persists it to the storage file.
        """
        str_value: str = str(value)
        attr_name: str = key.lower()
        if hasattr(self, attr_name):
            current_val = getattr(self, attr_name)
            if isinstance(current_val, bool):
                setattr(
                    self,
                    attr_name,
                    str_value.strip().lower() in {"1", "true", "yes", "on"},
                )
            elif isinstance(current_val, list):
                setattr(self, attr_name, parse_int_csv(str_value))
            elif isinstance(current_val, int):
                setattr(self, attr_name, int(str_value))
            elif isinstance(current_val, float):
                setattr(self, attr_name, float(str_value))
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

        new_lines: list[str] = []
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
