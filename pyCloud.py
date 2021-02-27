import sys

from src.cpi import ReadCPI
from src.twoDS import Read2DS

# Check for command line argument (must be a valid file name)
targetFileList = []
if (len(sys.argv) > 1):
    targetFileList.append(sys.argv[1])
# If no command line argument, launch a file dialog
else:
    print "Enter the name of the file to process as a command line argument"
    sys.exit(1)

# Replace this with a loop!
if len(targetFileList) > 0 : targetFile = targetFileList.pop(0)

if ".roi" in targetFile:
    ReadCPI.readCPI(targetFile)
elif ".2DS" in targetFile:
    Read2DS.read2DS(targetFile)
else:
    print "Enter a valid 2DS / CPI data file on the command line"
    print "or select a directory containing 2DS / CPI data..."
    sys.exit(1)
