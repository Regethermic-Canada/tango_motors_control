#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# setup_kiosk.sh -> Configure labwc kiosk autostart for tango_motors_control
#  - ensures required packages are installed
#  - configures CAN overlay in /boot/firmware/config.txt
#  - installs/enable systemd can0.service at boot
#  - writes ~/.config/labwc/rc.xml for kiosk hardening
#  - writes ~/.config/labwc/autostart
#  - backs up and updates Plymouth splash screen from project assets
#  - starts app from ${APP_DIR}
#  - switches LightDM session from rpd-labwc to labwc
###############################################################################

# Configuration
readonly HOME_DIR="${HOME}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
PROJECT_DIR_NAME="$(basename "$(dirname "${SCRIPT_DIR}")")"
readonly PROJECT_DIR_NAME
readonly APP_DIR="${HOME_DIR}/${PROJECT_DIR_NAME}"
readonly BOOT_CONFIG="/boot/firmware/config.txt"
readonly CAN_SPI_LINE="dtparam=spi=on"
readonly CAN_OVERLAY_LINE="dtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25,spimaxfrequency=2000000"
readonly UNIT_DIR="/etc/systemd/system"
readonly CAN_SERVICE_NAME="can0.service"
readonly SPLASH_SRC="${APP_DIR}/src/assets/regethermic_screensaver.png"
readonly PLYMOUTH_SPLASH_DST="/usr/share/plymouth/themes/pix/splash.png"
readonly PLYMOUTH_SPLASH_BACKUP="/usr/share/plymouth/themes/pix/splash.png.bak"
readonly LABWC_DIR="${HOME_DIR}/.config/labwc"
readonly RC_FILE="${LABWC_DIR}/rc.xml"
readonly AUTOSTART_FILE="${LABWC_DIR}/autostart"
readonly APP_CMD="${HOME_DIR}/.local/bin/uv run flet run"
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
# 1) make the boot silent

# 1) Configure CAN overlay in /boot/firmware/config.txt
echo "Configuring CAN overlay in ${BOOT_CONFIG}..."
if [[ ! -f "${BOOT_CONFIG}" ]]; then
	echo "ERROR: Missing boot config file: ${BOOT_CONFIG}"
	exit 1
fi

boot_config_changed=0
if ! sudo grep -Fxq "${CAN_SPI_LINE}" "${BOOT_CONFIG}"; then
	echo "${CAN_SPI_LINE}" | sudo tee -a "${BOOT_CONFIG}" >/dev/null
	boot_config_changed=1
fi
if ! sudo grep -Fxq "${CAN_OVERLAY_LINE}" "${BOOT_CONFIG}"; then
	echo "${CAN_OVERLAY_LINE}" | sudo tee -a "${BOOT_CONFIG}" >/dev/null
	boot_config_changed=1
fi

if [[ "${boot_config_changed}" -eq 1 ]]; then
	echo "CAN overlay entries added to ${BOOT_CONFIG}."
else
	echo "CAN overlay entries already present in ${BOOT_CONFIG}."
fi

# 2) Install systemd can0.service
echo "Writing ${UNIT_DIR}/${CAN_SERVICE_NAME}..."
sudo tee "${UNIT_DIR}/${CAN_SERVICE_NAME}" >/dev/null <<'EOF'
[Unit]
Description=Bring up SocketCAN can0
After=network-pre.target
Before=network.target
Wants=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/sh -c 'ip link set can0 down || true'
ExecStart=/bin/sh -c 'ip link set can0 up type can bitrate 1000000 restart-ms 100'
ExecStart=/bin/sh -c 'ip link set can0 txqueuelen 65536'
ExecStop=/bin/sh -c 'ip link set can0 down'

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd and enabling can0.service..."
sudo systemctl daemon-reload
sudo systemctl enable --now "${CAN_SERVICE_NAME}"

echo "CAN link details (if interface is already available):"
ip -details link show can0 || true

# 3) Backup and update Plymouth splash screen
echo "Updating Plymouth splash screen..."
if [[ ! -f "${SPLASH_SRC}" ]]; then
	echo "ERROR: Splash source not found: ${SPLASH_SRC}"
	exit 1
fi
if [[ ! -f "${PLYMOUTH_SPLASH_DST}" ]]; then
	echo "ERROR: Plymouth splash destination not found: ${PLYMOUTH_SPLASH_DST}"
	exit 1
fi
if [[ ! -f "${PLYMOUTH_SPLASH_BACKUP}" ]]; then
	echo "Creating Plymouth splash backup..."
	sudo cp "${PLYMOUTH_SPLASH_DST}" "${PLYMOUTH_SPLASH_BACKUP}"
else
	echo "Plymouth splash backup already exists: ${PLYMOUTH_SPLASH_BACKUP}"
fi
sudo cp "${SPLASH_SRC}" "${PLYMOUTH_SPLASH_DST}"
sudo update-initramfs -u

# 4) Prepare labwc config directory
echo "Preparing labwc config directory..."
mkdir -p "${LABWC_DIR}"

# 5) Write labwc rc.xml (disable desktop context menu + define hide-cursor bind)
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

# 6) Write labwc autostart script
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

# 7) Switch LightDM session from rpd-labwc -> labwc
echo "Updating LightDM session (rpd-labwc -> labwc)..."
sudo sed -i 's/\<rpd-labwc\>/labwc/g' "${LIGHTDM_CONF}"

# 8) Final summary
echo
echo "Required media packages checked:"
echo "  - libmpv2"
echo "  - wtype"
echo
echo "CAN overlay configured in:"
echo "  ${BOOT_CONFIG}"
echo "  - ${CAN_SPI_LINE}"
echo "  - ${CAN_OVERLAY_LINE}"
echo
echo "CAN boot service written/enabled:"
echo "  ${UNIT_DIR}/${CAN_SERVICE_NAME}"
echo
echo "Plymouth splash updated:"
echo "  ${PLYMOUTH_SPLASH_DST}"
echo "  (source: ${SPLASH_SRC})"
echo "Plymouth splash backup:"
echo "  ${PLYMOUTH_SPLASH_BACKUP}"
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
