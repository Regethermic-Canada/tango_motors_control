#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# kill_kiosk.sh -> Revert labwc kiosk autostart for tango_motors_control
#  - removes CAN overlay lines from /boot/firmware/config.txt
#  - disables/removes systemd can0.service
#  - restores Plymouth splash screen from backup
#  - removes ~/.config/labwc/rc.xml
#  - removes ~/.config/labwc/autostart
#  - switches LightDM session from labwc to rpd-labwc
###############################################################################

# Configuration
readonly HOME_DIR="${HOME}"
readonly BOOT_CONFIG="/boot/firmware/config.txt"
readonly CAN_SPI_LINE="dtparam=spi=on"
readonly CAN_OVERLAY_LINE="dtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25,spimaxfrequency=2000000"
readonly UNIT_DIR="/etc/systemd/system"
readonly CAN_SERVICE_NAME="can0.service"
readonly PLYMOUTH_SPLASH_DST="/usr/share/plymouth/themes/pix/splash.png"
readonly PLYMOUTH_SPLASH_BACKUP="/usr/share/plymouth/themes/pix/splash.png.bak"
readonly LABWC_DIR="${HOME_DIR}/.config/labwc"
readonly RC_FILE="${LABWC_DIR}/rc.xml"
readonly AUTOSTART_FILE="${LABWC_DIR}/autostart"
readonly LIGHTDM_CONF="/etc/lightdm/lightdm.conf"

echo
echo "Reverting kiosk setup for tango_motors_control..."

# 0) Remove CAN overlay entries from boot config
echo "Removing CAN overlay entries from ${BOOT_CONFIG}..."
if [[ ! -f "${BOOT_CONFIG}" ]]; then
	echo "ERROR: Missing boot config file: ${BOOT_CONFIG}"
	exit 1
fi

boot_config_changed=0
if sudo grep -Fxq "${CAN_SPI_LINE}" "${BOOT_CONFIG}"; then
	sudo sed -i "\|^${CAN_SPI_LINE}$|d" "${BOOT_CONFIG}"
	boot_config_changed=1
fi
if sudo grep -Fxq "${CAN_OVERLAY_LINE}" "${BOOT_CONFIG}"; then
	sudo sed -i "\|^${CAN_OVERLAY_LINE}$|d" "${BOOT_CONFIG}"
	boot_config_changed=1
fi

if [[ "${boot_config_changed}" -eq 1 ]]; then
	echo "CAN overlay entries removed from ${BOOT_CONFIG}."
else
	echo "CAN overlay entries already absent in ${BOOT_CONFIG}."
fi

echo

# 1) Disable/remove CAN boot service
echo "Stopping and Disabling ${CAN_SERVICE_NAME}..."
sudo systemctl stop "${CAN_SERVICE_NAME}" >/dev/null 2>&1 || true
sudo systemctl disable "${CAN_SERVICE_NAME}" >/dev/null 2>&1 || true

echo "Removing can0.service file..."
if [[ -f "${UNIT_DIR}/${CAN_SERVICE_NAME}" ]]; then
	sudo rm -f "${UNIT_DIR}/${CAN_SERVICE_NAME}"
	echo "Removed: ${UNIT_DIR}/${CAN_SERVICE_NAME}"
else
	echo "Service file not found: ${UNIT_DIR}/${CAN_SERVICE_NAME}"
fi

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo

# 2) Restore Plymouth splash screen from backup
echo "Restoring Plymouth splash screen from backup..."
if [[ -f "${PLYMOUTH_SPLASH_BACKUP}" ]]; then
	sudo cp "${PLYMOUTH_SPLASH_BACKUP}" "${PLYMOUTH_SPLASH_DST}"
	sudo update-initramfs -u
	echo "Restored: ${PLYMOUTH_SPLASH_DST}"
else
	echo "Backup not found, skipping splash restore: ${PLYMOUTH_SPLASH_BACKUP}"
fi

echo

# 3) Remove labwc kiosk rc.xml
echo "Removing kiosk rc.xml..."
if [[ -f "${RC_FILE}" ]]; then
	rm -f "${RC_FILE}"
	echo "Removed: ${RC_FILE}"
else
	echo "rc.xml not found: ${RC_FILE}"
fi

echo

# 4) Remove labwc autostart script
echo "Removing kiosk autostart..."
if [[ -f "${AUTOSTART_FILE}" ]]; then
	rm -f "${AUTOSTART_FILE}"
	echo "Removed: ${AUTOSTART_FILE}"
else
	echo "Autostart not found: ${AUTOSTART_FILE}"
fi

echo

# 5) Switch LightDM session from labwc -> rpd-labwc
echo "Updating LightDM session (labwc -> rpd-labwc)..."
sudo sed -i 's/\<labwc\>/rpd-labwc/g' "${LIGHTDM_CONF}"

# 6) Final summary
echo
echo "CAN overlay removed from:"
echo "  ${BOOT_CONFIG}"
echo
echo "CAN boot service removed (if present):"
echo "  ${UNIT_DIR}/${CAN_SERVICE_NAME}"
echo
echo "Plymouth splash restored (if backup exists):"
echo "  ${PLYMOUTH_SPLASH_DST}"
echo "  (backup: ${PLYMOUTH_SPLASH_BACKUP})"
echo
echo "Kiosk rc.xml removed (if present):"
echo "  ${RC_FILE}"
echo
echo "Kiosk autostart removed (if present):"
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
