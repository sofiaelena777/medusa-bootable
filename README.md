# 🐍 Medusa Bootable Generator

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-Required-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![Security](https://img.shields.io/badge/Pentesting-Tool-red?style=for-the-badge&logo=kalilinux&logoColor=white)

**Automated bootable USB creator for Windows password bypass and system recovery**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [How It Works](#-how-it-works) • [Disclaimer](#-disclaimer)

</div>

---

## ⚠️ DISCLAIMER

This tool is provided **STRICTLY for educational purposes, penetration testing, and legitimate system recovery scenarios**. 

**Legal Use Only:**
- ✅ Password recovery on YOUR OWN computers
- ✅ Authorized penetration testing with written permission
- ✅ IT emergency access to company systems (with authorization)
- ✅ Educational research and cybersecurity training
- ❌ Unauthorized access to systems you don't own
- ❌ Bypassing security on systems without explicit permission

**The author is NOT responsible for any misuse, illegal activities, or damages resulting from this software.**

---

## 📋 Overview

Medusa is a powerful Python script that creates fully automated bootable USB drives capable of bypassing Windows login screens using the Sticky Keys exploit. It creates a self-contained, bootable Linux environment that automatically detects Windows installations, mounts NTFS partitions, and replaces the Sticky Keys executable with Command Prompt for system-level access.

## ✨ Features

### 🚀 Automated USB Creation

**One-Click USB Generation**
- Automatic USB device detection and filtering
- Safe system disk protection (prevents accidental OS wiping)
- Complete disk partitioning and formatting
- GRUB bootloader installation
- Filesystem labeling (MEDUSA)

**Smart Device Detection**
- USB transport layer detection
- System disk safeguards
- Device size and label identification
- Manual device selection with confirmation

### 🔧 Complete Boot Environment

**GRUB Menu Options:**
1. **Automatic Bypass** - Fully automated sticky keys replacement
2. **Manual Mode** - Interactive shell for custom operations
3. **Boot Local System** - Chainload to installed OS

**Directory Structure:**
```
/boot/         - GRUB bootloader and configuration
/medusa/       - Main payload and batch scripts
/scripts/      - Automation scripts (bash)
/files/        - Free space for personal files
/logs/         - Execution logs and state tracking
/backup/       - Automatic backups of modified files
```

### 🎯 Sticky Keys Bypass

**Automatic Windows Detection:**
- Scans all block devices (/dev/sd*, /dev/nvme*, etc.)
- NTFS partition identification
- Windows System32 directory verification
- SAM database presence check
- BitLocker detection and warning

**Intelligent Mounting:**
- NTFS-3g with hibernation file removal
- Force mount options for stubborn systems
- Write permission verification
- Automatic unmounting and cleanup

**Safe Replacement Process:**
1. Backup original `sethc.exe` (Sticky Keys)
2. Copy backup to `/backup/` with timestamp
3. Replace `sethc.exe` with `cmd.exe`
4. Install Medusa payload to `C:\Medusa\`
5. Create desktop shortcut for easy access
6. Sync and safe unmount

### 📊 Comprehensive Logging

**State Tracking:**
- JSON state file for execution flow
- Timestamped log entries
- Error capture and reporting
- Recovery information

**Logged Events:**
- Dependency checks
- Device detection
- Windows partition discovery
- Mount/unmount operations
- File operations (backup, replace, install)
- Error messages with details

### 🛠️ Medusa Payload

**Interactive Menu System:**
1. **List Users** - Enumerate all Windows accounts
2. **Remove Password** - Blank any user password
3. **Create Admin User** - Add new administrator account
4. **Enable Administrator** - Activate built-in admin account
5. **System Restore** - Clean up changes
6. **Exit** - Close payload

**Test Mode:**
- Dry-run capability for testing
- Simulates operations without changes
- Safe for demonstration purposes

### 🔒 Security Features

**System Protection:**
- Automatic system disk detection and blocking
- Double confirmation required for wiping
- Exact device path verification
- Mount point safeguards

**Backup System:**
- Timestamped backups in `/backup/`
- Original file preservation in System32
- Recovery instructions in logs

**Audit Trail:**
- Complete execution logs
- State machine tracking
- Error documentation
- Timestamp for all operations

## 🚀 Installation

### Prerequisites

**System Requirements:**
- Linux operating system (Kali, Ubuntu, Debian, etc.)
- Python 3.8 or higher
- Root/sudo privileges
- USB drive (8GB+ recommended)

**Required Packages:**
```bash
sudo apt update
sudo apt install -y \
    grub-pc-bin \
    grub-common \
    parted \
    e2fsprogs \
    util-linux \
    ntfs-3g
```

### Quick Start

```bash
# Clone repository
git clone https://github.com/sofiaelena777/medusa-bootable.git
cd medusa-bootable

# Make executable
chmod +x medusa_generator.py

# Run as root
sudo python3 medusa_generator.py
```

## 📖 Usage

### Creating the Bootable USB

1. **Insert USB drive** (all data will be erased!)

2. **Run the generator:**
```bash
sudo python3 medusa_generator.py
```

3. **Select your USB device:**
```
  1. /dev/sdb (14.9G) - usb
  2. /dev/sdc (7.5G) - usb

selecione o dispositivo [0=cancelar]> 1
```

4. **Confirm destruction** by typing the exact device path:
```
[!] para confirmar, digite EXATAMENTE o caminho do dispositivo:
confirmar [/dev/sdb]> /dev/sdb
```

5. **Wait for completion** (typically 1-3 minutes)

### Using Medusa to Bypass Windows

1. **Boot from USB:**
   - Insert Medusa USB into target computer
   - Restart and enter boot menu (F12, F2, DEL, or ESC)
   - Select USB device from boot menu

2. **GRUB Menu:**
   - Select: **"medusa > bypass automatico"**
   - Wait for automatic process (2-5 minutes)

3. **Automatic Process:**
   - Detects Windows partition
   - Mounts NTFS filesystem
   - Backs up original files
   - Replaces Sticky Keys with Command Prompt
   - Installs payload
   - Unmounts safely

4. **Reboot to Windows:**
   - Remove USB drive safely
   - Restart computer normally
   - Boot into Windows

5. **Activate Bypass:**
   - At login screen: **Press SHIFT 5 times**
   - Command Prompt opens as SYSTEM
   - Run: `C:\Medusa\medusa_main.bat`

6. **Use Medusa Menu:**
   - Option 1: List all user accounts
   - Option 2: Remove password from any user
   - Option 3: Create new admin user (medusa/Medusa123!)
   - Option 4: Enable built-in Administrator account
   - Login with modified credentials

### Manual Mode

For advanced users or troubleshooting:

1. Select: **"medusa > modo manual"**
2. Shell opens with tools available
3. Run: `/scripts/auto_sticky.sh` for guided process
4. Or perform custom operations manually

## 🔍 How It Works

### Technical Architecture

**Boot Process:**
```
BIOS/UEFI → GRUB → Linux Kernel → Init Scripts → Medusa Automation
```

**Sticky Keys Exploit:**
```
Windows Login → SHIFT x5 → sethc.exe → Replaced with cmd.exe → SYSTEM Shell
```

### File Operations

**Original Windows File:**
```
C:\Windows\System32\sethc.exe (Sticky Keys executable)
```

**Replacement:**
```
C:\Windows\System32\cmd.exe (Command Prompt) → copied to sethc.exe
```

**Result:**
- Pressing SHIFT 5 times launches Command Prompt
- Runs with SYSTEM privileges (highest level)
- Full administrative access without login

### Automatic Detection Algorithm

1. Scan all block devices
2. Test mount as NTFS with read-only
3. Check for `Windows/System32` directory
4. Verify `config/SAM` database exists
5. Check for BitLocker encryption
6. Remount with write permissions
7. Execute replacement process

## 🗂️ USB Structure

### Directory Layout

```
MEDUSA (USB Drive)
├── boot/
│   └── grub/
│       └── grub.cfg          # Boot menu configuration
├── medusa/
│   ├── medusa_main.bat       # Main payload script
│   └── README.txt            # Payload documentation
├── scripts/
│   ├── boot.sh               # Initial boot script
│   └── auto_sticky.sh        # Automation script
├── files/
│   └── README.txt            # Free space for personal files
├── logs/
│   ├── medusa_execution.log  # Execution log
│   ├── state.json            # State tracking
│   └── build.log             # Creation log
├── backup/
│   └── sethc.exe.backup.*    # Timestamped backups
└── README.txt                # Main documentation
```

## 🛡️ Security Considerations

### Detection Avoidance

**What Medusa Does:**
- ✅ Creates timestamped backups
- ✅ Logs all operations
- ✅ Graceful error handling
- ✅ Safe mount/unmount
- ✅ BitLocker detection

**What Medusa Doesn't Do:**
- ❌ Bypass BitLocker encryption
- ❌ Crack passwords
- ❌ Modify registry (only file replacement)
- ❌ Install persistent backdoors
- ❌ Disable antivirus

### Forensic Traces

**Medusa leaves evidence:**
- Modified timestamp on `sethc.exe`
- Backup files in System32 (`.medusa_backup`)
- C:\Medusa directory and files
- Desktop shortcut
- Event logs (if enabled)

**For legitimate use:**
- Document authorization before use
- Preserve logs for audit trail
- Remove payload after recovery
- Restore original files

### Limitations

**Won't work if:**
- BitLocker or full disk encryption enabled
- Fast Startup enabled (hibernation active)
- NTFS permissions locked by policy
- BIOS boot disabled or SecureBoot active
- Disk corruption or filesystem errors

## 🔧 Troubleshooting

### USB Not Detected

```bash
# Manually list devices
lsblk -o NAME,SIZE,TYPE,TRAN

# Check if mounted
mount | grep /dev/sd

# Force unmount
sudo umount /dev/sdb* 2>/dev/null
```

### GRUB Installation Failed

```bash
# Reinstall GRUB manually
sudo grub-install --target=i386-pc --boot-directory=/mnt/boot --force /dev/sdb
```

### Windows Partition Not Found

**In manual mode shell:**
```bash
# List all partitions
lsblk -f

# Test mount manually
mkdir /tmp/test
mount -t ntfs-3g /dev/sda2 /tmp/test
ls /tmp/test/Windows
```

### Permission Denied on System32

**Possible causes:**
- Windows is hibernated (Fast Startup enabled)
- NTFS permissions locked
- Antivirus protection

**Solutions:**
```bash
# Force mount with remove_hiberfile
mount -t ntfs-3g -o remove_hiberfile,rw,force /dev/sda2 /mnt
```

### BitLocker Encrypted Drive

Medusa **cannot** bypass BitLocker. You need:
- Recovery key
- Password
- TPM unlock

**Alternative:** Boot into Windows Recovery and disable BitLocker first.

## 📊 Comparison

| Feature | Medusa | Kon-Boot | Hiren's BootCD | Offline NT |
|---------|--------|----------|----------------|------------|
| Price | Free | $27-$70 | Free | Free |
| Bootable USB | ✅ | ✅ | ✅ | ❌ |
| Automated | ✅ | ✅ | ❌ | ❌ |
| NTFS Support | ✅ | ✅ | ✅ | ✅ |
| Logging | ✅ | ❌ | ❌ | ❌ |
| Backups | ✅ | ❌ | ❌ | ❌ |
| Open Source | ✅ | ❌ | Mixed | ✅ |

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- UEFI boot support
- Windows 11 compatibility testing
- GUI for payload menu
- Additional bypass methods
- Automated restore function

## 📜 License

MIT License

```
Copyright (c) 2024 sofiaelena777

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

## 👤 Author

**sofiaelena777**

- GitHub: [@sofiaelena777](https://github.com/sofiaelena777)

## 🙏 Acknowledgments

- NTFS-3g developers
- GRUB bootloader team
- Sticky Keys exploit researchers
- Penetration testing community

---

<div align="center">

**⚠️ Educational Use Only | 🔒 Authorized Access Only | 📖 Know Your Laws**

Made with ❤️ by sofiaelena777

</div>
