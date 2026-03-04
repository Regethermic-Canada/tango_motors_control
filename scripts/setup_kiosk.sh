#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# setup_kiosk.sh -> Configure labwc kiosk autostart for tango_motors_control
#  - ensures required packages are installed
#  - writes ~/.config/labwc/rc.xml for kiosk hardening
#  - writes ~/.config/labwc/autostart
#  - starts app from ${HOME}/tango_motors_control
#  - switches LightDM session from rpd-labwc to labwc
###############################################################################

# Configuration
readonly HOME_DIR="${HOME}"
readonly APP_DIR="${HOME_DIR}/tango_motors_control"
readonly APP_CMD="${HOME_DIR}/.local/bin/uv run flet run"
readonly LABWC_DIR="${HOME_DIR}/.config/labwc"
readonly AUTOSTART_FILE="${LABWC_DIR}/autostart"
readonly RC_FILE="${LABWC_DIR}/rc.xml"
readonly LIGHTDM_CONF="/etc/lightdm/lightdm.conf"

echo
echo "Starting kiosk setup for tango_motors_control..."
echo

# 0a) Ensure libmpv2 is present (required for flet media support)
if ! dpkg -s libmpv2 >/dev/null 2>&1; then
	echo "Installing libmpv2..."
	sudo apt update
	sudo apt install -y libmpv2 wtype
fi

# 0b) Ensure wtype is present (required for kiosk cursor hide binding)
if ! dpkg -s wtype >/dev/null 2>&1; then
	echo "Installing wtype..."
	sudo apt update
	sudo apt install -y wtype
fi

# TODO:
# Automate :
# 1) make the boot silent + plymouth custom logo
# 2) /boot/firmware/config.txt overlay for can0
# 3) systemd root service to up can0

# 1) Prepare labwc config directory
echo "Preparing labwc config directory..."
mkdir -p "${LABWC_DIR}"

# 2) Write labwc rc.xml (disable desktop context menu + define hide-cursor bind)
echo "Writing labwc kiosk rc.xml..."
cat >"${RC_FILE}" <<'EOF'
<?xml version="1.0"?>
<labwc_config>
  <mouse>
    <default/>
    <!-- Disable root menu on desktop background. -->
    <context name="Desktop">
      <mousebind button="Left" action="Press"/>
      <mousebind button="Left" action="Click"/>
      <mousebind button="Right" action="Press"/>
      <mousebind button="Right" action="Click"/>
      <mousebind button="Middle" action="Press"/>
      <mousebind button="Middle" action="Click"/>
    </context>
  </mouse>

  <keyboard>
    <default/>

    <!-- Clear a common menu shortcut if present. -->
    <keybind key="W-Space">
      <action name="None"/>
    </keybind>

    <!-- Kiosk cursor hide: move pointer to output corner, then hide. -->
    <keybind key="W-F12">
      <action name="WarpCursor" to="output" x="-1" y="-1"/>
      <action name="HideCursor"/>
    </keybind>
  </keyboard>
</labwc_config>
EOF

# 3) Write labwc autostart script
echo "Writing kiosk autostart..."
cat >"${AUTOSTART_FILE}" <<EOF
#!/usr/bin/env bash

export NO_AT_BRIDGE=1

# Trigger the labwc hide-cursor binding a few times during startup.
# This reduces brief cursor flashes while session/app surfaces initialize.
if command -v wtype >/dev/null 2>&1; then
  (
    wtype -M logo -k F12 -m logo || true
    wtype -s 200 -M logo -k F12 -m logo || true
    wtype -s 500 -M logo -k F12 -m logo || true
  ) >/dev/null 2>&1 &
fi

cd "${APP_DIR}"
exec /usr/bin/env bash -lc $(printf '%q' "${APP_CMD}")
EOF
chmod +x "${AUTOSTART_FILE}"

# 4) Switch LightDM session from rpd-labwc -> labwc
echo "Updating LightDM session (rpd-labwc -> labwc)..."
sudo sed -i 's/\<rpd-labwc\>/labwc/g' "${LIGHTDM_CONF}"

# 5) Final summary
echo
echo "Required media packages checked:"
echo "  - libmpv2"
echo "  - wtype"
echo
echo "Kiosk rc.xml written:"
echo "  ${RC_FILE}"
echo
echo "Kiosk autostart written:"
echo "  ${AUTOSTART_FILE}"
echo
echo "LightDM session updated in:"
echo "  ${LIGHTDM_CONF}"
echo

echo "The system will reboot in:"
for i in {5..1}; do
	echo "  -> ${i} s"
	sleep 1
done

exec sudo reboot
