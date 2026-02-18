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
MOTOR_1_ID=1
MOTOR_2_ID=2
MOTOR_1_DIRECTION=1
MOTOR_2_DIRECTION=-1
```

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
