# tango_motors_control

---

## For all raspberrypi (debian based distro) -> for rendering

```
sudo apt install libmpv2
```

---

## For the can hat -> follow those instructions :

- https://www.waveshare.com/wiki/RS485_CAN_HAT

---

## Run the app

```bash
# Create a copy of data.template to data (.env in flet)
cp storage/data.template storage/data

# Install dependencies from pyproject.toml
uv sync

# Run the application
uv run flet run
```

---

## Motor control config

Motor control is disabled by default for safety. In `storage/data`:

```ini
MOTOR_ENABLED=true
MOTOR_TYPE=AK40-10
MOTOR_CAN_CHANNEL=can0
MOTOR_IDS=1,2
MOTOR_DIRECTIONS=1,-1
MOTOR_COMMAND_HZ=2
MOTOR_RAMP_TIME_S=0.5
MOTOR_HOLD_RELEASE_TIMEOUT_S=5.0
MOTOR_TRAY_SIZE_CM=53
MOTOR_MIN_SEC_PER_TRAY=15
MOTOR_MAX_SEC_PER_TRAY=40
DEFAULT_SEC_PER_TRAY=15
```

`MOTOR_RAMP_TIME_S` is the time used to slew from `0 rad/s` to the fastest configured
tray-time target. Internally the app converts `seconds/tray` into target `rad/s`.
Start, stop, and live speed changes use the same ramp so the motors do not step abruptly.
`MOTOR_HOLD_RELEASE_TIMEOUT_S` controls how long stop holds `0 rad/s` before auto-release.

`MOTOR_IDS` and `MOTOR_DIRECTIONS` must have the same number of entries.
Example: `MOTOR_IDS=1,2,3,4` with `MOTOR_DIRECTIONS=1,-1,1,-1`.

In UI, tray speed is configurable with `MOTOR_MIN_SEC_PER_TRAY..MOTOR_MAX_SEC_PER_TRAY`.
The slider stays in `seconds/tray`, and the UI also shows the derived `trays/minute`
indicator underneath. `Start Motors` / `Stop Motors` handles run state.

For complete motor/CAN setup (hardware wiring, CAN interface bring-up, usage and safety flow),
follow the CubeMars library repository documentation:

- https://github.com/sam0rr/cubemars_servo_can

---

## Check the code quality

1.  **Install dependencies:**

    ```bash
    uv sync
    ```

2.  **Check the types:**

    ```bash
    uv run mypy --strict src/
    ```

3.  **Run linters and formatters:**
    ```bash
    uv run black . && uv run ruff check .
    ```

---

## Package the app

```bash
# executable will be in the /dist folder
uv run flet pack src/main.py \
  --yes \
  --name tango_motors_control \
  --icon src/assets/icon.png \
  --pyinstaller-build-args=--paths=src \
  --add-data "src/assets:assets" \
  --add-data "storage:storage"
```

---
