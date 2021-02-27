from ..common.Canny import *

from PIL import Image
import numpy as np
from copy import deepcopy
from bitstring import BitStream
from struct import unpack
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw

def getFirstCPIbkg(dataBuff, startLoc, workArray, dispArray, ptDatCPI, hkDatCPI, nextSlice, actCol, actSlice, stampNum, stampLoc, stampContent, targetFileName):
    readParticles = 0
    Location = startLoc
    findType = -1
    numHSlice = -1
    numVSlice = -1
    ptDatCPI.nSli = 0
    ptDatCPI.nCol = 0
    ptDatCPI.HPtC = 0
    ptDatCPI.VPtC = 0
    stillInBuffer = 1
    while stillInBuffer:
        if dataBuff[Location] == '\xD5':
            if dataBuff[Location+1] == '\xA3':
                findType = 1
                thisFrameIsBackground = 0
                s = BitStream(bytes=dataBuff[Location+20:Location+22])
                hkDatCPI.BkBf, hkDatCPI.FROI, hkDatCPI.FstI, hkDatCPI.NewD, hkDatCPI.bkSb, hkDatCPI.iFull, hkDatCPI.isBk, hkDatCPI.imPr = s.readlist('8*bool')
                hkDatCPI.fStX = unpack("h",dataBuff[Location+22:Location+24])[0]      #12
                hkDatCPI.fStY = unpack("h",dataBuff[Location+24:Location+26])[0]      #13
                hkDatCPI.fEnX = unpack("h",dataBuff[Location+26:Location+28])[0]      #14
                hkDatCPI.fEnY = unpack("h",dataBuff[Location+28:Location+30])[0]      #15
                if hkDatCPI.isBk and hkDatCPI.imPr and hkDatCPI.fStX == 0 and fStY == 0 and hkDatCPI.fEnX > 1022 and hkDatCPI.fEnY > 1021:
                    thisFrameIsBackground = 1

# This should hopefully be thread safe for future use if we carefully divide dataBuff
# equally between threads. In the main application below startLoc is hard wired to
# value zero, but this provides for the DIFF files produced by CERN. This should be
#retained as a useful threading parameter.
def readCPIImageFrame(dataBuff, startLoc, workArray, dispArray, ptDatCPI, hkDatCPI, nextSlice, actCol, actSlice, stampNum, stampLoc, stampContent, targetFileName, currentCPIBackGround):
    bufferSize = len(dataBuff)
    readParticles = 0
    Location = startLoc
    findType = -1
    numHSlice = -1
    numVSlice = -1
    ptDatCPI.nSli = 0
    ptDatCPI.nCol = 0
    ptDatCPI.HPtC = 0
    ptDatCPI.VPtC = 0

    findType = 1
    thisFrameIsBackground = 0
    hkDatCPI.fByt = unpack("I",dataBuff[Location+2:Location+6])[0]        #02 - Total bytes in image block
    hkDatCPI.fTyp = unpack("h",dataBuff[Location+6:Location+8])[0]/10.0   #03 - Image data block version number
    hkDatCPI.nROI = unpack("h",dataBuff[Location+8:Location+10])[0]       #04 - Number of ROIs contained in block
    hkDatCPI.nByt = unpack("I",dataBuff[Location+10:Location+14])[0]      #05 - Total bytes of image data in block
    hkDatCPI.iDay = unpack("B",dataBuff[Location+14:Location+15])[0]      #06 - Day
    hkDatCPI.iHou = unpack("B",dataBuff[Location+15:Location+16])[0]      #07 - Hour
    hkDatCPI.iMin = unpack("B",dataBuff[Location+16:Location+17])[0]      #08 - Minute
    hkDatCPI.iSec = unpack("B",dataBuff[Location+17:Location+18])[0]      #09 - Second
    hkDatCPI.iMsc = unpack("h",dataBuff[Location+18:Location+20])[0]      #10 - Millisecond
    hkDatCPI.iTyt = unpack("h",dataBuff[Location+20:Location+22])[0]      #11 - Image type - see s.readlist below
    s = BitStream(bytes=dataBuff[Location+20:Location+22])
    hkDatCPI.fStX = unpack("h",dataBuff[Location+22:Location+24])[0]      #12 - ROI top left corner X co-ordinate
    hkDatCPI.fStY = unpack("h",dataBuff[Location+24:Location+26])[0]      #13 - ROI top left corner Y co-ordinate
    hkDatCPI.fEnX = unpack("h",dataBuff[Location+26:Location+28])[0]      #14 - ROI lower right corner X co-ordinate
    hkDatCPI.fEnY = unpack("h",dataBuff[Location+28:Location+30])[0]      #15 - ROI lower right corner Y co-ordinate
