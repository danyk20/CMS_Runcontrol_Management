import argparse
import getpass
import platform
import socket
import sys
import time

import pexpect
import requests
import json
import os

URL = 'http://srv-s2d16-22-01.cms/runcontrol/api/'
OUTPUT = '_apps.json'  # output file name for Runcontrol applications
INPUT = ''  # string input file for Runcontrol applications
FILE = ''  # input file name for Runcontrol applications
RUNCONTROL_INFO = False
LUMI = 'lumipro'
SERVICES = ['bril.central@srv-s2d16-18-01.service', 'bril.central@srv-s2d16-27-01.service']
PORT = 10880


def is_host_reachable_ping(hostname='srv-s2d16-18-01') -> bool:
    """
    Checks if a host is reachable using the system's ping command.
    :return: True if reachable, False otherwise.
    """
    if platform.system() == "Windows":
        command = f"ping -n 1 {hostname}"
    else:
        command = f"ping -c 1 {hostname}"

    null_output = "NUL" if platform.system() == "Windows" else "/dev/null"
    return os.system(f"{command} > {null_output} 2>&1") == 0


PROXIES = {} if is_host_reachable_ping() else {
    'http': 'socks5h://localhost:' + str(PORT),
    'https': 'socks5h://localhost:' + str(PORT)
}


