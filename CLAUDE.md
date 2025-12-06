# CLAUDE.md - AI Assistant Guide for Dark-borne Repository

## Repository Overview

This repository contains a **Hackintosh configuration** for running macOS Catalina 10.15.1 on custom PC hardware using the CLOVER bootloader. It is a configuration-based project rather than a traditional software development project.

### Hardware Specifications

- **Motherboard**: ASUS Gaming Plus S
- **CPU**: Intel Core i5-9400F
- **GPU**: AMD RX 588
- **Wireless/Bluetooth**: BCM94360 (desktop card)
- **USB Configuration**:
  - 2x USB 3.1 Gen2 ports
  - 2x USB 3.1 ports
  - 2x USB 2.0 ports

### Working Features

✅ macOS Catalina 10.15.1 fully operational
✅ All USB ports functioning correctly
✅ Handoff/Continuity features working
✅ AirDrop functionality
⚠️ Sidecar: iPad detected but shows black screen after connection

---

## Repository Structure

```
Dark-borne/
├── CLOVER.zip          # Main CLOVER bootloader configuration archive
├── README.md           # Hardware specs and feature status (Chinese)
└── CLAUDE.md          # This file - AI assistant guide
```

### CLOVER.zip Contents

The CLOVER.zip archive contains the complete EFI/CLOVER configuration:

```
CLOVER/
├── ACPI/
│   ├── origin/         # Original ACPI tables from hardware
│   └── patched/        # Modified ACPI tables (SSDTs)
│       ├── SSDT-EC.aml      # Embedded Controller patch
│       ├── SSDT-UIAC.aml    # USB configuration
│       └── backup/          # Backup of previous configurations
├── drivers/
│   └── UEFI/           # UEFI drivers for booting macOS
│       ├── ApfsDriverLoader.efi
│       ├── AptioInputFix.efi
│       ├── AudioDxe.efi
│       ├── HFSPlus.efi
│       ├── OsxAptioFix2Drv-free2000.efi
│       └── [other drivers]
├── kexts/
│   └── Other/          # Kernel extensions
│       ├── AppleALC.kext       # Audio patching
│       ├── Lilu.kext           # Patching engine (required)
│       ├── WhateverGreen.kext  # GPU patching
│       ├── IntelMausi.kext     # Ethernet driver
│       └── CPUFriend.kext      # CPU power management
├── config.plist        # Main CLOVER configuration file
└── CLOVERX64.efi       # CLOVER bootloader binary
```

---

## Key Files and Their Purpose

### 1. config.plist (26KB)
The **most critical file** in the repository. Contains:
- SMBIOS configuration (system definition)
- Boot arguments and flags
- Device properties and injections
- Kernel and kext patches
- Graphics configuration
- Audio layout ID
- USB port mappings

**⚠️ WARNING**: This file is highly hardware-specific. Changes must be made carefully.

### 2. ACPI Patches

#### SSDT-EC.aml
- Fixes Embedded Controller for Catalina compatibility
- Required for proper power management

#### SSDT-UIAC.aml
- Custom USB port mapping
- Defines which ports are USB 2.0, 3.0, or 3.1
- Critical for proper USB functionality

### 3. Essential Kexts

#### Lilu.kext
- **Foundation kext** - required by most other kexts
- Provides patching engine for macOS

#### WhateverGreen.kext
- GPU patches and fixes
- Enables AMD RX 588 graphics acceleration

#### AppleALC.kext
- Audio patching
- Enables motherboard audio

#### IntelMausi.kext
- Intel Ethernet driver
- Required for wired network connectivity

#### CPUFriend.kext
- CPU power management
- Optimizes performance and battery (if applicable)

---

## Development Workflow

### This is NOT a Traditional Code Repository

This repository contains **configuration files** for a Hackintosh system. There is no compilation, no build process, and no traditional software development.

### Typical Workflow for Changes

1. **Extract CLOVER.zip** to examine current configuration
2. **Make changes** to config.plist or kexts using appropriate tools
3. **Test changes** on actual hardware (cannot be tested in this environment)
4. **Re-archive** modified files into CLOVER.zip
5. **Commit and push** changes to repository
6. **Update README.md** with any feature status changes

### Tools Used (External to Repository)

- **Clover Configurator**: GUI tool for editing config.plist
- **ProperTree**: Cross-platform plist editor
- **IORegistryExplorer**: Analyzing hardware and loaded kexts
- **Hackintool**: USB mapping and hardware information
- **gfxutil**: Getting device paths and IDs

---

## AI Assistant Guidelines

### When Modifying This Repository

#### ✅ DO:

1. **Understand the hardware context** - Changes must match the specific hardware (ASUS Gaming Plus S + i5-9400F + RX 588)
2. **Preserve working configurations** - If USB/Audio/Network is working, don't break it
3. **Keep backups** - ACPI/patched/backup folder exists for a reason
4. **Update README.md** - Document any feature changes in both English and Chinese
5. **Research compatibility** - Kext versions must be compatible with Catalina 10.15.1
6. **Be cautious with SMBIOS** - Changing system definition can break iServices

