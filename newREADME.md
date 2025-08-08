# Runcontrol Reboot Script

This script manages Runcontrol applications and central services for BRIL.  
It supports turning Runcontrol applications ON or OFF via API calls, restarting systemd services on remote hosts, and saving or querying Runcontrol application states.

---

## Features

- Turn Runcontrol applications ON/OFF using API calls with automatic proxy/tunnel detection.
- Restart selected systemd services remotely via SSH (jump through `cmsusr`).
- Save current application states to a JSON file.
- Can operate both inside and outside the CMS network with SOCKS5 proxy.

---

## Prerequisites / Environment

- A Python 3 Conda environment is already set up with all necessary packages installed.
- Before running the script, ensure your Conda environment's `bin` directory is added to your `PATH`. For example:

`
export PATH=/brilpro/brilconda310/bin:$PATH
`

- SSH access with CERN credentials.
- (Optional) If running outside the CMS network, establish a SOCKS5 SSH tunnel for remote API access:

`
ssh -D 10880 <your-CERN-username>@cmsusr.cern.ch
`

*No extra Python package installation is required if your Conda environment includes all dependencies (`requests`, `pexpect`, etc.).*

---

## Usage

`
python runcontrol_reboot.py [--apps APPS] [--services SERVICES] [--show_apps]
`

### Command-Line Arguments

| Argument      | Description                                                                                                               |
| ------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `--apps`      | JSON file path or inline JSON string specifying Runcontrol apps and their states to operate on.                           |
| `--services`  | Path to a `.txt` file listing systemd service names (one per line) to restart.                                           |
| `--show_apps` | Save currently detected state of all Runcontrol applications to `runcontrol_apps.json` and exit.                         |

---

## Typical Workflows

### 1. Saving Application States

Save current state of all Runcontrol applications to a JSON file:

`
python runcontrol_reboot.py --show_apps
`

This creates `runcontrol_apps.json`.

---

### 2. Rebooting Services and Applications

Turn OFF all currently ON apps, restart specified services, then turn ON all previously OFF apps:

`
python runcontrol_reboot.py --services services.txt
`

You will be prompted for your CERN username and password for remote SSH commands.

---

### 3. Using a Custom Application List

Use a JSON file or inline JSON defining apps and states to control:

`
python runcontrol_reboot.py --apps runcontrol_apps.json --services services.txt
`

or inline JSON example:

```python runcontrol_reboot.py --apps '{"http://example.com/app1":"ON", "http://example.com/app2":"OFF"}'```

---

## How Application Entries Are Processed

- The script **only acts on applications listed** in the JSON input (`--apps`).
- The `"ON"` or `"OFF"` values do **not directly force** the process ON or OFF immediately.
- Instead, they indicate the current state and guide the script workflow:
  - At the start, the script turns **OFF** all apps marked `"ON"`.
  - After restarting services, it turns **ON** apps marked `"OFF"` to resume operation.

**To exclude a process from being affected by the script:**  
Simply **remove its entry** from the JSON input. The script ignores any apps not explicitly listed.

---

## File Formats

### `services.txt` example

```
brilservice@srv-s2d16-18-01.cern.ch
another-service@srv-s2d16-27-02.cern.ch
myservice@srv-s2d16-22-01.cern.ch
```

### Example JSON for `--apps`

```
{"http://cmsrc-lumi.cms:26000/urn:rcms-fm:fullpath=/lumipro/dip/global/LumiLevelling": "ON",
    "http://cmsrc-lumi.cms:26000/urn:rcms-fm:fullpath=/lumipro/central/global/LuminosityMonitor": "OFF"
}
```

---

## Frequently Asked Questions (FAQ)

**Q: Can I use `runcontrol_apps.json` (from `--show_apps`) directly as input for `--apps`?**  
**A:** Yes, the file is formatted properly for use as input.

**Q: Does the `"ON"` or `"OFF"` value in JSON force an app to a specific state immediately?**  
**A:** No. These values represent the current state and dictate the order in which the script processes the apps (turn OFF then turn ON).

**Q: How can I prevent a specific application from being restarted or touched?**  
**A:** Remove that app's entry from your input JSON; it will be ignored completely by the script.

---

## Troubleshooting

- **SSH/jump host errors:** Ensure you have valid CERN credentials and SSH access to `cmsusr`.
- **Proxy setup issues:** If API calls fail outside the CMS network, establish an SSH SOCKS5 tunnel on port 10880 before running the script.
- **JSON errors:** Verify that inline JSON strings are properly escaped and valid.



