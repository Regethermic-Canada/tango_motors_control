---
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

## Run the app

```bash
# Install dependencies from pyproject.toml
uv sync

# Run the application
uv run flet run
```

---

## Package the app

```bash
# executable will be in the /dist folder
uv run flet pack src/main.py
```

---