#### ❌ DON'T:

1. **Don't modify config.plist without understanding** - This can prevent the system from booting
2. **Don't update kexts randomly** - Version mismatches cause kernel panics
3. **Don't remove working ACPI patches** - SSDT files are hardware-specific
4. **Don't change boot arguments carelessly** - Many flags are critical for stability
5. **Don't assume you can test changes** - This requires physical hardware to verify
6. **Don't delete the backup folder** - It contains fallback configurations

### Common Tasks and How to Handle Them

#### Updating Kexts

```
1. Extract CLOVER.zip
2. Navigate to kexts/Other/
3. Replace [KextName].kext with newer version
4. Verify compatibility with macOS 10.15.1
5. Re-archive as CLOVER.zip
6. Update README.md with new kext versions
```

#### Fixing USB Issues

```
1. Check SSDT-UIAC.aml for port definitions
2. Verify config.plist USB injection settings
3. May require USBPorts.kext (see backup folder)
4. Maximum 15 ports per controller due to macOS limit
```

#### Audio Not Working

```
1. Check AppleALC.kext is present and loaded
2. Verify Audio Layout ID in config.plist
3. Common layouts for ALC series: 1, 2, 3, 5, 7, 11
4. Check boot-args for alcid= parameter
```

#### Graphics Issues

```
1. Verify WhateverGreen.kext is loaded
2. Check device properties in config.plist
3. For AMD RX 588, no additional patching usually needed
4. Verify SMBIOS is set to iMac19,1 or compatible
```

### Code/Configuration Conventions

#### File Naming

- ACPI patches: `SSDT-[Purpose].aml` (e.g., SSDT-EC.aml)
- Kexts: CamelCase with .kext extension
- Config: Always `config.plist` (lowercase)

#### Version Control

- Keep CLOVER.zip in root directory
- Update README.md with each significant change
- Commit messages should describe what was changed and why
- Chinese + English documentation preferred

#### Directory Structure Inside CLOVER

```
CLOVER/
├── ACPI/patched/     # Only place custom SSDTs here
├── drivers/UEFI/     # Only UEFI drivers, not BIOS
├── kexts/Other/      # All third-party kexts
└── config.plist      # Main configuration
```

---

## Troubleshooting Guide for AI Assistants

### Cannot Boot After Changes

**Likely causes:**
- Incorrect config.plist syntax
- Incompatible kext versions
- Missing required drivers
- Broken ACPI patches

**What to do:**
- Recommend reverting to backup configuration
- Suggest checking Clover boot log (F2 at boot menu)
- Verify all required files are present

### Features Stopped Working

**Audio:**
- Check AppleALC.kext version
- Verify layout ID in config.plist
- Confirm Lilu.kext is present

**USB:**
- Check SSDT-UIAC.aml is present
- Verify USBInjectAll.kext if needed
- Check port limit patches

**Graphics:**
- Verify WhateverGreen.kext
- Check SMBIOS matches GPU
- Confirm device properties

### macOS Update Issues

**Before updating macOS:**
1. Backup current EFI
2. Check kext compatibility with new macOS version
3. Update Clover bootloader if needed
4. Review community reports for hardware compatibility

---

## Important Technical Details

### SMBIOS Configuration

Current system likely uses: **iMac19,1**
- Matches Coffee Lake CPU (i5-9400F)
- Compatible with RX 580/588 GPU
- Supports Catalina natively

### Boot Arguments

Common boot arguments in this setup may include:
- `alcid=X` - Audio layout ID
- `darkwake=X` - Sleep/wake behavior
- `-v` - Verbose mode (for debugging)
- `debug=0x100` - Kernel panic debugging

### USB Port Mapping

With SSDT-UIAC.aml, ports are mapped to:
- HS01-HS10: USB 2.0 ports
- SS01-SS06: USB 3.0/3.1 ports
- Maximum 15 total ports (macOS limit)

---

## Resource Links for AI Context

