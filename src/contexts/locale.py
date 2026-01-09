from collections.abc import Callable
from dataclasses import dataclass

import flet as ft


@dataclass(frozen=True)
class LocaleContextValue:
    locale: str
    translations: dict[str, str]
    set_locale: Callable[[str], None]

    def t(self, key: str, default: str | None = None) -> str:
        return self.translations.get(key, default or key)


LocaleContext = ft.create_context(
    LocaleContextValue(
        locale="en",
        translations={},
        set_locale=lambda _: None,
    )
)
