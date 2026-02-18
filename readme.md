# tango_motors_control

---

## Using a raspberrypi 3 (weak support for openGL -> force cpu rendering)

```
export LIBGL_ALWAYS_SOFTWARE=1
```

---

## For all raspberrypi (debian based distro)

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
MOTOR_COMMAND_HZ=20
MOTOR_MIN_STEP_SPEED=-10
MOTOR_MAX_STEP_SPEED=10
MOTOR_SPEED_MIN=-100
MOTOR_SPEED_MAX=100
```

`MOTOR_IDS` and `MOTOR_DIRECTIONS` must have the same number of entries.
Example: `MOTOR_IDS=1,2,3,4` with `MOTOR_DIRECTIONS=1,-1,1,-1`.

In UI, speed is configurable with `MOTOR_MIN_STEP_SPEED..MOTOR_MAX_STEP_SPEED` and is
scaled to `MOTOR_SPEED_MIN..MOTOR_SPEED_MAX` (%).
Use the `Start Motors` / `Stop Motors` button to run or stop commands.

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
  --add-data "src/assets:assets" \
  --add-data "src/components:components" \
  --add-data "src/contexts:contexts" \
  --add-data "src/models:models" \
  --add-data "src/services:services" \
  --add-data "src/utils:utils" \
  --add-data "storage:storage"
```

---
