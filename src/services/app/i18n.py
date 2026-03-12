import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class I18nService:
    def __init__(self, lang_root: Path | None = None) -> None:
        project_root = Path(__file__).resolve().parents[2]
        self._lang_root = lang_root or (project_root / "assets" / "lang")
        self._default_locale = "en"
        self._default_translations = self._read_locale_file(self._default_locale)

    def translations_for(self, locale: str) -> dict[str, str]:
        normalized_locale = locale.lower()
        if normalized_locale == self._default_locale:
            return dict(self._default_translations)

        translations = dict(self._default_translations)
        translations.update(self._read_locale_file(normalized_locale))
        return translations

    def _read_locale_file(self, locale: str) -> dict[str, str]:
        lang_file = self._lang_root / f"{locale}.json"
        if not lang_file.exists():
            logger.error("Translation file not found: %s", lang_file)
            return {}

        with open(lang_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            logger.error("Translation file is not a dictionary: %s", lang_file)
            return {}

        return {
            str(key): str(value)
            for key, value in data.items()
            if isinstance(key, str) and isinstance(value, str)
        }
