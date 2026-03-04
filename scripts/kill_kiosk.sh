#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# kill_kiosk.sh -> Revert labwc kiosk autostart for tango_motors_control
#  - removes ~/.config/labwc/autostart
#  - removes ~/.config/labwc/rc.xml
#  - switches LightDM session from labwc to rpd-labwc
###############################################################################

# Configuration
readonly HOME_DIR="${HOME}"
readonly LABWC_DIR="${HOME_DIR}/.config/labwc"
readonly AUTOSTART_FILE="${LABWC_DIR}/autostart"
readonly RC_FILE="${LABWC_DIR}/rc.xml"
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

# 1) Remove labwc kiosk rc.xml
echo "Removing kiosk rc.xml..."
if [[ -f "${RC_FILE}" ]]; then
	rm -f "${RC_FILE}"
	echo "Removed: ${RC_FILE}"
else
	echo "rc.xml not found: ${RC_FILE}"
fi

# 2) Switch LightDM session from labwc -> rpd-labwc
echo "Updating LightDM session (labwc -> rpd-labwc)..."
sudo sed -i 's/\<labwc\>/rpd-labwc/g' "${LIGHTDM_CONF}"

# 3) Final summary
echo "Kiosk autostart removed (if present):"
echo "  ${AUTOSTART_FILE}"
echo
echo "Kiosk rc.xml removed (if present):"
echo "  ${RC_FILE}"
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
