from __future__ import print_function
from src.cpi.scanFile import scanROIFile
from src.cpi.checkLocList import checkImLocList
import os
import sys

# Read data one file at a time (only one defined so far, but this could concatenate a
# series of files in future)
targetFileList = []
if (len(sys.argv) > 1):
    targetFileList.append(sys.argv[1])
# If no command line argument, launch a file dialog
else:
    print("Enter the name of the file to process as a command line argument")
    sys.exit(1)

# Replace this with a loop!
if len(targetFileList) > 0 : targetFile = targetFileList.pop(0)

# Load data into buffer for processing
targetFileName = os.path.abspath(targetFile)
targetFile = open(targetFile, "rb")
dataBuff = targetFile.read()
targetFile.close()

# Construct data block list for ROI file
imList, hkList, roiList, pdsList = scanROIFile(dataBuff, targetFileName)
# Copy roiList so we can POP items from it in checkLocList
newROIList = list(roiList)
# Consolidate and check data block list
mergedImList = checkImLocList(imList, hkList, newROIList, pdsList)


# Go through block list and run appropriate actions
for item in mergedImList:
    if item[0] == "HK":
        (blockType, blockVersion, Location) = item
        print(blockType, Location)
    if item[0] == "Img":
        (blockType, blockVersion, Location, nROI) = item
        print(blockType, blockVersion, Location, nROI)
    if item[0] == "ROI":
        (blockType, Location, imSize) = item
        print(blockType, Location, imSize)