#    hkDatCPI.imPr, hkDatCPI.isBk, hkDatCPI.iFull, hkDatCPI.bkSb, hkDatCPI.NewD, hkDatCPI.FstI, hkDatCPI.FROI, hkDatCPI.BkBf = s.readlist('8*bool')
    hkDatCPI.BkBf, hkDatCPI.FROI, hkDatCPI.FstI, hkDatCPI.NewD, hkDatCPI.bkSb, hkDatCPI.iFull, hkDatCPI.isBk, hkDatCPI.imPr = s.readlist('8*bool')
    printBkgState = 0
    if printBkgState:
        imPres = "        "
        isBCK = "        "
        isFull = "        "
        isSubd = "        "
        isNDat = "        "
        isFirst = "        "
        isFoundROI = "        "
        isBckBuff = "        "
        if hkDatCPI.imPr:
            imPres = "ImagePr "
        if hkDatCPI.isBk:
            isBCK = "BackGnd "
        if hkDatCPI.iFull:
            isFull = "FullFra "
        if hkDatCPI.bkSb:
            isSubd = "BkgSubd "
        if hkDatCPI.NewD:
            isNDat = "NewData "
        if hkDatCPI.FstI:
            isFirst = "FirstIm "
        if hkDatCPI.FROI:
            isFoundROI = "GotROI  "
        if hkDatCPI.BkBf:
            isBckBuff = "BkgBuff "
        if hkDatCPI.isBk:
            print imPres, isBCK, isFull, isSubd, isNDat, isFirst, isFoundROI, isBckBuff, hkDatCPI.fStX, hkDatCPI.fStY, hkDatCPI.fEnX, hkDatCPI.fEnY
    if hkDatCPI.isBk and hkDatCPI.imPr and hkDatCPI.fStX == 0 and hkDatCPI.fStY == 0 and hkDatCPI.fEnX > 1022 and hkDatCPI.fEnY > 1021:
        thisFrameIsBackground = 1
    hkDatCPI.bkgR = unpack("h",dataBuff[Location+30:Location+32])[0]/10.0 #16 - Background rate in tenths of seconds
    hkDatCPI.nPDS = unpack("h",dataBuff[Location+32:Location+34])[0]      #17 - Maximum number of PDS strobes to tolerate for background to be taken
    hkDatCPI.tNFP = unpack("I",dataBuff[Location+34:Location+38])[0]      #18 - Total number of frames processed so far
    hkDatCPI.thrs = unpack("B",dataBuff[Location+38:Location+39])[0]      #19 - Image threshold (0 to 255)
    hkDatCPI.rErr = unpack("B",dataBuff[Location+39:Location+40])[0]      #20 - ROI error - rejection failure code
    hkDatCPI.mnes = unpack("h",dataBuff[Location+40:Location+42])[0]      #21 - Minimum ROI size
    hkDatCPI.asRt = unpack("f",dataBuff[Location+42:Location+46])[0]      #22 - Aspect ratio rejection criterion
    hkDatCPI.flRt = unpack("f",dataBuff[Location+46:Location+50])[0]      #23 - Minimum ROI fill ratio
    hkDatCPI.pCnt = unpack("I",dataBuff[Location+50:Location+54])[0]      #24 - Number of pixels in ROI above threshold
    hkDatCPI.imMn = unpack("B",dataBuff[Location+54:Location+55])[0]      #25 - Image mean intensity
    hkDatCPI.bkMn = unpack("B",dataBuff[Location+55:Location+56])[0]      #26 - Background mean intensity
    hkDatCPI.spr1 = unpack("h",dataBuff[Location+56:Location+58])[0]      #27 - SPARE 1
    hkDatCPI.xPad = unpack("h",dataBuff[Location+58:Location+60])[0]      #28 - ROI horizontal border pad
    hkDatCPI.yPad = unpack("h",dataBuff[Location+60:Location+62])[0]      #29 - ROI vertical border pad
    hkDatCPI.sCnt = unpack("I",dataBuff[Location+62:Location+66])[0]      #30 - Strobe count (per image basis)
    hkDatCPI.fSav = unpack("I",dataBuff[Location+66:Location+70])[0]      #31 - Number of frames saved to disc so far
    hkDatCPI.minV = unpack("B",dataBuff[Location+70:Location+71])[0]      #32 - Minimum image mean for an acceptable frame
    hkDatCPI.maxV = unpack("B",dataBuff[Location+71:Location+72])[0]      #33 - Maximum image mean for acceptable image
    hkDatCPI.rSav = unpack("I",dataBuff[Location+72:Location+76])[0]      #34 - Number of ROIs saved so far
    hkDatCPI.PCsF = unpack("h",dataBuff[Location+76:Location+78])[0]      #35 - PDS checksum flag
    hkDatCPI.PDH1 = unpack("h",dataBuff[Location+78:Location+80])[0]      #36 - PDS header 1
    hkDatCPI.PDH2 = unpack("h",dataBuff[Location+80:Location+82])[0]      #37 - PDS header 2
    hkDatCPI.PDH3 = unpack("h",dataBuff[Location+82:Location+84])[0]      #38 - PDS header 3
    hkDatCPI.tSOY = unpack("I",dataBuff[Location+84:Location+88])[0]      #39 - Seconds into current year
    hkDatCPI.PAT1 = unpack("h",dataBuff[Location+88:Location+90])[0]      #40 - Arrival time 1 - number of 62.5ms chunks into second
    hkDatCPI.PAT2 = unpack("h",dataBuff[Location+90:Location+92])[0]      #41 - Arrival time 2 - number of 0.8us chunks into 16th
    hkDatCPI.tTrn = unpack("h",dataBuff[Location+92:Location+94])[0]      #42 - Transit time
    hkDatCPI.Strs = unpack("h",dataBuff[Location+94:Location+96])[0]      #43 - Number of strobes since last PDS packet
    hkDatCPI.PI45 = unpack("h",dataBuff[Location+96:Location+98])[0]      #44 - Pulse height 45
    hkDatCPI.PI90 = unpack("h",dataBuff[Location+98:Location+100])[0]     #45 - Pulse height 90
    hkDatCPI.pdCS = unpack("h",dataBuff[Location+100:Location+102])[0]    #46 - PDS checksum
    hkDatCPI.pbMd = unpack("h",dataBuff[Location+102:Location+104])[0]    #47 - Probe mode <---- End of frame header

    frameStamp = "%02d" % hkDatCPI.iHou +":"+"%02d" % hkDatCPI.iMin +":"+"%02d" % hkDatCPI.iSec +":"+"%03d" % hkDatCPI.iMsc
    Location += 104
    isValidParticle = 0
