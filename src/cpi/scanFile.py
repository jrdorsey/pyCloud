from __future__ import print_function
import sys
import os
from struct import unpack

def scanROIFile(dataBuff, targetFileName):

# Check Python version - 3 is unspported
    if sys.version_info[0] >= 3:
        sys.stderr.write("You need python 2 to run this script - the binary data type in Python 3 is broken\n")
        exit(1)

# Set some control variables
    doAcceleratedScan = True
    writeIndexFile = True

# Create output file
    if writeIndexFile:
        outFile = targetFileName.replace('/','.')
        outFile = outFile.split('.')
        outFile = "intermediate/" + outFile[-2] + outFile[-1] + ".ind"
        if os.path.isfile(outFile):
            print("Warning - there is already an index file for", targetFileName)
            print("in the ./intermediates/ directory. Aborting index operation.")
        outputFile = open(outFile,"w")

# Inspect the file byte by byte looking for blockmarks
    imList = []
    roiList = []
    hkList = []
    pdsList = []
    buffSize = len(dataBuff)
    Location = 0
    stillInBuffer = 1
    while stillInBuffer:
        if Location >= buffSize-1 and doAcceleratedScan: break
# Find CPI IMG blocks
        if dataBuff[Location] == '\xD5':
            if dataBuff[Location+1] == '\xA3':
                nROI = unpack("h",dataBuff[Location+8:Location+10])[0]
                if nROI < 300:
                    imList.append(("Img","21",Location, nROI))
                    if writeIndexFile: outputFile.write("{0}, Img21, {1}\n".format(Location,nROI))
                    if doAcceleratedScan:
                        nBYT = unpack("I",dataBuff[Location+2:Location+6])[0]
                        if nBYT > 150: nBYT = 1
#                        print nBYT
                        Location += (nBYT-1)
                        if Location >= buffSize-1: break
            if dataBuff[Location+1] == '\xA2':
                nROI = unpack("h",dataBuff[Location+8:Location+10])[0]
                if nROI < 300:
                    imList.append(("Img","20",Location, nROI))
                    if writeIndexFile: outputFile.write("{0}, Img20, {1}\n".format(Location,nROI))
                    if doAcceleratedScan:
                        nBYT = unpack("I",dataBuff[Location+2:Location+6])[0]
                        if nBYT > 150: nBYT = 1
#                        print nBYT
                        Location += (nBYT-1)
                        if Location >= buffSize-1: break
            if dataBuff[Location+1] == '\xA1':
                nROI = unpack("h",dataBuff[Location+8:Location+10])[0]
                if nROI < 300:
                    imList.append(("Img","19",Location, nROI))
                    if writeIndexFile: outputFile.write("{0}, ImgXX, {1}\n".format(Location,nROI))
                    if doAcceleratedScan:
                        nBYT = unpack("I",dataBuff[Location+2:Location+6])[0]
                        if nBYT > 150: nBYT = 1
 #                       print nBYT
                        Location += (nBYT-1)
                        if Location >= buffSize-1: break
# Find CPI ROI blocks
        if dataBuff[Location] == '\xE6':
            if dataBuff[Location+1] == '\xB2':
                rStX = unpack("H",dataBuff[Location+8:Location+10])[0]     #5
                rStY = unpack("H",dataBuff[Location+10:Location+12])[0]    #6
                rEnX = unpack("H",dataBuff[Location+12:Location+14])[0]    #7
                rEnY = unpack("H",dataBuff[Location+14:Location+16])[0]    #8
                pByt = unpack("h",dataBuff[Location+16:Location+18])[0]    #9
                bLen = (rEnX - rStX) * (rEnY - rStY) * pByt
                roiList.append(("ROI",Location,bLen))
                if writeIndexFile: outputFile.write("{0}, ROI, {1}\n".format(Location,bLen))
                if doAcceleratedScan:
#                    print (rEnX - rStX), (rEnY - rStY), pByt, bLen, Location
                    Location += (bLen-1)
                    if Location >= buffSize-1: break
# Find CPI HK blocks
        if dataBuff[Location] == '\xD6':
            if dataBuff[Location+1] == '\xA1':
                hkList.append(("HK","19",Location))
                print("HK","19",Location)
                nBYT = unpack("h",dataBuff[Location+2:Location+4])[0]
                if writeIndexFile: outputFile.write("{0}, HKXX\n".format(Location))
                if doAcceleratedScan:
                        nBYT = unpack("I",dataBuff[Location+2:Location+6])[0]
                        if nBYT > 150: nBYT = 1
#                        print nBYT
                        Location += (nBYT-1)
                        if Location >= buffSize-1: break
            if dataBuff[Location+1] == '\xA2':
                hkList.append(("HK","20",Location))
                print("HK","20",Location)
                if writeIndexFile: outputFile.write("{0}, HK20\n".format(Location))
                if doAcceleratedScan:
                        nBYT = unpack("I",dataBuff[Location+2:Location+6])[0]
                        if nBYT > 150: nBYT = 1
#                        print nBYT
                        Location += (nBYT-1)
                        if Location >= buffSize-1: break
        if dataBuff[Location] == '\xD7':
            if dataBuff[Location+1] == '\xA1':
                hkList.append(("HK","21",Location))
                print("HK","21",Location)
                if writeIndexFile: outputFile.write("{0}, HK21\n".format(Location))
                if doAcceleratedScan:
                        nBYT = unpack("I",dataBuff[Location+2:Location+6])[0]
                        if nBYT > 150: nBYT = 1
#                        print nBYT
                        Location += (nBYT-1)
                        if Location >= buffSize-1: break
        if dataBuff[Location] == '\x4b':
            if dataBuff[Location+1] == '\x48':
                if dataBuff[Location+2] == '\x53' and dataBuff[Location+3] == '\x00':
                    nBYT = unpack("h",dataBuff[Location+2:Location+4])[0]
                    hkList.append(("HK","3V",Location))
                    print("HK","21",Location)
                    if writeIndexFile: outputFile.write("{0}, HK3V\n".format(Location))
                    if doAcceleratedScan:
                        nBYT = unpack("I",dataBuff[Location+2:Location+6])[0]
                        if nBYT > 150: nBYT = 1
#                        print nBYT
                        Location += (nBYT-1)
                        if Location >= buffSize-1: break
# Find CPI VALID blocks
        if dataBuff[Location] == '\x1D':
            if dataBuff[Location+1] == '\xAE':
                imList.append(("VALID",Location))
                if writeIndexFile: outputFile.write("{0}, VALID1\n".format(Location))
        if dataBuff[Location] == '\x2D':
            if dataBuff[Location+1] == '\xBE':
                imList.append(("VALID",Location))
                if writeIndexFile: outputFile.write("{0}, VALID2\n".format(Location))
        if dataBuff[Location] == '\x3D':
            if dataBuff[Location+1] == '\xCE':
                imList.append(("VALID",Location))
                if writeIndexFile: outputFile.write("{0}, VALID3\n".format(Location))
# Find CPI PDS blocks
        if dataBuff[Location] == '\x50':
            if dataBuff[Location+1] == '\x44':
                if dataBuff[Location+4] == '\x50' and dataBuff[Location+5] == '\x50':
                    pdsList.append(("PDS",Location))
                    print("PDS",Location)
                    if writeIndexFile: outputFile.write("{0}, PDS\n".format(Location))
        Location += 1
        if Location == buffSize-1:
            stillInBuffer = 0
    if writeIndexFile: outputFile.close()
    return imList, hkList, roiList, pdsList
