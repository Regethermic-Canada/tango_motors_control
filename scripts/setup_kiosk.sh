#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# setup_kiosk.sh -> Configure labwc kiosk autostart for tango_motors_control
#  - ensures libmpv2 is installed
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
readonly LIGHTDM_CONF="/etc/lightdm/lightdm.conf"

echo
echo "Starting kiosk setup for tango_motors_control..."
echo

# 0) Ensure libmpv2 is present
if ! dpkg -s libmpv2 >/dev/null 2>&1; then
	echo "Installing libmpv2..."
	sudo apt update
	sudo apt install -y libmpv2
fi

# TODO:
# here i should also automate the steps to make the boot silent + plymouth custom logo, but for now let's just do the kiosk setup

# 1) Prepare labwc config directory
echo "Preparing labwc config directory..."
mkdir -p "${LABWC_DIR}"

# 2) Write labwc autostart script
echo "Writing kiosk autostart..."
cat >"${AUTOSTART_FILE}" <<EOF
#!/usr/bin/env bash

export NO_AT_BRIDGE=1
cd "${APP_DIR}"
exec /usr/bin/env bash -lc $(printf '%q' "${APP_CMD}")
EOF
chmod +x "${AUTOSTART_FILE}"

# 3) Switch LightDM session from rpd-labwc -> labwc
echo "Updating LightDM session (rpd-labwc -> labwc)..."
sudo sed -i 's/\<rpd-labwc\>/labwc/g' "${LIGHTDM_CONF}"

# 4) Final summary
echo "Required media packages checked:"
echo "  - libmpv2"
echo
echo "Kiosk autostart written:"
echo "  ${AUTOSTART_FILE}"
echo
echo "LightDM session updated in:"
echo "  ${LIGHTDM_CONF}"
echo

echo "The system will shut down in:"
for i in {5..1}; do
	echo "  -> ${i} s"
	sleep 1
done

exec sudo reboot
