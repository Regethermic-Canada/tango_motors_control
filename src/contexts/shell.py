from __future__ import annotations

from dataclasses import dataclass

import flet as ft

from services.app.shell import ShellService


@dataclass(frozen=True)
class ShellContextValue:
    service: ShellService | None = None

    def current(self) -> ShellService:
        if self.service is None:
            raise RuntimeError("ShellContext is not configured")
        return self.service


ShellContext = ft.create_context(ShellContextValue())
