import sys
import os
from struct import unpack

# Read target file name from command line
targetFileList = []
if (len(sys.argv) > 1):
    targetFileList.append(sys.argv[1])

# If no command line argument, launch a file dialog
else:
    print "Enter the name of the file to process as a command line argument"
    sys.exit(1)

# Replace this with a loop!
if len(targetFileList) > 0 : targetFile = targetFileList.pop(0)
targetFileName = os.path.abspath(targetFile)

# Set some control variables
doAcceleratedScan = 1
writeIndexFile = 1

# Create output file
if writeIndexFile:
    outFile = targetFileName.replace('/','.')
    outFile = outFile.split('.')
    outFile = "intermediate/" + outFile[-2] + outFile[-1] + ".ind"
    if os.path.isfile(outFile):
        print "There is already an index file for", targetFile
        print "in the ./intermediates/ directory. Aborting index operation."
        sys.exit(2)
    outputFile = open(outFile,"w")

# Open data file and read into buffer
targetFile = open(targetFileName, "rb")
dataBuff = targetFile.read()
targetFile.close()

# Inspect the file byte by byte looking for blockmarks
buffSize = len(dataBuff)
Location = 0
stillInBuffer = 1
while stillInBuffer:
    if Location >= buffSize - 1 and doAcceleratedScan: break
# Find CPI IMG blocks
    if dataBuff[Location] == '\xD5':
        if dataBuff[Location+1] == '\xA3':
            nROI = unpack("h",dataBuff[Location+8:Location+10])[0]
            if writeIndexFile: outputFile.write("{0}, Img21, {1}\n".format(Location,nROI))
            if doAcceleratedScan:
                nBYT = unpack("I",dataBuff[Location+2:Location+6])[0]
                if nBYT > 150: nBYT = 1
#                print nBYT
                Location += (nBYT-1)
                if Location >= buffSize-1: break
        if dataBuff[Location+1] == '\xA2':
            nROI = unpack("h",dataBuff[Location+8:Location+10])[0]
            if writeIndexFile: outputFile.write("{0}, Img20, {1}\n".format(Location,nROI))
            if doAcceleratedScan:
                nBYT = unpack("I",dataBuff[Location+2:Location+6])[0]
                if nBYT > 150: nBYT = 1
#                print nBYT
                Location += (nBYT-1)
                if Location >= buffSize-1: break
        if dataBuff[Location+1] == '\xA1':
            nROI = unpack("h",dataBuff[Location+8:Location+10])[0]
            if writeIndexFile: outputFile.write("{0}, ImgXX, {1}\n".format(Location,nROI))
            if doAcceleratedScan:
                nBYT = unpack("I",dataBuff[Location+2:Location+6])[0]
                if nBYT > 150: nBYT = 1
 #               print nBYT
                Location += (nBYT-1)
                if Location >= buffSize-1: break
# Find CPI ROI blocks
    if dataBuff[Location] == '\xE6':
        if dataBuff[Location+1] == '\xB2':
            if writeIndexFile: outputFile.write("{0}, ROI\n".format(Location))
            if doAcceleratedScan:
                rStX = unpack("H",dataBuff[Location+8:Location+10])[0]     #5
                rStY = unpack("H",dataBuff[Location+10:Location+12])[0]    #6
                rEnX = unpack("H",dataBuff[Location+12:Location+14])[0]    #7
                rEnY = unpack("H",dataBuff[Location+14:Location+16])[0]    #8
                pByt = unpack("h",dataBuff[Location+16:Location+18])[0]    #9
                bLen = (rEnX - rStX) * (rEnY - rStY) * pByt
#                print (rEnX - rStX), (rEnY - rStY), pByt, bLen, Location
                Location += (bLen-1)
                if Location >= buffSize-1: break
# Find CPI HK blocks
    if dataBuff[Location] == '\xD6':
        if dataBuff[Location+1] == '\xA1':
            if writeIndexFile: outputFile.write("{0}, HKXX\n".format(Location))
        if dataBuff[Location+1] == '\xA2':
            if writeIndexFile: outputFile.write("{0}, HK20\n".format(Location))
    if dataBuff[Location] == '\xD7':
        if dataBuff[Location+1] == '\xA1':
            if writeIndexFile: outputFile.write("{0}, HK21\n".format(Location))
    if dataBuff[Location] == '\x4b':
        if dataBuff[Location+1] == '\x48':
            if dataBuff[Location+2] == '\x53' and dataBuff[Location+3] == '\x00':
                if writeIndexFile: outputFile.write("{0}, HK3V\n".format(Location))
# Find CPI VALID blocks
    if dataBuff[Location] == '\x1D':
        if dataBuff[Location+1] == '\xAE':
            if writeIndexFile: outputFile.write("{0}, VALID1\n".format(Location))
    if dataBuff[Location] == '\x2D':
        if dataBuff[Location+1] == '\xBE':
            if writeIndexFile: outputFile.write("{0}, VALID2\n".format(Location))
    if dataBuff[Location] == '\x3D':
        if dataBuff[Location+1] == '\xCE':
            if writeIndexFile: outputFile.write("{0}, VALID3\n".format(Location))
# Find CPI PDS blocks
    if dataBuff[Location] == '\x50':
        if dataBuff[Location+1] == '\x44':
            if dataBuff[Location+4] == '\x50' and dataBuff[Location+5] == '\x50':
                if writeIndexFile: outputFile.write("{0}, PDS\n".format(Location))
    Location += 1
    if Location == buffSize-1:
        stillInBuffer = 0
if writeIndexFile: outputFile.close()