def check_port_listening(host, port, timeout=1) -> bool:
    """
    Checks if a given port on a host is listening.
    :return: True if listening, False otherwise.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False
    except Exception as e:
        print(f"An error occurred while checking port {port} on {host}: {e}")
        return False


def extract_uris(data) -> list[str]:
    """
    Extracts URIs from a JSON string.

    :param data: JSON string.
    :return: List of URIs.
    """
    uris = []
    for key, value in data.items():
        uris.append(data[key]["URI"])
    return uris


def turn_off() -> None:
    """
    Turn off all services that are currently ON.
    :return: None
    """
    full_paths = json.loads(INPUT) if INPUT else get_apps(state='ON')
    if FILE:
        with open(FILE, 'r') as file:
            full_paths = json.load(file)
    return execute(full_paths, True)


def turn_on() -> None:
    """
    Turn on all services that are currently OFF.
    :return: None
    """
    full_paths = json.loads(INPUT) if INPUT else get_apps(state='OFF')
    if FILE:
        with open(FILE, 'r') as file:
            full_paths = json.load(file)
    return execute(full_paths, False)


def execute(full_paths: dict, off: bool) -> None:
    """
    Sends a GET request to a specified URL to turn off all components one by one,
    using a SOCKS5 proxy with remote DNS resolution.
    :return: None
    """
    print("--- Python JSON GET Request Script with Proxy ---")

    baseurl = URL + 'send/Turn' + ('OFF' if off else 'ON')

    for path in full_paths:
        clean_path = path.split('=')[1][:-6]
        url = baseurl + clean_path
        print(f"\nSending POST request to: {url} via proxy: {PROXIES}")
        call_url(url)
        print(f"\nTurned {'OFF' if off else 'ON'} successfully!")


def call_url(url: str, call_type='GET', data=None) -> requests.Response:
    """
    Call API endpoint of specific URL.
    :param data: Data in JSON format
    :param url: URL to use;
    :param call_type: GET or POST
    :return: response
    """
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.get(url, headers=headers, proxies=PROXIES) if call_type == 'GET' else (
            requests.post(url, json=extract_uris(data), headers=headers, proxies=PROXIES))
        response.raise_for_status()

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        if not check_port_listening("localhost", PORT):
            print(f"Missing tunnel to CMS network! Run: `ssh -D 10880 <username>@cmsusr` ")
            raise RuntimeError("Outside of CMS network!")
        else:
            print(f"Connection error occurred: {conn_err}.")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}. The request took too long to respond.")
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred during the request: {req_err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return response


def get_runcontrol_apps() -> dict[str, dict[str, str]]:
    """
    Sends a GET request to a specified URL to store JSON data in a file,
    using a SOCKS5 proxy with remote DNS resolution.
    :return: Dictionary with app names as keys and JSON data ['URI', 'resGID', 'version'] as values.
    """
    url = URL + 'running/' + LUMI
    print(f"\nSending GET request to: {url} via proxy: {PROXIES}")
    response = call_url(url)
    print(f"Response Body:\n{response.text}")
    return response.json()


def get_apps(state: str = 'ON') -> dict[str: dict[str: str]]:
    """
    Sends a POST request to a specified URL with JSON data loaded from a file,
    using a SOCKS5 proxy with remote DNS resolution.
    """
    json_data: dict[str: dict[str: str]] = get_runcontrol_apps()
    json.dumps(json_data, indent=2)

    print("--- Python JSON POST Request Script ---")
    url = URL + 'states'
    print(f"\nSending POST request to: {url} via proxy: {PROXIES}")
    response = call_url(url, 'POST', data=json_data)
    print(f"Response Body:\n{response.text}")

    if RUNCONTROL_INFO:
        state_apps = {key: value for key, value in response.json().items()}
        with open('runcontrol' + OUTPUT, "w") as file:
            json.dump(state_apps, file, indent=4)
        sys.exit(0)
    state_apps = {key: value for key, value in response.json().items() if value == state}
    with open(state + OUTPUT, "w") as file:
        json.dump(state_apps, file, indent=4)
    return state_apps


def get_host(service) -> str:
    """
    Extracts the host name from a full service name.
    :param service: Full service name
    :return: host name
    """
    prefix_removed = service.split('@')[1]
    host = prefix_removed.split('.')[0]
    return host


def sort_services(services: list) -> list[str]:
    """
    Order services based on their priority: 1# NON 18 or 27 services, 2# 18 services, 3# 27 services
    :param services: list of services
    :return: sorted list of services
    """
    first = []
    second = []
    third = []
    for service in services:
        match get_host(service):
            case 'srv-s2d16-18-01':
                second.append(service)
                continue
            case 'srv-s2d16-27-02':
                third.append(service)
                continue
            case default:
                first.append(service)
    return first + second + third


def restart_central_service(services: list[str]) -> None:
    """
    Sends a 'restart' command to a specified systemd service with sudo permissions.
    :return: None
    """
    username = input("Please enter your CERN username: ")
    password = getpass.getpass("Enter your @cmsusr password: ")
    for service in sort_services(services):
        host = get_host(service)

        command = 'ssh -J ' + username + '@cmsusr ' + username + '@' + host + ' "sudo systemctl restart ' + service + '"'
        print(command + "\n")
        try:
            child = pexpect.spawn(command)

            child.expect('.*Password:.*')
            child.sendline(password)
            child.expect('.*password:.*')
            child.sendline(password)

            child.expect(pexpect.EOF)
            print(child.before.decode())

        except pexpect.exceptions.ExceptionPexpect as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")


def parse_arguments() -> None:
    """
    Parses command line arguments
    :return: None
    """
    parser = argparse.ArgumentParser(
        description="Runcontrol reboot script"
    )

    parser.add_argument(
        '--apps',
        type=str,
        required=False,
        help='A JSON (string or path) runcontrol apps and their state, e.g. --apps {\"http://cmsrc-lumi.cms:26000/urn:rcms-fm:fullpath=/lumipro/dip/global/LumiLevelling,group=BrilDAQFunctionManager,owner=lumipro\":\"ON\",\"http://cmsrc-lumi.cms:26000/urn:rcms-fm:fullpath=/lumipro/central/global/LuminosityMonitor,group=BrilDAQFunctionManager,owner=lumipro\":\"ON\"}'
    )

    parser.add_argument(
        '--services',
        type=str,
        required=False,
        help='A path to the .txt file or string with services to restart'
    )

    parser.add_argument(
        '--show_apps',
        action="store_true",
        help='Saves state of all Runcontrol application into runcontrol_apps.json'
    )

    args = parser.parse_args()
    global INPUT, FILE, SERVICES, RUNCONTROL_INFO
    if args.apps:
        if os.path.exists(args.apps):
            FILE = args.apps
        else:
            INPUT = args.apps
    if args.services:
        with open(args.services, 'r') as file:
            SERVICES = []
            for line in file:
                SERVICES.append(line)
    RUNCONTROL_INFO = args.show_apps


if __name__ == "__main__":
    parse_arguments()

    turn_off()
    time.sleep(10)
    restart_central_service(SERVICES)
    time.sleep(10)
    turn_on()