# Read all ROIs contained in the image - need to import the ROI location list to this function and pop(0) entries from it
    if hkDatCPI.nROI > 0: print "nROI = ", hkDatCPI.nROI
    for pNum in range(hkDatCPI.nROI):
        print(pNum)
        isValidParticle, Location, actCol, actSlice, nextSlice, stampNum, stampLoc, stampContent, currentCPIBackGround = readCPIROIHeader(hkDatCPI, ptDatCPI, Location, dataBuff, workArray, dispArray, nextSlice, actCol, actSlice, stampNum, stampLoc, stampContent, frameStamp, targetFileName, thisFrameIsBackground, currentCPIBackGround)

    return findType, isValidParticle, hkDatCPI, workArray, ptDatCPI.nCol, ptDatCPI.nSli, Location, hkDatCPI.tSOY, actCol, actSlice, nextSlice, stampNum, stampLoc, stampContent, currentCPIBackGround

def readCPIROIHeader(hkDatCPI, ptDatCPI, Location, dataBuff, workArray, dispArray, nextSlice, actCol, actSlice, stampNum, stampLoc, stampContent, frameStamp, targetFileName, thisFrameIsBackground, currentCPIBackGround):
    hkDatCPI.rHed = unpack("H",dataBuff[Location:Location+2])[0]        #1 <---- Start of ROI header
    hkDatCPI.rByt = unpack("H",dataBuff[Location+2:Location+4])[0]      #2 - 
    hkDatCPI.rUnk = unpack("H",dataBuff[Location+4:Location+6])[0]      #3 - 
    hkDatCPI.rTyp = unpack("H",dataBuff[Location+6:Location+8])[0]/10.0 #4 - 
    hkDatCPI.rStX = unpack("H",dataBuff[Location+8:Location+10])[0]     #5
    hkDatCPI.rStY = unpack("H",dataBuff[Location+10:Location+12])[0]    #6
    hkDatCPI.rEnX = unpack("H",dataBuff[Location+12:Location+14])[0]    #7
    hkDatCPI.rEnY = unpack("H",dataBuff[Location+14:Location+16])[0]    #8
    hkDatCPI.pByt = unpack("H",dataBuff[Location+16:Location+18])[0]    #9
    hkDatCPI.rFlg = unpack("H",dataBuff[Location+18:Location+20])[0]    #10
    hkDatCPI.rLen = unpack("H",dataBuff[Location+20:Location+22])[0]    #11
    hkDatCPI.sLen = unpack("H",dataBuff[Location+22:Location+24])[0]    #12
    hkDatCPI.eLen = unpack("H",dataBuff[Location+24:Location+26])[0]    #13
    hkDatCPI.rWid = unpack("H",dataBuff[Location+26:Location+28])[0]    #14
    hkDatCPI.sWid = unpack("H",dataBuff[Location+28:Location+30])[0]    #15
    hkDatCPI.eWid = unpack("H",dataBuff[Location+30:Location+32])[0]    #16
    hkDatCPI.Dark = unpack("H",dataBuff[Location+32:Location+34])[0]    #17
    hkDatCPI.Area = unpack("H",dataBuff[Location+34:Location+36])[0]    #18
    hkDatCPI.Prim = unpack("H",dataBuff[Location+36:Location+38])[0]    #19 <---- End of ROI header V25

    isValidParticle = 0
    if 0 < hkDatCPI.iDay <= 31 and 0 <= hkDatCPI.iHou < 24 and 0 <= hkDatCPI.iMin < 60 and 0 <= hkDatCPI.iSec < 60 and hkDatCPI.nByt > 0:
        isValidParticle = 1
    Location += 54

    ptDatCPI.nCol, ptDatCPI.nSli, actCol, actSlice, nextSlice, stampNum, stampLoc, stampContent, currentCPIBackGround = readCPIROI(hkDatCPI.rStX, hkDatCPI.rStY, hkDatCPI.rEnX, hkDatCPI.rEnY, dataBuff, workArray, dispArray, Location, nextSlice, actCol, actSlice, stampNum, stampLoc, stampContent, frameStamp, targetFileName, thisFrameIsBackground, currentCPIBackGround)

    Location += (ptDatCPI.nCol * ptDatCPI.nSli)
    print(ptDatCPI.nCol * ptDatCPI.nSli, Location)
    return isValidParticle, Location, actCol, actSlice, nextSlice, stampNum, stampLoc, stampContent, currentCPIBackGround

