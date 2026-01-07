---
# tango_motors_control
---

## Using a raspberrypi 3 (weak support for openGL -> force cpu rendering)

```
export LIBGL_ALWAYS_SOFTWARE=1
```

---

## Run the app

```
uv pip install -r requirements.txt
uv run flet run
```

---

## Package the app

```
# executable will be in the /dist folder
uv run flet pack main.py
```

---
