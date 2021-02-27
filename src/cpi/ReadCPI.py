# Import Python modules to be used
import sys
import os
import fnmatch
from numpy import zeros
from copy import deepcopy
from fCPI import readCPIImageFrame
from fCPI import setCPIBkg
from fCPI import houseRecordCPI
from fCPI import particleRecord2DS
from fCPI import addCPIImage
from scanFile import scanROIFile
from checkLocList import checkImLocList

def readCPI(targetFile):

# Define some global variables so we don't run into the problem of redefining them
# for a panel which is already instantiated.
# pWidth, pHeight are sizes for single particle buffers - constrain particles to be
# less than 10 time as long as they are wide - Ximarray.
    pWidth = 1024
    pHeight = 1024
# dWidth, dHeight are the sizes of the output arrays for multiple particle images -
# dispArray.
# Set dWidth, dHeight to A4 paper at 150dpi
    dWidth = 1754
    dHeight = 1240
    bkgColor = (255,255,255)
    workArray = zeros((pHeight,pWidth,3),'uint8')
    currentCPIBackGround = zeros((pHeight,pWidth,3),'uint8')
    workArray[:,:,] = bkgColor
    dispArray = zeros((dHeight,dWidth,3),'uint8')
# Set up outline structure for dispArray
    setCPIBkg(dispArray, bkgColor)
# And some more to contain housekeeping, image frames, data types and locations
    findtype = -1
    stampNum = 0
    stampLoc = zeros((4640,2),'uint16')
    stampContent = []      # Could possibly restrict this to 4640 - the maximum likely image density of 80 x 58 on A4 paper
    hkDatCPI = houseRecordCPI()
    ptDatCPI = particleRecord2DS()
    Location = 0

# Read data one file at a time (only one defined so far, but this could concatenate a
# series of files in future)
    targetFileName = os.path.abspath(targetFile)
    targetFile = open(targetFile, "rb")
    dataBuff = targetFile.read()
    targetFile.close()
    buffSize = len(dataBuff)

# Construct data block list for ROI file
#    imList, hkList, roiList, pdsList = scanROIFile(dataBuff, targetFileName)
# Copy roiList so we can POP items from it in checkLocList
#    newROIList = list(roiList)
# Consolidate and check data block list
#    mergedImList = checkImLocList(imList, hkList, newROIList, pdsList)

# Set up image output starting values
    actSlice = 80
    actCol = 40
    nextSlice = 0
    numIm = 0

# Loop over image frame list performing appropriate actions
#    for item in imList:
#        if item[0] == "Img":
#            if 1:
#                (blockType, blockVersion, Location, nROI) = item
# Call image decode function which returns a tuple
# Note that we need to pass this the image frame location and the locations of all ROIs within that frame - currently just does image frame location - JRD
#                findType, isValidParticle, hkDatCPI, passArray, numCols, numSlices, newLoc, timeStamp, actCol, actSlice, nextSlice, stampNum, stampLoc, stampContent, currentCPIBackGround = readCPIImageFrame(dataBuff, Location, workArray, dispArray, ptDatCPI, hkDatCPI, nextSlice, actCol, actSlice, stampNum, stampLoc, stampContent, targetFileName, currentCPIBackGround)
#        if item[0] == "HK":
#            if 1:
# Call housekeeping decode function which returns a tuple
#                pass

    while Location < buffSize:
# Call main decode function, which returns a tuple
        findType, isValidParticle, hkDatCPI, passArray, numCols, numSlices, newLoc, timeStamp, actCol, actSlice, nextSlice, stampNum, stampLoc, stampContent, currentCPIBackGround = readCPIData(dataBuff, Location, workArray, dispArray, ptDatCPI, hkDatCPI, nextSlice, actCol, actSlice, stampNum, stampLoc, stampContent, targetFileName, currentCPIBackGround)
        Location = newLoc
        if findType == 1: # Do housekeeping
            numIm += isValidParticle