def readCPIROI(stX, stY, enX, enY, dataBuff, workArray, dispArray, Location, nextSlice, actCol, actSlice, stampNum, stampLoc, stampContent, frameStamp, targetFileName, thisFrameIsBackground, currentCPIBackGround):
    dX = enX - stX
    dY = enY - stY
    if stX < 0 or stY < 0 or enX > 1024 or enY > 1024 or dX < 1 or dY < 1:
        print "Particle size error: Starts",stX,stY,"ends:",enX,enY,"size:",dX,dY 
        return 0, 0, actCol, actSlice, nextSlice, stampNum, stampLoc, stampContent, currentCPIBackGround
    nPix = (1 + dX) * (1 + dY)
    xLoc = 0
    yLoc = 0
    for i in xrange (0,nPix):
        pixVal = unpack("B",dataBuff[Location+i:Location+1+i])[0]
        workArray[yLoc,xLoc,0:3] = (pixVal,pixVal,pixVal)
        if xLoc == dX:
            xLoc = 0
            yLoc += 1
        else:
            xLoc += 1

    doCanny = 0
    doBkgSubtract = 0
    doMarkEdges = 1
    doMarkBox = 1
# If this is a background, store it.
    if thisFrameIsBackground:
        currentCPIBackGround[:,:,:] = workArray[:,:,:]
        print "Read new background"
