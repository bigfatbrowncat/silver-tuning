#!/bin/env python3

# This script is designed to enable plymouth and disable log messages during the boot of Debian Trixie
# It should be run on a clean system right after the installation finished

import os.path
import shutil
import re
import subprocess
import sys
from common import *

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

GRUB_CMDLINE_LINUX_DEFAULT = "GRUB_CMDLINE_LINUX_DEFAULT"

def get_printk_vars():
    sp = subprocess.run(["/sbin/sysctl", "-a"], capture_output=True, shell=False)
    output = sp.stdout.decode("utf-8")
    #kernel.printk = 2       2       1       2

    for o in output.splitlines():
        k, vals = o.split('=')
        k = k.strip()
        vals = vals.strip()
        if k == "kernel.printk":
            vals = vals.split('\t')
            for i, v in enumerate(vals):
                vals[i] = int(v.strip())
            return vals

    return None


def patch_sysctl_printk():
    print("* Checking printk (kernel logging) configuration...")
    printk_vars = get_printk_vars()
    if printk_vars != [2, 2, 1, 2]:
        if not is_root():
            raise EscalationNecessaryError(f"Need root permissions to disable logging. Use sudo.")
        with open("/etc/sysctl.d/00_silver-tuning_printk.conf", "w") as f:
            f.write("kernel.printk = 2 2 1 2\n")
    else:
        print("  No patching needed")


# GRUB_CMDLINE_LINUX_DEFAULT="quiet loglevel=3 splash vt.global_cursor_default=0"
def patch_grub():
    lines = None
    with open("/etc/default/grub", "r") as f:
        lines = f.readlines()

    has_quiet = False
    has_splash = False
    has_loglevel_not_more_than_3 = False
    has_vt_global_cursor_default_0 = False

    cmdline_linux_default_options = None
    cmdline_linux_default_options_line_index = -1

    kv_pattern = re.compile(r"(\w+)=(.*)")
    for i, line in enumerate(lines):
        kv = kv_pattern.match(line)
        if kv is not None and len(kv.groups()) == 2:
            k, v = kv.groups()
            k = k.strip()
            v = v.strip()
            if v[0] == v[-1] == '"': v = v[1:-1]

            if k == GRUB_CMDLINE_LINUX_DEFAULT:
                cmdline_linux_default_options = v
                cmdline_linux_default_options_line_index = i

                has_quiet = False
                has_splash = False
                has_loglevel_not_more_than_3 = False
                has_vt_global_cursor_default_0 = False

                opts = v.split(' ')
                for o in opts:
                    o = o.strip()
                    if o == "quiet":
                        has_quiet = True
                    elif o == "splash":
                        has_splash = True
                    elif o.startswith("loglevel"):
                        k, v = o.split('=')
                        k = k.strip()
                        v = v.strip()
                        if k == "loglevel" and int(v) <= 3:
                            has_loglevel_not_more_than_3 = True
                    elif o.startswith("vt.global_cursor_default"):
                        k, v = o.split('=')
                        k = k.strip()
                        v = v.strip()
                        if k == "vt.global_cursor_default" and int(v) == 0:
                            has_vt_global_cursor_default_0 = True

        # Continue parsing the file! If there are multiple GRUB_CMDLINE_LINUX_DEFAULT=... lines, it should catch the last one

    needs_patching = False
    print("* Checking boot options...")

    if not has_quiet:
        print("  Not quiet. Fixing.")
        cmdline_linux_default_options += " quiet"
        needs_patching = True
    else:
        print("  Quiet. Skipping.")

    if not has_splash:
        print("  Splash isn't enabled. Fixing.")
        cmdline_linux_default_options += " splash"
        needs_patching = True
    else:
        print("  Splash enabled. Skipping.")

    if not has_loglevel_not_more_than_3:
        print("  Fixing the loglevel.")
        cmdline_linux_default_options += " loglevel=3"
        needs_patching = True
    else:
        print("  Log level is low. Skipping.")

    if not has_vt_global_cursor_default_0:
        print("  Hiding the global VT cursor (to avoid cursor blinking during boot time).")
        cmdline_linux_default_options += " vt.global_cursor_default=0"
        needs_patching = True
    else:
        print("  Global VT cursor is hidden. Skipping.")

    if needs_patching:
        if not is_root():
            raise EscalationNecessaryError(f"Need root permissions to disable logging. Use sudo.")
        cmdline_linux_default_options = cmdline_linux_default_options.strip()
        with open("/etc/default/grub", "w") as f:
            for i, line in enumerate(lines):
                if i != cmdline_linux_default_options_line_index:
                    f.write(line)
                else:
                    f.write(f'{GRUB_CMDLINE_LINUX_DEFAULT}="{cmdline_linux_default_options}"\n')


def main():
    if not is_trixie():
        print("This OS is not Debian Trixie.", file=sys.stderr)
        print("Halting", file=sys.stderr)
        return UNSUPPORTED
    print("The OS is Debian Trixie.")
    print()

    try:
        patch_sysctl_printk()
        patch_grub()
    except Exception as e:
        print(f"Error occurred: {e}", file=sys.stderr)
        print("Halting", file=sys.stderr)
        return UNKNOWN_ERROR

    return SUCCESS


if __name__ == "__main__":
    exit(main())
