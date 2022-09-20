#!/usr/bin/env python3
import argparse
from re import match
import subprocess
import time

parser = argparse.ArgumentParser(description="Snapraid status parser")
parser.add_argument(
    "--influx", action="store_true", help="Use Influx line protocol as output format"
)
parser.add_argument(
    "--debug", action="store_true", help="Print output to stdout for debuggin purposes"
)
args = parser.parse_args()


#
# Get output of 'snapraid status'
#
def get_snapraid_status():
    status_output = subprocess.getoutput("sudo snapraid status -v")
    # print status_output
    # count = len(status_output)
    # print count
    return status_output


#
# E.g. "Using 257 MiB of memory for the FileSystem."
#
def parse_memory_for_filesystem(line):
    words = line.split(" ")
    if words[2] == "MiB":
        multiplier = 1024 * 1024
    elif words[2] == "kiB":
        multiplier = 1024
    elif words[2] == "GiB":
        multiplier = 1024 * 1024 * 1024
    else:
        multiplier = 1

    memory_in_bytes = int(words[1]) * multiplier

    if args.influx:
        print(
            "snapraid_status,Type=Array memory_use={0} {1}".format(
                memory_in_bytes, unix_timestamp
            )
        )
    return memory_in_bytes


#
# E.g. "The 31% of the array is not scrubbed."
#
def parse_not_scrubbed(line):
    words = line.split(" ")
    not_scrubbed_percent = int(words[1].strip("%"))

    if args.influx:
        print(
            "snapraid_status,Type=Array not_scrubbed_percent={0} {1}".format(
                not_scrubbed_percent, unix_timestamp
            )
        )
    return not_scrubbed_percent


#
# E.g. "You have 51 files with zero sub-second timestamp."
#
def parse_subsecond_timestamp(line):
    if line.strip() == "No file has a zero sub-second timestamp.":
        subsecond_timestamp_files = 0
    else:
        words = line.split(" ")
        subsecond_timestamp_files = int(words[2])

    if args.influx:
        print(
            "snapraid_status,Type=Array "
            "subsecond_timestamp_files={0} {1}".format(
                subsecond_timestamp_files, unix_timestamp
            )
        )
    return subsecond_timestamp_files


#
# E.g. "0 hardlinks"
#
def parse_hardlinks(line):
    words = line.strip().split(" ")
    hardlinks = int(words[0])
    if args.influx:
        print(
            "snapraid_status,Type=Array hardlinks={0} {1}".format(
                hardlinks, unix_timestamp
            )
        )
    return hardlinks


#
# E.g. "3951 symlinks"
#
def parse_symlinks(line):
    words = line.strip().split(" ")
    symlinks = int(words[0])
    if args.influx:
        print(
            "snapraid_status,Type=Array symlinks={0} {1}".format(
                symlinks, unix_timestamp
            )
        )
    return symlinks


#
# E.g. "6398 empty dirs"
#
def parse_empty_dirs(line):
    words = line.strip().split(" ")
    empty_dirs = int(words[0])
    if args.influx:
        print(
            "snapraid_status,Type=Array empty_dirs={0} {1}".format(
                empty_dirs, unix_timestamp
            )
        )
    return empty_dirs


#
# E.g. "DANGER! In the array there are 15 errors!"
#
def parse_errors(line):
    words = line.strip().split(" ")
    array_errors = int(words[6])
    if args.influx:
        print(
            "snapraid_status,Type=Array array_errors={0} {1}".format(
                array_errors, unix_timestamp
            )
        )
    return array_errors


#
# E.g. "The oldest block was scrubbed 9 days ago, the median 3, the newest 0."
#
def parse_scrubs(line):
    words = line.strip().split(" ")
    scrub_oldest = int(words[5])
    scrub_median = int(words[10].strip(",."))
    scrub_newest = int(words[13].strip(",."))
    if args.influx:
        print(
            "snapraid_status,Type=Array scrub_oldest={0},scrub_median={1},"
            "scrub_newest={2} {3}".format(
                scrub_oldest, scrub_median, scrub_newest, unix_timestamp
            )
        )
    return empty_dirs


