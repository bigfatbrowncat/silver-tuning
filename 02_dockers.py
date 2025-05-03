#!/bin/env python3

# This script is designed to enable plymouth and disable log messages during the boot of Debian Trixie
# It should be run on a clean system right after the installation finished

import sys
import getpass

from common import *
from common.run_app import run_app

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

def check_package_installed(name: str):
    print(f"* Checking if package installed: {name}")

    installed = False

    def dpkg_out(out_line: str):
        nonlocal installed
        if out_line == "Status: install ok installed":
            installed = True

    returncode = run_app(['/usr/bin/dpkg', '-s', name],
            process_out_line=dpkg_out,
            process_err_line=None, print_out=False, print_err=True)

    if returncode == 0:
        return installed
    else:
        if returncode == 1:
            return False
        else:
            raise Exception(f"Can't check if a package is installed: {name}. dpkg returned {returncode}")


def install_docker():
    check_list = ["docker.io", "docker-cli", "docker-compose"]
    inst_list = []

    for pkg in check_list:
        pkg_installed = check_package_installed(f"{pkg}")
        if pkg_installed:
            print(f"  {pkg} is already installed")
        else:
            print(f"  {pkg} is to be installed")
            inst_list += [f"{pkg}"]

    if len(inst_list) == 0:
        return False

    print(f"* Installing docker packages: {', '.join(inst_list)}")
    if not is_root():
        raise EscalationNecessaryError("Root privileges needed to install packages")

    ret = run_app(['/usr/bin/apt', "install", "-y"] + inst_list)

    if ret != 0:
        raise RuntimeError(f"Failed to install packages. apt returned code {ret}")

    return True

def assure_docker_group():
    if "SUDO_USER" in os.environ:
        user = os.environ["SUDO_USER"]
    else:
        user = getpass.getuser()

    print(f"* Checking if the current user {user} is in the \"docker\" group")

    is_in_docker = False
    def groups_out(out_line: str):
        out_line = out_line.split(':')[1].strip()
        nonlocal is_in_docker
        if 'docker' in out_line.split():
            is_in_docker = True


    result = run_app(['/usr/bin/groups', user], process_out_line=groups_out, print_out=False)
    if result != 0:
        raise RuntimeError(f"docker failed with result {result}")

    #SUDO_USER = il

    if not is_in_docker:
        print(f"* Adding the current user {user} to the docker group")
        result = run_app(['/sbin/usermod', '-aG', 'docker', user])
        if result != 0:
            raise RuntimeError(f"usermod failed with result {result}")
        return True
    else:
        print("  The current user is already in the \"docker\" group")
        return False

def main():
    if not is_trixie():
        print("This OS is not Debian Trixie.", file=sys.stderr)
        print("Halting", file=sys.stderr)
        return UNSUPPORTED
    print("The OS is Debian Trixie.")
    print()

    patched = False
    try:
        patched = install_docker()
        patched |= assure_docker_group()
    except Exception as e:
        print(f"Error occurred: {e}", file=sys.stderr)
        print("Halting", file=sys.stderr)
        return UNKNOWN_ERROR

    print()
    if patched:
        print("All done. Reboot the system to apply all the changes.")
    else:
        print("No changes made")

    return SUCCESS


if __name__ == "__main__":
    exit(main())
