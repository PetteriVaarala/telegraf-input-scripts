#!/usr/bin/python
import argparse
from re import match
import numbers
import subprocess
import time

parser = argparse.ArgumentParser(description='Snapraid status parser')
parser.add_argument("--influx",
                    action="store_true",
                    help="Use Influx line protocol as output format")
parser.add_argument("--debug",
                    action="store_true",
                    help="Print output to stdout for debuggin purposes")
args = parser.parse_args()


#
# Get output of 'snapraid smart -v'
#
def get_snapraid_smart():
    status_output = subprocess.Popen(['sudo', 'snapraid', 'smart', '-v'],
                                     stdout=subprocess.PIPE
                                     ).stdout.readlines()
    return status_output


#
# When matched line with disk smart info
# "     35    764       0  36%  3.0  Z500XGRL  /dev/sda  d1"
# "     39    589 logfail  39%  3.0  Z500XH0F  /dev/sde  d2"
# "     35    769       0  30%  3.0  Z500XH2Z  /dev/sdc  d3"
# "     36    747       0  12%  4.0  S3019HAF  /dev/sdf  d4"
# "     35    769       0  31%  3.0  Z500XAQA  /dev/sdd  parity"
# "     35    764       0  12%  3.0  Z500XB02  /dev/sdb  2-parity"
#
def parse_smart_report(line):
    disk_stats = line.split()
    smart_stats = dict()
    smart_stats["temp"] = disk_stats[0]
    smart_stats["power_on_days"] = disk_stats[1]
    smart_stats["error_count"] = disk_stats[2]
    smart_stats["fail_next_year_percent"] = disk_stats[3]
    smart_stats["size_tb"] = disk_stats[4]
    smart_stats["serial"] = disk_stats[5]
    smart_stats["device"] = disk_stats[6]
    smart_stats["disk"] = disk_stats[7]

    # error count can be also string, convert to to digit
    if smart_stats["error_count"].isalpha():
        smart_stats["error_count"] = -1

    if args.influx:
        print 'snapraid_status,Type=Disk,Serial={5},Device={6},Disk={7} '\
              'temp={0},power_on_days={1},error_count={2},'\
              'fail_next_year_percent={3},size_tb={4} {8}'\
              .format(smart_stats["temp"],
                      smart_stats["power_on_days"],
                      smart_stats["error_count"],
                      smart_stats["fail_next_year_percent"].replace("%", ""),
                      smart_stats["size_tb"],
                      smart_stats["serial"],
                      smart_stats["device"],
                      smart_stats["disk"],
                      unix_timestamp)
    if args.debug:
        print smart_stats

    return smart_stats


#
# When matched line with disk smart info
# "     1     5.79%                 22.56%               53.56%       "
# "     2     0.15%                  2.67%               21.62%       "
# "     3     0.0027%                0.21%                5.64%       "
# "     4     0.000034%              0.011%               0.92%       "
# "     5     0.00000021%            0.00030%             0.073%      "
# "     6     0.00000000000000%      0.00000000000000%     0.00000000000000%"
#
def parse_fail_probabilities(line):
    parity_stats = line.split()
    parity_stat = dict()
    parity_stat["fail_for_parity"] = parity_stats[0]
    parity_stat["1_week"] = parity_stats[1]
    parity_stat["1_month"] = parity_stats[2]
    parity_stat["3_months"] = parity_stats[3]

    if args.influx:
        print 'snapraid_status,Type=Array,FailForParity={0} '\
              '1_week={1},1_month={2},3_months={3} {4}'\
              .format(parity_stat["fail_for_parity"],
                      parity_stat["1_week"].replace("%", ""),
                      parity_stat["1_month"].replace("%", ""),
                      parity_stat["3_months"].replace("%", ""),
                      unix_timestamp)
    if args.debug:
        print parity_stat

    return parity_stat


#
# "Probability that at least one disk is going to fail in the next year is 86%"
#
def parse_total_fail_probability(line):
    words = line.strip().split(" ")
    total_fail_probability = int(words[15].strip("%."))
    if args.influx:
        print 'snapraid_status,Type=Array total_fail_probability={0} {1}'\
              .format(total_fail_probability,
                      unix_timestamp)
    if args.debug:
        print 'Probability disk to fail next year: {0}'\
              .format(total_fail_probability)
    return total_fail_probability


#
# Main
#

# Define variables
smart_report_disks = []
fail_probabilities_per_parity = []
unix_timestamp = int(round(time.time() * 1000000000))


snapraid_smart_output = get_snapraid_smart()

for line in snapraid_smart_output:
    if "Probability that at least one disk is going to fail" in line:
        total_fail_probability = parse_total_fail_probability(line)
    if match("^\s+\S+\s+\S+\s+\S+\s+\S+%\s+\S+.\d+\s+\S+\s+\/dev\/\S+\s+\S+",
             line):
        smart_report_disks.append(parse_smart_report(line))

    # Probability of data loss in the next year for different parity and
    # combined scrub and repair time
    if match("^\s+\d+\s+\d+.\d+%\s+\d+.\d+%\s+\d+.\d+%",
             line):
        fail_probabilities_per_parity.append(parse_fail_probabilities(line))