# OK. Got the image out. Now we can start to process it.
    elif doCanny:
        if doBkgSubtract:
            workArray = bkgRawSubtract(workArray, currentCPIBackGround, stX, stY, dX, dY)
        sigma = 3
        lowThresh = 0.00002
        highThresh = 0.3
        edges, boxVals, floodArea = CannyEdge(workArray, dX, dY, sigma, lowThresh, highThresh, currentCPIBackGround, stX, stY)
#        print "Box: ", boxVals['area'], "Flood: ", floodArea, "Ratio: ", floodArea/boxVals['area']
        if doMarkEdges:
# Mark edges orange - RGB = (255,165,0)
            workArray[np.where(edges)] = (255,165,0)
        if doMarkBox and len(boxVals['corners']) > 3:
# Mark MinAreaRect green - RGB = (127,255,0)
            img = Image.fromarray(workArray)
            draw = ImageDraw.Draw(img)
            draw.polygon([tuple(p) for p in boxVals['corners']], fill=None, outline = (127,255,0))
            boxedData = np.asarray(img)
            workArray[:,:,:] = boxedData[:,:,:]
# Add the new image to the output sheet.
    if not thisFrameIsBackground:
        actSlice, actCol, nextSlice, stampNum, stampLoc, stampContent = addCPIImage(workArray, dispArray, dX, dY, nextSlice, actCol, actSlice, stampNum, stampLoc, stampContent, frameStamp, targetFileName)
    return dX, dY, actCol, actSlice, nextSlice, stampNum, stampLoc, stampContent, currentCPIBackGround

def bkgRawSubtract(image, bkg, xTL, yTL, dX, dY):
# JRD - This is fucking clumsy - need to do better - TRY - if abs(image-bkg)>someValue: image=image else: image=0
    for i in xrange(0,dY):
        for j in xrange(0,dX):
            if image[i, j, 0] - bkg[i, j, 0] > 0:
                image[i, j, :] = image[i, j, 0] - bkg[i, j, 0]
            else:
                image[i, j, :] = 0
    return image

# Exception to deal with (alleged) stereo particle events
class GetOutOfLoop(Exception):
     pass

# Set up frames and title in image display page
def setCPIBkg(workArray, bkgColor):
    workArray[:,:,] = bkgColor

def addCPIImage(workArray, dispArray, numCols, numSlices, nextSlice, actCol, actSlice, stampNum, stampLoc, stampContent, frameStamp, targetFileName):
    print "Adding image", numCols, " x ", numSlices
    if (actCol + numCols) <= 1714 and (nextSlice + numSlices) < 1230:
        stampContent.append(frameStamp)
        stampLoc[stampNum,0] = actCol
        stampLoc[stampNum,1] = actSlice + numSlices + 1
        stampNum += 1
        dispArray[actSlice : actSlice + numSlices, actCol : actCol + numCols, :] = workArray[0 : numSlices, 0 : numCols]
        actCol += 2 + numCols
        if 2 + 9 + actSlice + numSlices > nextSlice:
            nextSlice = 2 + 9 + actSlice + numSlices
        workArray[0:1024, 0:1024, 0:3] = 255
        return actSlice, actCol, nextSlice, stampNum, stampLoc, stampContent
    elif (actCol + numCols) > 1714 and (nextSlice + numSlices) < 1230:
        actCol = 40
        actSlice = nextSlice
        stampContent.append(frameStamp)
        stampLoc[stampNum,0] = actCol
        stampLoc[stampNum,1] = actSlice + numSlices + 1
        stampNum += 1
        dispArray[actSlice : actSlice + numSlices, actCol : actCol + numCols, :] = workArray[0 : numSlices, 0 : numCols]
        actCol += 2 + numCols
        if 2 + 9 + actSlice + numSlices > nextSlice:
            nextSlice = 2 + 9 + actSlice + numSlices
        workArray[0:1024, 0:1024, 0:3] = 255
        return actSlice, actCol, nextSlice, stampNum, stampLoc, stampContent
    else:
        plotCPIImage(dispArray, stampLoc, stampContent, stampNum, targetFileName)
        actCol = 40
        actSlice = 80
        nextSlice = 80
        setCPIBkg(dispArray, 255)
        stampNum = 0
        stampContent = []
        stampLoc[stampNum,0] = actCol
        stampLoc[stampNum,1] = actSlice + numSlices + 1
        stampContent.append(frameStamp)
        stampNum += 1
        dispArray[actSlice : actSlice + numSlices, actCol : actCol + numCols, :] = workArray[0 : numSlices, 0 : numCols]
        actCol += 2 + numCols
        if 2 + 9 + actSlice + numSlices > nextSlice:
            nextSlice = 2 + 9 + actSlice + numSlices
        workArray[0:1024, 0:1024, 0:3] = 255
        return actSlice, actCol, nextSlice, stampNum, stampLoc, stampContent

