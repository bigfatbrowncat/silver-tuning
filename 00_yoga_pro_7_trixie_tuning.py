#!/bin/env python3

# This script is designed to fix the issues of Lenovo Yoga Pro 7 14IMH9 (model 83E2003LIV) running Debian Trixie
# It should be run on a clean system right after the installation finished
# It could be extended to support any other type of machine (you are welcome to create MRs to this repo)

import os.path
import shutil
import sys
from common import *


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

YOGA_PRO_7_14IMH9 = "Yoga Pro 7 14IMH9"

SND_SOF_INTEL_HDA_GENERIC = "snd_sof_intel_hda_generic"
ALC287_YOGA9_BASS_SPK_PIN = "alc287-yoga9-bass-spk-pin"

INTEL_SOUND_VOLUME_FIX_PATCH_FILE_NAME = "/etc/modprobe.d/silver-tuning_intel-sound-volume-fix.conf"


def get_hda_model():
    with open(f"/sys/module/{SND_SOF_INTEL_HDA_GENERIC}/parameters/hda_model") as hda_model:
        return hda_model.readline().strip()

def patch_yoga_pro_7_14imh9_firmware():
    print("* Installing the firmware...")

    needs_reboot = False
    files_list = [ "lib/firmware/intel/vpu/vpu_37xx_v0.0.bin" ]
    for f in files_list:
        target = os.path.join("/", f)
        if not os.path.exists(target):
            if not is_root():
                raise EscalationNecessaryError(f"Can't install the file {f}. Need root permissions. Use sudo.")
            print(f"  Copying {f}")
            target_dir = os.path.dirname(target)
            os.makedirs(target_dir, exist_ok=True)
            shutil.copyfile(
                os.path.join(SCRIPT_DIR, "yoga_pro_7_files", "root", f),
                target
            )
            needs_reboot = True
        else:
            print(f"  {target} already exists, skipping.")
    return needs_reboot

def patch_yoga_pro_7_14imh9_sound_write():
    if not is_root():
        raise EscalationNecessaryError(f"Can't patch {INTEL_SOUND_VOLUME_FIX_PATCH_FILE_NAME} without root permissions. Use sudo.")
    with open(INTEL_SOUND_VOLUME_FIX_PATCH_FILE_NAME, "w") as patch_file:
        patch_file.write(f"options {SND_SOF_INTEL_HDA_GENERIC} hda_model={ALC287_YOGA9_BASS_SPK_PIN}")
    return True

def patch_yoga_pro_7_14imh9_sound():
    print("* Checking sound configuration...")
    hda_model = get_hda_model()
    if hda_model != ALC287_YOGA9_BASS_SPK_PIN:
        print(f"  Adding modprobe option fix: {INTEL_SOUND_VOLUME_FIX_PATCH_FILE_NAME}")
        return patch_yoga_pro_7_14imh9_sound_write()
    else:
        print("  No need to patch")
        return False


def main():
    machine_model = None
    try:
        with open("/sys/devices/virtual/dmi/id/product_family", "r") as product_family:
            machine_model = product_family.readline().strip()

    except Exception as e:
        print("Failed to read the machine's model.", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        print("Halting", file=sys.stderr)
        return ERROR_NO_PRODUCT_FAMILY

    print(f"This machine's model is: {machine_model}")
    if not is_trixie():
        print("This OS is not Debian Trixie.", file=sys.stderr)
        print("Halting", file=sys.stderr)
        return UNSUPPORTED
    print("The OS is Debian Trixie.")
    print()

    if machine_model == YOGA_PRO_7_14IMH9:
        p1 = False
        p2 = False
        try:
            p1 = patch_yoga_pro_7_14imh9_firmware()
            p2 = patch_yoga_pro_7_14imh9_sound()
        except Exception as e:
            print(f"Error occurred: {e}", file=sys.stderr)
            print("Halting", file=sys.stderr)
            return UNKNOWN_ERROR

        print()
        if p1 or p2:
            print("All done. Reboot the system to apply all the changes.")
        else:
            print("No changes made")
        return SUCCESS
    else:
        print("This model is not supported by the script.")
        print("You are welcome to contribute.")
        return UNSUPPORTED


if __name__ == "__main__":
    exit(main())
