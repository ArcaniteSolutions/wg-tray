# wg-tray

wg-tray enables to quickly bring up/down wireguard interfaces from the system tray, using `wg` and `wg-quick`.

## Installation

`$ pip install wg-tray`

## Usage
```bash
wg-tray [-h] [-v] [-c CONFIG]

optional arguments:
  -h, --help                   show this help message and exit
  -v, --version                show program version info and exit
  -c CONFIG, --config CONFIG   path to the config file listing all wireguard interfaces 
                               (default: none; use root privileges to look up in /etc/wireguard/)
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
