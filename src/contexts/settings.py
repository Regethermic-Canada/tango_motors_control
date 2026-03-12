from __future__ import annotations

from dataclasses import dataclass

import flet as ft

from services.app.settings import SettingsService


@dataclass(frozen=True)
class SettingsContextValue:
    service: SettingsService | None = None

    def current(self) -> SettingsService:
        if self.service is None:
            raise RuntimeError("SettingsContext is not configured")
        return self.service


SettingsContext = ft.create_context(SettingsContextValue())
