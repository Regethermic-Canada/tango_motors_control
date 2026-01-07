---
# tango_motors_control
---

## Using a raspberrypi 3 (weak support for openGL -> force cpu rendering)

```
export LIBGL_ALWAYS_SOFTWARE=1
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

```
# executable will be in the /dist folder
uv run flet pack main.py
```

---
