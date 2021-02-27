# Import Python modules to be used
import os
import fnmatch
from numpy import zeros
from f2DS import getStartTimeFromFileName
from f2DS import read2DSData
from f2DS import set2DSBkg
from f2DS import houseRecord2DS
from f2DS import particleRecord2DS
from f2DS import timeStruct2DS
from f2DS import add2DSImage
from f2DS import outputGeometry
from f2DS import imageTimeStamps

def read2DS(targetFile):
# Define some global variables so we don't run into the problem of redefining them
# for a panel which is already instantiated.
# pWidth, pHeight are sizes for single particle buffers - constrain particles to be
# less than 10 time as long as they are wide - Ximarray.
    pWidth = 128
    pHeight = 1280
# dWidth, dHeight are the sizes of the output arrays for multiple particle images - XdispArray.
# Set dWidth, dHeight to A4 paper at 150dpi
    dWidth = 1754
    dHeight = 1240
    bkgColor = (255,255,255)
    HimArray = zeros((pHeight,pWidth,3),'uint8')
    HimArray[:,:,] = bkgColor
    VimArray = zeros((pHeight,pWidth,3),'uint8')
    VimArray[:,:,] = bkgColor
    HdispArray = zeros((dHeight,dWidth,3),'uint8')
    VdispArray = zeros((dHeight,dWidth,3),'uint8')
# And some more to contain housekeeping, image frames, data types and locations
    findtype = -1
    stampContent = imageTimeStamps()
    hkDat2DS = houseRecord2DS()
    ptDat2DS = particleRecord2DS()
    time2DS = timeStruct2DS()
    imageDims = outputGeometry()
# Setup locations for timestamps at top and bottom of each strip
    stampLoc = zeros((2*imageDims.numStrips,2))
    j = 0
    for i in xrange(0,2*imageDims.numStrips):
        if i%2 == 0:
            stampLoc[i,0] = imageDims.leftPixLoc + (j * (imageDims.stripWidth + 1))
            stampLoc[i,1] = imageDims.topPixLoc-15
        else:
            stampLoc[i,0] = imageDims.leftPixLoc + (j * (imageDims.stripWidth + 1))
            stampLoc[i,1] = imageDims.bottomPixLoc
            j += 1
    Location = 0
# Set up outline structure for XdispArray
    set2DSBkg(HdispArray, imageDims, bkgColor)
    set2DSBkg(VdispArray, imageDims, bkgColor)

# Start by getting start time from file name before we turn it from a string into a file object
    targetFileName = os.path.abspath(targetFile)
    time2DS.currentTime = getStartTimeFromFileName(targetFile)
    time2DS.oldTime = time2DS.currentTime
    time2DS.probeResolution = 1E-5
    time2DS.TAS = 100.0
# Read data one file at a time (only one defined so far, but this could concatenate a series of files in future)
    targetFile = open(targetFile, "rb")
    dataBuff = targetFile.read()
    targetFile.close()
    time2DS.buffSize = len(dataBuff)

# Now need to loop over full number of images and housekeeping - readData returns when
# it finds either a housekeeping block, or an H or V image.
    HactSlice = imageDims.topPixLoc + 1
    HactCol = 0
    VactSlice = imageDims.topPixLoc + 1
    VactCol = 0
    while Location < time2DS.buffSize:
# Call main decode function, which returns a tuple
        findType, time2DS, hPassArray, vPassArray, numSlices, newLoc = read2DSData(dataBuff, Location, time2DS, HimArray, VimArray, ptDat2DS, hkDat2DS)
# Graeme - extract data here: images are in h or v workarray. They're 128 x numSlices pixels. Timestamp is obvious.
        Location = newLoc
        if findType == 0: # Do housekeeping
            pass
        elif findType == 1: # Do H image
            if numSlices > 1200:
                print "H - Can't happen - 1200+ slices"
            else:
                HactSlice, HactCol = add2DSImage(HimArray, HdispArray, numSlices, HactCol, HactSlice, time2DS, "H", imageDims, targetFileName, stampContent, stampLoc)
        elif findType == 2: # Do V image
            if numSlices > 1200:
                print "V - Can't happen - 1200+ slices"
            else:
                VactSlice, VactCol = add2DSImage(VimArray, VdispArray, numSlices, VactCol, VactSlice, time2DS, "V", imageDims, targetFileName, stampContent, stampLoc)