### Official Documentation
- [CLOVER Documentation](https://sourceforge.net/projects/cloverefiboot/)
- [OpenCore vs CLOVER](https://dortania.github.io/OpenCore-Install-Guide/)

### Kext Repositories
- [Lilu and plugins](https://github.com/acidanthera/Lilu)
- [AppleALC](https://github.com/acidanthera/AppleALC)
- [WhateverGreen](https://github.com/acidanthera/WhateverGreen)

### Community Resources
- [r/hackintosh](https://www.reddit.com/r/hackintosh/)
- [tonymacx86 Forums](https://www.tonymacx86.com/)
- [InsanelyMac Forums](https://www.insanelymac.com/)

---

## Language Considerations

This repository uses **Chinese** as the primary language in README.md, indicating the target audience is Chinese-speaking users.

### When updating documentation:
1. **Bilingual updates preferred**: Provide both Chinese and English
2. **Technical terms**: Keep in English (e.g., "kext", "ACPI", "SMBIOS")
3. **Feature descriptions**: Translate to Chinese for consistency with existing README

### Example format:
```
✅ Working / 工作正常
⚠️ Partial / 部分工作
❌ Not Working / 不工作
```

---

## Safety and Ethics

### This is a Hackintosh Configuration

**Legal considerations:**
- macOS EULA prohibits installation on non-Apple hardware
- This configuration is for educational/personal use only
- Do not assist with commercial Hackintosh deployments
- Do not help circumvent Apple's security measures beyond standard Hackintosh practices

**What you can help with:**
- Fixing broken configurations
- Updating kexts and drivers
- Improving compatibility
- Documenting working configurations
- Educational explanations

**What you should avoid:**
- Assisting with commercial use
- Bypassing Apple security for malicious purposes
- Distributing macOS installation files
- Violating software licenses

---

## Git Workflow

### Branch Naming Convention

This repository uses automated branch naming:
- Format: `claude/claude-md-[session-id]-[unique-id]`
- Example: `claude/claude-md-miur65anbloe7vhx-014nQc6HqBqv2GYKJVXVi16d`

### Commit Guidelines

**Good commit messages:**
```
Update kexts to support macOS 10.15.7
Fix USB 3.1 ports not working
Add SSDT-PLUG for power management
Update README with Sidecar status
```

**Bad commit messages:**
```
Updated files
Changes
Fix
Test
```

### When to Commit

- After updating kexts
- After modifying config.plist
- After testing new configurations
- After updating documentation
- When feature status changes

---

## Testing Limitations

### ⚠️ CRITICAL: You Cannot Test Changes

As an AI assistant, you **cannot test** changes to this repository because:
1. Requires physical hardware (ASUS Gaming Plus S + specific components)
2. Requires actual macOS installation
3. Boot failures require physical access to hardware
4. USB/Audio/Graphics testing needs real devices

### What you CAN do:
- Analyze configurations for obvious errors
- Verify file structure and syntax
- Research kext compatibility
- Provide recommendations based on community knowledge
- Document changes clearly

### What you CANNOT do:
- Verify a configuration boots successfully
- Test USB ports work correctly
- Confirm audio output functions
- Validate graphics acceleration
- Test sleep/wake behavior

**Always recommend the user test changes on their hardware before considering them complete.**

---

## Quick Reference

### Repository Type
Configuration repository (Hackintosh/CLOVER)

### Primary Files
- `CLOVER.zip` - Main bootloader configuration (5.1 MB)
- `README.md` - Hardware specs and status (Chinese)

### Key Technologies
- CLOVER Bootloader
- ACPI (SSDT patches)
- macOS Catalina 10.15.1
- Kexts (kernel extensions)

### Target Hardware
ASUS Gaming Plus S + i5-9400F + RX 588 + BCM94360

### Documentation Language
Chinese (primary), English (technical terms)

### Last Updated
Based on git history: October-November 2019

---

## Change Log

### 2025-12-06
- Created initial CLAUDE.md documentation
- Analyzed repository structure
- Documented all components and workflows
- Added AI assistant guidelines

---

## Additional Notes

### Why CLOVER Instead of OpenCore?

This configuration uses CLOVER (older bootloader). Modern Hackintosh builds typically use OpenCore. If asked about migration:

**CLOVER Pros:**
- GUI boot menu
- Simpler for beginners
- More forgiving of configuration errors

**OpenCore Pros:**
- Better macOS update compatibility
- More actively developed
- Better security
- Smaller footprint

**Migration warning:** Moving from CLOVER to OpenCore requires complete reconfiguration and is beyond simple file updates.

### Kext Loading Order

Kext loading is handled by CLOVER automatically, but dependencies matter:
1. **Lilu.kext** - Must load first (other kexts depend on it)
2. **VirtualSMC/FakeSMC** - SMC emulation (not visible in current config)
3. **WhateverGreen** - Depends on Lilu
4. **AppleALC** - Depends on Lilu
5. **Other kexts** - Order usually doesn't matter

### File Modifications

When modifying files extracted from CLOVER.zip:
1. Extract entire archive
2. Make modifications
3. Test if possible
4. Re-compress maintaining directory structure
5. Replace CLOVER.zip in repository
6. Commit with descriptive message

### Finding Information

If you need information about:
- **Specific hardware**: Ask user to check System Profiler or IORegistryExplorer
- **Current kext versions**: Ask user to extract CLOVER.zip and check Info.plist files
- **Boot logs**: Ask user to press F2 at CLOVER boot menu to access logs
- **Kernel panics**: Request panic log from user's system

---

**End of CLAUDE.md**

*This guide is maintained for AI assistants (Claude) to better understand and work with this Hackintosh configuration repository. Human users may also find it useful for understanding the repository structure and conventions.*
