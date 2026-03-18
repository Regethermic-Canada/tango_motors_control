import logging

import flet as ft
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from .i18n import I18nService
from utils.config import config

logger = logging.getLogger(__name__)


@ft.observable
class SettingsService:
    def __init__(self, i18n_service: I18nService) -> None:
        self._i18n_service = i18n_service
        self._password_hasher = PasswordHasher()
        self.default_speed_max = abs(config.motor_max_step_speed)
        self.default_speed_min = -self.default_speed_max
        self.locale = config.locale.lower()
        self.locale_version = 0
        self.translations = self._i18n_service.translations_for(self.locale)
        self.default_speed = self._clamp_default_speed(config.default_speed)
        self.inactivity_timeout = config.inactivity_timeout

    def set_locale(self, locale: str) -> None:
        normalized_locale = locale.lower()
        if self.locale == normalized_locale:
            return

        self.locale = normalized_locale
        self.translations = self._i18n_service.translations_for(normalized_locale)
        self.locale_version += 1
        config.set("LOCALE", normalized_locale)
        logger.info("Locale changed to %s", self.locale)

    def t(self, key: str, default: str | None = None) -> str:
        return self.translations.get(key, default or key)

    def set_inactivity_timeout(self, seconds: float) -> None:
        if self.inactivity_timeout == seconds:
            return

        self.inactivity_timeout = seconds
        config.set("INACTIVITY_TIMEOUT", seconds)
        logger.info("Inactivity timeout changed to %ss", self.inactivity_timeout)

    def set_default_speed(self, speed: int) -> None:
        normalized_speed = self._clamp_default_speed(speed)
        if self.default_speed == normalized_speed:
            return

        self.default_speed = normalized_speed
        config.set("DEFAULT_SPEED", normalized_speed)
        logger.info("Default speed changed to %s", self.default_speed)

    def update_admin_passcode(self, new_passcode: str) -> None:
        new_hash = self._password_hasher.hash(new_passcode)
        config.set("ADMIN_PASSCODE_HASH", new_hash)
        logger.info("Admin passcode updated and persisted")

    def verify_admin_passcode(self, passcode: str) -> bool:
        stored_hash = config.admin_passcode_hash
        default_passcode = config.app_admin_default_passcode

        try:
            if not stored_hash:
                if passcode != default_passcode:
                    return False
                config.set(
                    "ADMIN_PASSCODE_HASH",
                    self._password_hasher.hash(passcode),
                )
                return True

            self._password_hasher.verify(stored_hash, passcode)
            return True
        except VerifyMismatchError:
            return False
        except Exception:
            logger.exception("Admin passcode verification failed")
            return False

    def _clamp_default_speed(self, speed: int) -> int:
        return max(self.default_speed_min, min(speed, self.default_speed_max))
