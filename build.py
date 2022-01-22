import subprocess
import os
import sys
import re
import argparse

# Parse arguments, determine if whitelist and blaclist should be used
parser = argparse.ArgumentParser(description="Build QMK for Sonix keyboards")
parser.add_argument("--whitelist", help="enables the whitelist (specify a filename)")
parser.add_argument("--blacklist", help="enables the blacklist (specify a filename)")
parser.add_argument("--debug", help="displays which keyboards are being excluded based on whitelist/blacklist", action="store_true")
args = parser.parse_args()

KEYBOARDS = []
# Search the repository for Sonix SN32F2 keyboard directories
command = "grep -rl 'MCU = SN32F2' | sed -e 's/keyboards\///g' -e 's/\/rules.mk//g'| sort"

if args.whitelist:
  # Grab the list of whitelisted keyboards
  whitelisted_kb_command = "cat " + args.whitelist + " | tr -d '\r'"
  whitelisted_kb_ret = subprocess.run(whitelisted_kb_command, capture_output=True, shell=True)
  WHITELISTED_BOARDS = whitelisted_kb_ret.stdout.decode().split('\n')

if args.blacklist:
  # Grab the list of blacklisted keyboards
  blacklisted_kb_command = "cat " + args.blacklist + " | tr -d '\r'"
  blacklisted_kb_ret = subprocess.run(blacklisted_kb_command, capture_output=True, shell=True)
  BLACKLISTED_BOARDS = blacklisted_kb_ret.stdout.decode().split('\n')

ret = subprocess.run(command, capture_output=True, shell=True)
BOARDS = ret.stdout.decode().split('\n')
def main():
    for line in BOARDS:
        # We need to manipulate some non-standard directories
        if should_include(line):
            if re.match("^(gmmk)",line.strip()):
                KEYBOARDS.append(line.strip()+"/rev2")
                KEYBOARDS.append(line.strip()+"/rev3")
            if re.match("^(keychron/k)",line.strip()):
                KEYBOARDS.append(line.strip())
                # keychron K series white don't have yet via/optical support
                if re.match("(?!.*white)",line.strip()):
                    KEYBOARDS.append(line.strip()+"/via")
                    KEYBOARDS.append(line.strip()+"/optical")
                    KEYBOARDS.append(line.strip()+"/optical_via")
            else: KEYBOARDS.append(line.strip())
    print ('Filtered and processed boards: ', KEYBOARDS)

def should_include(keyboard):
  if keyboard.strip() == "":
    return false
  if keyboard.strip() == "lib/python/build_all.py":
    return false
  if args.blacklist:
    if (keyboard.strip() in BLACKLISTED_BOARDS):
      if args.debug:
        print ("Excluding blacklisted keyboard: ", keyboard.strip())
      return false
  if args.whitelist:
    if keyboard.strip() not in WHITELISTED_BOARDS:
      if args.debug:
        print ("Excluding non-whitelisted keyboard: ", keyboard.strip())
      return false
  return true

if __name__ == '__main__':
    main()

error = False
for kb in KEYBOARDS:
    # We are building for different chips, and some things need a clean pass, so make sure it's clean
    build_command = f"qmk clean && qmk compile -kb {kb} -km all -j{os.cpu_count()}"
    if subprocess.run(build_command, shell=True).returncode != 0:
        error = True
if error:
    sys.exit(1)
