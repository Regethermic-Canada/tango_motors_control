#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# kill_kiosk.sh -> Revert labwc kiosk autostart for tango_motors_control
#  - removes ~/.config/labwc/autostart
#  - switches LightDM session from labwc to rpd-labwc
###############################################################################

# Configuration
readonly HOME_DIR="${HOME}"
readonly LABWC_DIR="${HOME_DIR}/.config/labwc"
readonly AUTOSTART_FILE="${LABWC_DIR}/autostart"
readonly LIGHTDM_CONF="/etc/lightdm/lightdm.conf"

echo
echo "Reverting kiosk setup for tango_motors_control..."
echo

# 0) Remove labwc autostart script
echo "Removing kiosk autostart..."
if [[ -f "${AUTOSTART_FILE}" ]]; then
	rm -f "${AUTOSTART_FILE}"
	echo "Removed: ${AUTOSTART_FILE}"
else
	echo "Autostart not found: ${AUTOSTART_FILE}"
fi

# 1) Switch LightDM session from labwc -> rpd-labwc
echo "Updating LightDM session (labwc -> rpd-labwc)..."
sudo sed -i 's/\<labwc\>/rpd-labwc/g' "${LIGHTDM_CONF}"

# 2) Final summary
echo "Kiosk autostart removed (if present):"
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