#
# When matched line with disk info
# "   46025       4       4     7.0    1457    1487  49% d1"
#
def parse_status_report_disk(line):
    stats_split = line.split()
    disk_stats = dict()
    disk_stats["name"] = stats_split[7]
    disk_stats["files"] = stats_split[0]
    disk_stats["frag_files"] = stats_split[1]
    disk_stats["excess_frag"] = stats_split[2]
    disk_stats["wasted_gb"] = stats_split[3]
    disk_stats["used_gb"] = stats_split[4]
    disk_stats["free_gb"] = stats_split[5]
    disk_stats["use_percent"] = stats_split[6]

    if args.influx:
        print(
            "snapraid_status,Type=Disk,DiskName={0} files={1},"
            "frag_files={2},excess_frag={3},wasted_gb={4},used_gb={5},"
            "free_gb={6},use_percentage={7} {8}".format(
                disk_stats["name"],
                disk_stats["files"],
                disk_stats["frag_files"],
                disk_stats["excess_frag"],
                disk_stats["wasted_gb"],
                disk_stats["used_gb"],
                disk_stats["free_gb"],
                disk_stats["use_percent"].replace("%", ""),
                unix_timestamp,
            )
        )

    return disk_stats


#
# When matched line with total info of disks
# "  612072      40    1134  1122.0    6435    5250  55%       "
#
def parse_status_report_total(line):
    disk_stats = line.split()
    total_disk_stats = dict()
    total_disk_stats["total_files"] = disk_stats[0]
    total_disk_stats["total_frag_files"] = disk_stats[1]
    total_disk_stats["total_excess_frag"] = disk_stats[2]
    total_disk_stats["total_wasted_gb"] = disk_stats[3]
    total_disk_stats["total_used_gb"] = disk_stats[4]
    total_disk_stats["total_free_gb"] = disk_stats[5]
    total_disk_stats["total_use_percent"] = disk_stats[6]

    if args.influx:
        print(
            "snapraid_status,Type=Array files={0},frag_files={1},"
            "excess_frag={2},wasted_gb={3},used_gb={4},free_gb={5},"
            "use_percentage={6} {7}".format(
                total_disk_stats["total_files"],
                total_disk_stats["total_frag_files"],
                total_disk_stats["total_excess_frag"],
                total_disk_stats["total_wasted_gb"],
                total_disk_stats["total_used_gb"],
                total_disk_stats["total_free_gb"],
                total_disk_stats["total_use_percent"].replace("%", ""),
                unix_timestamp,
            )
        )

    return total_disk_stats


#
# Main
#

# Define variables
not_scrubbed = 0
subsecond_timestamps = 0
memory_for_filesystem = ""
status_report = ""
status_report_disks = []
unix_timestamp = int(round(time.time() * 1000000000))


snapraid_status_output = get_snapraid_status().splitlines()

for line in snapraid_status_output:
    # print line
    if "memory for the file-system." in line:
        memory_for_filesystem = parse_memory_for_filesystem(line)
    if "of the array is not scrubbed." in line:
        not_scrubbed = parse_not_scrubbed(line)
    if "zero sub-second timestamp." in line:
        subsecond_timestamps = parse_subsecond_timestamp(line)
    if "hardlinks" in line:
        hardlinks = parse_hardlinks(line)
    if "symlinks" in line:
        symlinks = parse_symlinks(line)
    if "empty dirs" in line:
        empty_dirs = parse_empty_dirs(line)
    if "The oldest block was scrubbed" in line:
        scrubs = parse_scrubs(line)
    if "DANGER! In the array there are" and "errors!" in line:
        array_errors = parse_errors(line)
    if match("^\s+\d+\s+\d+\s+\d+\s+-?\d+.\d+\s+-?\d+\s+-?\d+\s+\d+%+\s+\w+", line):
        status_report_disks.append(parse_status_report_disk(line))
    if match("^\s+\d+\s+\d+\s+\d+\s+\d+.\d+\s+\d+\s+\d+\s+\d+%+\s+$", line):
        status_report_total = parse_status_report_total(line)

if args.debug:
    print("Memory for FileSystem (bytes): {0}".format(memory_for_filesystem))
    print("Not scrubbed of the array (%): {0}".format(not_scrubbed))
    print("Files with zero sub-second timestamp: {0}".format(subsecond_timestamps))
    print("Hardlinks: {0}".format(hardlinks))
    print("Symlinks: {0}".format(symlinks))
    print("Empty dirs: {0}".format(empty_dirs))
    print("Array ERRORS!: {0}".format(array_errors))
    print(status_report_disks)
    print(status_report_total)
