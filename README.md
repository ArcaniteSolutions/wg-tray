# wg-tray

wg-tray enables to quickly bring up/down wireguard interfaces from the system tray, using `wg` and `wg-quick`.

## Installation
wg-tray is a small python package. To install it globally, the recommended version is using [pipx](https://pipx.pypa.io/stable/installation/) (using just pip will result in the error "externally-managed-environment").

`$ pipx install wg-tray`

## Usage
```bash
usage: wg-tray [-h] [-v] [-c CONFIG] [-g CONFIG_GROUPS]

A simple UI tool to handle WireGuard interfaces

options:
  -h, --help            show this help message and exit
  -v, --version         show program version info and exit
  -c CONFIG, --config CONFIG
                        path to the config file listing all WireGuard interfaces (if none is
                        provided, use root privileges to look up in /etc/wireguard/) (default:
                        None)
  -g CONFIG_GROUPS, --config-groups CONFIG_GROUPS
                        Path to the config (.ini file) to have groups of wireguard configs.
                        (default: ~/.wireguard/wg_tray_groups.ini)
```
The config file should simply list all wireguard interfaces, separated either by newlines or spaces (e.g. `wg0 wg1` or
```
wg0 
wg1
```
). The purpose of this config file is to avoid using root access on `ls` to read in `/etc`; however, its correctness is not checked and it is your responsability to keep it up to date.
If no config is provided, the interfaces are dynamically looked up in `/etc/wireguard`.

If you want to avoid being prompted for your root password each time you run `wg-tray`, use a config file and add the following lines to your sudoers file (`sudo visudo` to edit), replacing `<username>` with your user name:
```
<username> ALL=(ALL) NOPASSWD: /usr/bin/wg
<username> ALL=(ALL) NOPASSWD: /usr/bin/wg-quick
```

### Config groups
You can group configs by defining them in the config groups file (located at `./wireguard/wg_tray_groups.ini` by default).

#### Example
Here's an example of a `wg_tray_groups.ini` config file:

```ini
[settings]
pick_one_at_random = false

[Group 01]
pick_one_at_random = true
interfaces = inter01
           = inter02
           = inter03
           = inter04

[Group 02]
interfaces = inter05
           = inter06
```

#### Configs groups settings: `pick_one_at_random`
By default all interfaces in a group will be brought up with a shortcut button. If you wish to only bring up one random interface from the group, you can define the setting `pick_one_at_random` in your group section.
You can also use it on all groups by defining a `settings` section.