def plotCPIImage(dispArray, stampLoc, stampContent, stampNum, targetFileName):
    im=Image.Image()
    im=Image.fromarray(dispArray)
    for i in xrange (0,stampNum):
#        print i, stampContent[i], stampLoc[i,0], stampLoc[i,1]
        drawText(im,stampContent[i], stampLoc[i,0], stampLoc[i,1], 8)
    drawText(im,"CPI DATA - time range "+stampContent[0]+" to "+stampContent[stampNum-1], 40, 20, 24)
    drawText(im,"RAW FILE: "+targetFileName, 40, 45, 24)
    drawText(im,"Extracted using pyCPI - "+u"\u00A9"+" James Dorsey - University of Manchester - 2013", 1350, 25, 10)
    draw = ImageDraw.Draw(im)
    draw.line((1350, 50, 1393, 50), fill=0, width = 2)
    drawText(im,"100 "+u"\u03BC"+"m scale line", 1400, 43, 10)
    del draw
    imFileName = "output/" + stampContent[0]+"-"+stampContent[stampNum-1]+".png"
    imFileName = imFileName.replace(":", "")
    im.save(imFileName)
    print "Writing image file ", imFileName

# Direct copy of the function in pyCPI - move this to a common file
def drawText(img, textString, xLoc, yLoc, fontSize):
    font = ImageFont.truetype("/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf",fontSize)
    draw = ImageDraw.Draw(img)
    draw.text((xLoc, yLoc),textString,(0,0,0),font=font)
    draw = ImageDraw.Draw(img)
    draw = ImageDraw.Draw(img)

