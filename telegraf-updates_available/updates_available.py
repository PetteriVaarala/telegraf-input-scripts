#!/usr/bin/env python3

import string
import platform
import subprocess
import os
import argparse
import time

system = ""
distro = ""
unix_timestamp = int(round(time.time() * 1000000000))


parser = argparse.ArgumentParser(description="Snapraid status parser")
parser.add_argument(
    "--influx",
    action="store_true",
    help="Use Influx line protocol as output format",
)
parser.add_argument(
    "--debug",
    action="store_true",
    help="Print output to stdout for debuggin purposes",
)
args = parser.parse_args()


#
# Get OS
#
def get_os():
    if platform.system() == "Linux":
        if os.path.isfile("/etc/os-release"):
            with open("/etc/os-release") as f:
                d = {}
                for line in f:
                    key, value = line.rstrip().split("=")
                    d[key] = value.strip('"')

            distro = d["NAME"]
            return distro
        # Check if Solus
        elif "solus" in platform.linux_distribution():
            return "Solus"
        # Check if ElementaryOS
        elif '"elementary OS"' in platform.linux_distribution():
            return "elementary OS"
        elif "Ubuntu" in platform.linux_distribution():
            return "Ubuntu"
        else:
            print("unknown distribution")
            exit()
    else:
        print("not linux")
        exit()


#
# Get update count, critical & normal
#
def get_update_count(system):
    if system == "Solus":
        list_upgrades = subprocess.Popen(
            ["eopkg", "list-upgrades"], stdout=subprocess.PIPE
        ).stdout.readlines()
        count = len(list_upgrades)

        # we need to check if only line is update or not
        if count == 1:
            if list_upgrades[0] == "No packages to upgrade.\n":
                return 0, 0

        return int(count), 0

    elif system == "elementary OS" or system == "Ubuntu":
        count = subprocess.getoutput("/usr/lib/update-notifier/apt-check")
        return count.split(";")


system = get_os()
norm, crit = get_update_count(system)

if args.debug:
    print(f"critical:{crit} normal:{norm}")

if args.influx:
    print(
        f"updates_available,OS={system} critical_updates={crit},normal_updates={norm} {unix_timestamp}"
    )
