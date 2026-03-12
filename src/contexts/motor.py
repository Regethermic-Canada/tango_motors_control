from __future__ import annotations

from dataclasses import dataclass

import flet as ft

from services.motors.controller import MotorController


@dataclass(frozen=True)
class MotorContextValue:
    controller: MotorController | None = None

    def current(self) -> MotorController:
        if self.controller is None:
            raise RuntimeError("MotorContext is not configured")
        return self.controller


MotorContext = ft.create_context(MotorContextValue())