class houseRecordCPI(object):
    '''ITERABLE data structure to receive CPI housekeeping data'''

    def __init__(self):
        self.pLen = 63905 #02 - Packet length (83)
        self.tFST = 63905 #03 - Forward sample tube temperature
        self.tUOB = 63905 #04 - Upper optics block temperature
        self.tLOB = 63905 #05 - Lower optics block temperature
        self.tCST = 63905 #06 - Central sample tube temperature
        self.tFBL = 63905 #07 - FibreLink temperature (old aft sample tube)
        self.tNCo = 63905 #08 - Nose cone temperarure
        self.tPy2 = 63905 #09 - Pylon temperature 2
        self.tPy3 = 63905 #10 - Pylon temperature 3
        self.tCCD = 63905 #11 - CCD camera temperature
        self.tILn = 63905 #12 - Imaging lens temperature
        self.fILs = 63905 #13 - Imaging laser temperature
        self.tLsV = 63905 #14 - PDS45 (or vertical) laser temperature
        self.tLsH = 63905 #15 - PDS90 (or horizontal) laser temperature
        self.tPBd = 63905 #16 - Power board temperature
        self.tVPl = 63905 #17 - PDS45 (or vertical) platen temperature
        self.tVOp = 63905 #18 - PDS45 optics temperature
        self.tHPl = 63905 #19 - PDS90 platen temperature
        self.tHOp = 63905 #20 - PDS90 optics temperature
        self.tVIM = 63905 #21 - PDS45 input mirror temperature
        self.tHIM = 63905 #22 - PDS90 input mirror temperature
        self.tAir = 63905 #23 - Internal air temperature
        self.tDSP = 63905 #24 - DSP card temperature
        self.tVAT = 63905 #25 - PDS45 array top temperature
        self.tVAB = 63905 #26 - PDS45 array bottom temperature
        self.tHAT = 63905 #27 - PDS90 array top temperature
        self.tHAB = 63905 #28 - PDS90 array bottom temperature
        self.relH = 63905 #29 - Relative humidity
        self.canP = 63905 #30 - Internal pressure - PSI
        self.VTcC = 63905 #31 - PDS45 TEC current - A
        self.HTcC = 63905 #32 - PDS90 TEC current - A
        self.VLsO = 63905 #33 - PDS45 laser on (unused)
        self.HLsO = 63905 #34 - PDS90 laser on (unused)
        self.vMSe = 63905 #35 - -7V monitor - V
        self.vPSe = 63905 #36 - +7V monitor V
        self.v000 = 63905 #37 - PDS45 diode element 0 - V
        self.v021 = 63905 #38 - PDS45 diode element 21 - V
        self.v042 = 63905 #39 - PDS45 diode element 42 - V
        self.v064 = 63905 #40 - PDS45 diode element 64 - V
        self.v085 = 63905 #41 - PDS45 diode element 85 - V
        self.v106 = 63905 #42 - PDS45 diode element 106 - V
        self.v127 = 63905 #43 - PDS45 diode element 127 - V
        self.cImL = 63905 #44 - Imaging laser measured current
        self.h000 = 63905 #45 - PDS90 diode element 0 - V
        self.h021 = 63905 #46 - PDS90 diode element 21 - V
        self.h042 = 63905 #47 - PDS90 diode element 42 - V
        self.h064 = 63905 #48 - PDS90 diode element 64 - V
        self.h085 = 63905 #49 - PDS90 diode element 85 - V
        self.h106 = 63905 #50 - PDS90 diode element 106 - V
        self.h127 = 63905 #51 - PDS90 diode element 127 - V
        self.ILWm = 63905 #52 - Imaging laser measured pulse width - V
        self.ILCs = 63905 #53 - Imaging laser current set point - V
        self.ILWs = 63905 #54 - Imaging laser pulse width control set point - V
        self.pbMd = 63905 #55 - Probe mode - bit mapped
        self.htMd = 63905 #56 - Heater mode - bit mapped
        self.oPWM = 63905 #57 - Optical block PWM percentage - %
        self.nHpt = 63905 #58 - Number of H particles detected
        self.nVpt = 63905 #59 - Number of V particles detected
        self.tDed = 63905 #60 - Dead time - s
        self.MSFi = 63905 #61 - Maximum slices to fire on - bit mapped
        self.LTDl = 63905 #62 - Laser trigger delay and minimum pixels before firing - bit mapped
        self.vLPS = 63905 #63 - PDS45 laser power set point
        self.hLPS = 63905 #64 - PDS90 laser power set point
        self.vMBC = 63905 #65 - PDS45 masked bits count
        self.hMBC = 63905 #66 - PDS90 masked bits count
        self.nHOP = 63905 #67 - Number of horizontal overload periods
        self.nVOP = 63905 #68 - Number of vertical overload periods
        self.nStP = 63905 #69 - Number of detected stereo particles
        self.cCon = 63905 #70 - 2DS compression configuration - bit mapped
        self.PAW1 = 63905 #71 - PDS alignment info word 1 (unused)
        self.PAW2 = 63905 #72 - PDS alignment info word 2 (unused)
        self.tMSW = 63905 #73 - Timing word bits 47 to 32 (MSW)
        self.tISW = 63905 #74 - Timing word bits 31 to 16 (ISW)
        self.tLSW = 63905 #75 - Timing word bits 15 to 0 (LSW)
        self.tsW1 = 63905 #76 - TAS floating point word 1
        self.tsW2 = 63905 #77 - TAS floating point word 2
        self.CA2D = 63905 #78 - 2DS commands accepted
        self.CACP = 63905 #79 - CPI commands accepted
        self.n2DB = 63905 #80 - Number od 2DS data blocks sent in the last second
        self.ASOF = 63905 #81 - Array skew offset / fuzzy skew - bit mapped
        self.CPIS = 63905 #82 - CPI image stats - bit mapped
        self.Chck = 63905 #83 - Checksum

    def __iter__(self):
        for each in self.__dict__.keys():
            yield self.__getattribute__(each)

# Empty data container for single particle data - ACHTUNG - allocated at runtime
class particleRecord2DS:
    pass
