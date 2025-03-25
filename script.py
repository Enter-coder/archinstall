#!/usr/bin/env python3
import archinstall

# ===== CONFIGURATION =====
DISK = archinstall.all_disks()[0]  # !!! CHANGE TO YOUR DISK (e.g., 'nvme0n1') !!!
SWAP = True
SWAP_SIZE = "4G"

# Region/Locale
LANGUAGE = "en_US"
ENCODING = "UTF-8"
KEYMAP = "us"
TIMEZONE = "Europe/Prague"
MIRROR_REGION = "Czech"

# User Setup
HOSTNAME = "arch"
ROOT_PASSWORD = "a"  # Change this!
USERNAME = "linux"
USER_PASSWORD = "a"  # Change this!

# System
KERNEL = "linux"
DRIVERS = "best-effort"
AUDIO = "pulseaudio"
NETWORK = "copy-config"
MULTILIB = True

# Desktop
EXTRA_PACKAGES = [
    "git",
    "xorg",
    "xorg-xinit",
    "mesa",
    "lib32-mesa",
    "dmenu",
    "st",
]

# ===== INSTALLATION =====
def install_dwm():
    """Install DWM and auto-start it via .bash_profile"""
    with archinstall.target_env("/mnt") as root:
        # Install DWM/st/dmenu from source
        root.run("pacman -S --noconfirm --needed base-devel")
        root.run("git clone https://git.suckless.org/dwm /tmp/dwm && cd /tmp/dwm && make clean install")
        root.run("git clone https://git.suckless.org/st /tmp/st && cd /tmp/st && make clean install")
        root.run("git clone https://git.suckless.org/dmenu /tmp/dmenu && cd /tmp/dmenu && make clean install")

        # Auto-start DWM when user logs in (via .bash_profile)
        root.run(f"echo 'if [ -z \"$DISPLAY\" ] && [ \"$(tty)\" = \"/dev/tty1\" ]; then' > /home/{USERNAME}/.bash_profile")
        root.run(f"echo '  exec startx' >> /home/{USERNAME}/.bash_profile")
        root.run(f"echo 'fi' >> /home/{USERNAME}/.bash_profile")
        root.run(f"chown {USERNAME}:{USERNAME} /home/{USERNAME}/.bash_profile")

        # Configure .xinitrc to launch DWM
        root.run(f"echo 'exec dwm' > /home/{USERNAME}/.xinitrc")
        root.run(f"chown {USERNAME}:{USERNAME} /home/{USERNAME}/.xinitrc")

# Main Installation
if __name__ == "__main__":
    # !!! WARNING: THIS WILL WIPE THE DISK !!!
    archinstall.log(f"Using disk: /dev/{DISK}", level=archinstall.LogLevel.Info)
    archinstall.sys_command(f"wipefs -a /dev/{DISK}")

    # Partitioning (UEFI + ext4 + swap)
    with archinstall.Filesystem(DISK, archinstall.GPT) as fs:
        fs.use_entire_disk(root_filesystem_type="ext4")  # CHANGED TO ext4
        if SWAP:
            fs.add_partition(SWAP_SIZE, filesystem="swap")

    # Configure system
    installation = archinstall.Installer(
        DISK,
        hostname=HOSTNAME,
        kernel=KERNEL,
        timezone=TIMEZONE,
        audio=AUDIO,
        drivers=DRIVERS,
        network=NETWORK,
        multilib=MULTILIB,
    )
    installation.set_keyboard(KEYMAP)
    installation.set_locale(f"{LANGUAGE}.{ENCODING}")
    installation.set_mirrors({MIRROR_REGION: ["https://mirrors.nic.cz/archlinux/"]})
    installation.add_user(USERNAME, USER_PASSWORD, is_sudo=True)
    installation.set_root_password(ROOT_PASSWORD)
    installation.install_packages(EXTRA_PACKAGES)
    installation.add_bootloader("systemd")

    # Enable NTP
    with archinstall.target_env("/mnt") as root:
        root.run("systemctl enable systemd-timesyncd")

    # Install DWM and configure auto-start
    install_dwm()

    archinstall.log("Installation complete! Reboot and log in to start DWM.", level=archinstall.LogLevel.Info)
