#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# setup_kiosk.sh -> Configure labwc kiosk autostart for tango_motors_control
#  - ensures required packages are installed
#  - configures boot silence, Bluetooth disable, and UARTs in /boot/firmware/config.txt
#  - configures CAN overlay in /boot/firmware/config.txt
#  - backs up and updates /boot/firmware/cmdline.txt for silent boot
#  - installs/enables systemd can0.service at boot
#  - writes ~/.config/labwc/rc.xml for kiosk hardening
#  - writes ~/.config/labwc/autostart
#  - backs up and updates Plymouth splash screen from project assets
#  - masks getty@tty1.service
#  - configures app autostart from ${APP_BIN}
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
readonly BOOT_CMDLINE="/boot/firmware/cmdline.txt"
readonly CONFIG_BACKUP="/boot/firmware/config.txt.back"
readonly CONFIG_APPEND=(
	"disable_splash=1"
	"dtoverlay=disable-bt"
	"dtparam=spi=on"
	"dtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25,spimaxfrequency=2000000"
	"enable_uart=1"
	"dtoverlay=uart2"
	"dtoverlay=uart3"
	"dtoverlay=uart5"
)
readonly CMDLINE_BACKUP="/boot/firmware/cmdline.txt.back"
readonly CMDLINE_REMOVE=(
	"console=tty1"
	"console=serial0,115200"
)
readonly CMDLINE_APPEND=(
	"quiet"
	"loglevel=0"
	"logo.nologo"
	"vt.global_cursor_default=0"
	"systemd.show_status=false"
)
readonly UNIT_DIR="/etc/systemd/system"
readonly CAN_SERVICE_NAME="can0.service"
readonly SPLASH_SRC="${APP_DIR}/src/assets/regethermic_screensaver.png"
readonly PLYMOUTH_SPLASH_DST="/usr/share/plymouth/themes/pix/splash.png"
readonly PLYMOUTH_SPLASH_BACKUP="/usr/share/plymouth/themes/pix/splash.png.bak"
readonly LABWC_DIR="${HOME_DIR}/.config/labwc"
readonly RC_FILE="${LABWC_DIR}/rc.xml"
readonly AUTOSTART_FILE="${LABWC_DIR}/autostart"
readonly APP_BIN="${APP_DIR}/dist/tango_motors_control"
readonly LIGHTDM_CONF="/etc/lightdm/lightdm.conf"

echo
echo "Starting kiosk setup for tango_motors_control..."

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

echo

# 0c) Ensure packaged executable is present
echo "Checking packaged executable..."
if [[ ! -x "${APP_BIN}" ]]; then
	echo "ERROR: Packaged executable not found or not executable: ${APP_BIN}"
	echo "Build it first, then rerun this setup."
	exit 1
fi

echo

# 1) Configure boot options in /boot/firmware/config.txt
echo "Configuring boot options in ${BOOT_CONFIG}..."
if [[ ! -f "${BOOT_CONFIG}" ]]; then
	echo "ERROR: Missing boot config file: ${BOOT_CONFIG}"
	exit 1
fi
if [[ ! -f "${CONFIG_BACKUP}" ]]; then
	echo "Creating config backup..."
	sudo cp "${BOOT_CONFIG}" "${CONFIG_BACKUP}"
else
	echo "Config backup already exists: ${CONFIG_BACKUP}"
fi

boot_config_changed=0
for line in "${CONFIG_APPEND[@]}"; do
	if ! sudo grep -Fxq "${line}" "${BOOT_CONFIG}"; then
		echo "${line}" | sudo tee -a "${BOOT_CONFIG}" >/dev/null
		boot_config_changed=1
		echo "  + Added: ${line}"
	fi
done

if [[ "${boot_config_changed}" -eq 1 ]]; then
	echo "Boot config updated in ${BOOT_CONFIG}."
else
	echo "Boot config already up to date in ${BOOT_CONFIG}."
fi

echo

# 2) Configure silent kernel/systemd boot in /boot/firmware/cmdline.txt
echo "Configuring silent boot kernel arguments in ${BOOT_CMDLINE}..."
if [[ ! -f "${BOOT_CMDLINE}" ]]; then
	echo "ERROR: Missing boot cmdline file: ${BOOT_CMDLINE}"
	exit 1
fi
if [[ ! -f "${CMDLINE_BACKUP}" ]]; then
	echo "Creating cmdline backup..."
	sudo cp "${BOOT_CMDLINE}" "${CMDLINE_BACKUP}"
else
	echo "Cmdline backup already exists: ${CMDLINE_BACKUP}"
fi

current_cmdline="$(sudo cat "${BOOT_CMDLINE}")"
updated_cmdline="${current_cmdline}"
for arg in "${CMDLINE_REMOVE[@]}"; do
	updated_cmdline="${updated_cmdline// ${arg} / }"
	updated_cmdline="${updated_cmdline#"${arg}" }"
	updated_cmdline="${updated_cmdline% "${arg}"}"
	updated_cmdline="${updated_cmdline// ${arg}/}"
done

for arg in "${CMDLINE_APPEND[@]}"; do
	if [[ " ${updated_cmdline} " != *" ${arg} "* ]]; then
		updated_cmdline+=" ${arg}"
	fi
done

updated_cmdline="$(printf '%s\n' "${updated_cmdline}" | awk '{$1=$1; print}')"
if [[ "${updated_cmdline}" != "${current_cmdline}" ]]; then
	printf '%s\n' "${updated_cmdline}" | sudo tee "${BOOT_CMDLINE}" >/dev/null
	echo "Updated ${BOOT_CMDLINE}."
else
	echo "Silent boot arguments already present in ${BOOT_CMDLINE}."
fi

echo

# 3) Install systemd can0.service
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
sudo systemctl enable "${CAN_SERVICE_NAME}"

echo "CAN link details (if interface is already available):"
ip -details link show can0 || true

echo

# 4) Backup and update Plymouth splash screen
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

echo

# 5) Prepare labwc config directory
echo "Preparing labwc config directory..."
mkdir -p "${LABWC_DIR}"

echo

# 6) Write labwc rc.xml (disable desktop context menu + define hide-cursor bind)
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

echo

# 7) Write labwc autostart script
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
exec "${APP_BIN}"
EOF
chmod +x "${AUTOSTART_FILE}"

echo

# 8) Mask tty1 getty to suppress the local text login prompt
echo "Masking getty@tty1.service..."
sudo systemctl mask getty@tty1.service

echo

# 9) Switch LightDM session from rpd-labwc -> labwc
echo "Updating LightDM session (rpd-labwc -> labwc)..."
sudo sed -i 's/\<rpd-labwc\>/labwc/g' "${LIGHTDM_CONF}"

# 10) Final summary
echo
echo "Required media packages checked:"
echo "  - libmpv2"
echo "  - wtype"
echo
echo "Boot options configured in ${BOOT_CONFIG}:"
echo "  (backup: ${CONFIG_BACKUP})"
for line in "${CONFIG_APPEND[@]}"; do
	echo "  - ${line}"
done
echo
echo "Boot cmdline updated:"
echo "  ${BOOT_CMDLINE}"
echo "  (backup: ${CMDLINE_BACKUP})"
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
echo "tty1 getty masked:"
echo "  getty@tty1.service"
echo
echo "App executable:"
echo "  ${APP_BIN}"
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
