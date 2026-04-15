#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# kill_kiosk.sh -> Revert labwc kiosk autostart for tango_motors_control
#  - restores /boot/firmware/config.txt from backup
#  - restores /boot/firmware/cmdline.txt from backup
#  - disables/removes systemd can0.service
#  - restores Plymouth splash screen from backup
#  - removes ~/.config/labwc/rc.xml
#  - removes ~/.config/labwc/autostart
#  - unmasks getty@tty1.service
#  - switches LightDM session from labwc to rpd-labwc
###############################################################################

# Configuration
readonly HOME_DIR="${HOME}"
readonly BOOT_CONFIG="/boot/firmware/config.txt"
readonly BOOT_CMDLINE="/boot/firmware/cmdline.txt"
readonly CONFIG_BACKUP="/boot/firmware/config.txt.back"
readonly CMDLINE_BACKUP="/boot/firmware/cmdline.txt.back"
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

# 1) Restore boot config from backup
echo "Restoring ${BOOT_CONFIG} from backup..."
if [[ -f "${CONFIG_BACKUP}" ]]; then
	sudo cp "${CONFIG_BACKUP}" "${BOOT_CONFIG}"
	sudo rm -f "${CONFIG_BACKUP}"
	echo "Restored: ${BOOT_CONFIG}"
else
	echo "Config backup not found, skipping restore: ${CONFIG_BACKUP}"
fi

echo

# 2) Restore boot cmdline from backup
echo "Restoring ${BOOT_CMDLINE} from backup..."
if [[ -f "${CMDLINE_BACKUP}" ]]; then
	sudo cp "${CMDLINE_BACKUP}" "${BOOT_CMDLINE}"
	sudo rm -f "${CMDLINE_BACKUP}"
	echo "Restored: ${BOOT_CMDLINE}"
else
	echo "Cmdline backup not found, skipping restore: ${CMDLINE_BACKUP}"
fi

echo

# 3) Disable/remove CAN boot service
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

# 4) Restore Plymouth splash screen from backup
echo "Restoring Plymouth splash screen from backup..."
if [[ -f "${PLYMOUTH_SPLASH_BACKUP}" ]]; then
	sudo cp "${PLYMOUTH_SPLASH_BACKUP}" "${PLYMOUTH_SPLASH_DST}"
	sudo update-initramfs -u
	echo "Restored: ${PLYMOUTH_SPLASH_DST}"
else
	echo "Backup not found, skipping splash restore: ${PLYMOUTH_SPLASH_BACKUP}"
fi

echo

# 5) Remove labwc kiosk rc.xml
echo "Removing kiosk rc.xml..."
if [[ -f "${RC_FILE}" ]]; then
	rm -f "${RC_FILE}"
	echo "Removed: ${RC_FILE}"
else
	echo "rc.xml not found: ${RC_FILE}"
fi

echo

# 6) Remove labwc autostart script
echo "Removing kiosk autostart..."
if [[ -f "${AUTOSTART_FILE}" ]]; then
	rm -f "${AUTOSTART_FILE}"
	echo "Removed: ${AUTOSTART_FILE}"
else
	echo "Autostart not found: ${AUTOSTART_FILE}"
fi

echo

# 7) Unmask tty1 getty
echo "Unmasking getty@tty1.service..."
sudo systemctl unmask getty@tty1.service >/dev/null 2>&1 || true

echo

# 8) Switch LightDM session from labwc -> rpd-labwc
echo "Updating LightDM session (labwc -> rpd-labwc)..."
sudo sed -i 's/\<labwc\>/rpd-labwc/g' "${LIGHTDM_CONF}"

# 9) Final summary
echo
echo "Boot config restored (if backup exists):"
echo "  ${BOOT_CONFIG}"
echo "  (backup: ${CONFIG_BACKUP})"
echo
echo "Boot cmdline restored (if backup exists):"
echo "  ${BOOT_CMDLINE}"
echo "  (backup: ${CMDLINE_BACKUP})"
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
echo "tty1 getty unmasked:"
echo "  getty@tty1.service"
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
