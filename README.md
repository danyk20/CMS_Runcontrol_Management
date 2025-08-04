# CMS Runcontrol Service Management Script

This Python script automates the process of restarting specific services within the CMS Runcontrol system. It's designed to manage service states by interacting with a REST API and uses SSH to execute restart commands on remote machines.

### Features

* **Service State Management**: Automatically turns Runcontrol applications ON and OFF via API calls.

* **Central Service Restart**: Uses `ssh` and `pexpect` to restart central services on remote hosts.

* **Proxy Support**: Automatically detects if an SSH SOCKS5 proxy is needed to access the CMS network and uses it for API requests.

* **Flexible Inputs**: Accepts lists of applications and services via command-line arguments, either as JSON strings or file paths.

* **Automated Workflow**: Executes a complete restart cycle: turn off services, wait, restart central services, wait, and turn services back on.

### Prerequisites

Before running this script, ensure you have the following:

* **Python 3.x** installed.

* **Python Libraries**: `requests` and `pexpect`.

* **SSH Tunnel**: An active SSH tunnel to the CMS network is required for the script's proxy logic to work.

* **CERN Credentials**: Your CERN username and password for SSH authentication.

### Installation

Install the required Python libraries using `pip`:

### Configuration

The script's behavior is controlled by a few global variables at the top of the file. You may need to adjust these to fit your environment.

* `URL`: The base URL for the Runcontrol API endpoint.

* `PORT`: The port used for the SSH SOCKS5 proxy. The default is `10880`.

* `LUMI`: The string used to specify the `Lumi` project. The default is `'lumipro'`.

### Usage

The script is executed from the command line and can accept two optional arguments.


**Command-line Arguments**

* `--apps`: This argument is used to specify the Runcontrol applications to manage. It can accept one of two formats:

  * **A path to a JSON file**: The file should contain a JSON object where keys are the full application URIs and values are the desired state (`"ON"` or `"OFF"`).

  * **A JSON string**: The JSON object can be passed directly as a string on the command line. Ensure the string is properly quoted to prevent shell errors.

* `--services`: This argument specifies the central services to be restarted. It must be a path to a plain `.txt` file where each service is listed on a new line or list of strings representing individual services.

**Example 1: Using files**

This is the recommended approach for managing a large number of applications or services.

**Example 2: Using JSON string for apps**

This is useful for quick restarts of a small number of applications.

**Script Workflow**

When you run the script, it performs the following sequence of actions:

1. Parses the provided command-line arguments.

2. Turns **OFF** the specified Runcontrol applications.

3. Waits for **10 seconds**.

4. Restarts the specified central services on their respective hosts using `sudo systemctl restart`.

5. Waits for **10 seconds**.

6. Turns **ON** the Runcontrol applications again.

### Setting up the SSH Tunnel

The script is designed to work with an SSH SOCKS5 proxy to access the CMS network from an external machine. If you are not on the network, you must establish the tunnel before running the script.

Use the following command, replacing `<username>` with your CERN username:

```shell
ssh -D 10880 <username>@cmsusr
```