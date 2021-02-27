import datetime
import time
import os
from bitstring import BitStream
from struct import unpack

from PIL import Image
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw

# This should hopefully be thread safe for future use if we carefully divide dataBuff
# equally between threads. In the main application below startLoc is hard wired to
# value zero, but this provides for the DIFF files produced by CERN. This should be
#retained as a useful threading parameter.
def read2DSData(dataBuff, startLoc, time2DS, hWorkArray, vWorkArray, ptDat2DS, hkDat2DS):
    probeResolution = 1E-5 # 10 um in m
    bufferSize = len(dataBuff)
    readParticles = 1
    Location = startLoc
    findType = -1
    stillInBuffer = 1
    while stillInBuffer:
        if dataBuff[Location] == "K":
            if dataBuff[Location+1] == "H":
                if ((dataBuff[Location+106:Location+108] == "KM" or dataBuff[Location+106:Location+108] == "LN") or dataBuff[Location+106:Location+108] == "S2"):
                    if unpack("h",dataBuff[Location+8:Location+10])[0]*0.00244140625 < 5 and unpack("h",dataBuff[Location+98:Location+100]) != 1 and unpack("h",dataBuff[Location+2:Location+4])[0]*0.00244140625 < 5:
# This is definitely an HK packet, so decode it...
                        hkDat2DS, Location, findType = decodeHKPacket(hkDat2DS, dataBuff, Location)
# Update probe time from tick counter based on HK packet
                        time2DS.TAS = hkDat2DS.TASw
                        time2DS.timeWord = hkDat2DS.TMwr
                        updateCurrentTime(time2DS, "HK")
                        return findType, time2DS, hWorkArray, vWorkArray, 0, Location
        if readParticles:
            if dataBuff[Location] == "S":
                if dataBuff[Location+1] == "2":
                    findType, time2DS, hWorkArray, vWorkArray, ptDat2DS.NSli, Location = decodeIMPacket(ptDat2DS, Location, time2DS, hWorkArray, vWorkArray, dataBuff, findType)
                    return findType, time2DS, hWorkArray, vWorkArray, ptDat2DS.NSli, Location
        Location += 1
        if Location >= bufferSize:
            stillInBuffer = 0
            return findType, time2DS, hWorkArray, vWorkArray, ptDat2DS.NSli, Location

def decodeIMPacket(ptDat2DS, Location, time2DS, hWorkArray, vWorkArray, dataBuff, findType):
# Set up image analysis options
    doCanny = 0
# Set some default values for particle and data packet decriptors
    numHSlice = -1
    numVSlice = -1
    ptDat2DS.NSli = 0
    ptDat2DS.HPtC = 0
    ptDat2DS.VPtC = 0
    ptDat2DS.HTWd = 0
    ptDat2DS.VTWd = 0
# Load horizontal image descriptors
    if time2DS.buffSize - Location < 20000:
        print "Warning: Reached position ", Location, " of ", time2DS.buffSize, " in input file"
    s = BitStream(bytes=dataBuff[Location+3:Location+4]+dataBuff[Location+2:Location+3])
    ptDat2DS.HTWF, ptDat2DS.SPRc, ptDat2DS.HFOE, ptDat2DS.HOTW, ptDat2DS.NHwd = s.readlist('4*bool,uint:12')
    ptDat2DS.HTWF = not ptDat2DS.HTWF
# Load vertical image descriptors
    s = BitStream(bytearray(dataBuff[Location+5:Location+6]+dataBuff[Location+4:Location+5]))
    ptDat2DS.VTWF, ptDat2DS.VTWM, ptDat2DS.VFOE, ptDat2DS.VOTW, ptDat2DS.NVwd = s.readlist('4*bool,uint:12')
    ptDat2DS.VTWF = not ptDat2DS.VTWF
# Load some common image descriptors
    PTCt = unpack("H",dataBuff[Location+6:Location+8])[0]
#    print "PTCt: ", PTCt
    ptDat2DS.NSli = unpack("H",dataBuff[Location+8:Location+10])[0]
    if ptDat2DS.NSli > 1280:
        print "Warning: Particle length > 12800 um (", 10*ptDat2DS.NSli, "um) - skipping!"
        Location += 1
        return -1, time2DS, hWorkArray, vWorkArray, ptDat2DS.NSli, Location
# If there is only H data present, then read it
    if ptDat2DS.NHwd:
        ptDat2DS.HPtC = PTCt
    elif ptDat2DS.NVwd:
        ptDat2DS.VPtC = PTCt
    else:
        print "Warning: No horizontal or vertical words found!"
        Location += 1
        return findType, time2DS, hWorkArray, vWorkArray, ptDat2DS.NSli, Location
    try:
        if ptDat2DS.NHwd:
            if ptDat2DS.NVwd:
                print "Warning: Both horizontal and vertical words found! - (", ptDat2DS.NHwd, ",", ptDat2DS.NVwd, ")"
                Location += 1
                raise GetOutOfLoop
            findType = 1
            hElLoc = 0
# Here if ptDat2DS.HTWF = 1 then remove last two 8 bit words from length of NHwd and treat these as the time stamp
            if ptDat2DS.HTWF:
                ptDat2DS.NHwd -= 2
                if ptDat2DS.NHwd < 1:
                    print "Warning: Aborting H image read as there are less than two words including timing information (", ptDat2DS.NHwd, ")"
                    raise GetOutOfLoop
            for word in xrange(0,ptDat2DS.NHwd):
                s = BitStream(bytes=dataBuff[Location+(11+(2*word)):Location+(12+(2*word))]+dataBuff[Location+(10+(2*word)):Location+(11+(2*word))])
                isImWd, isStartSlice, off, on = s.readlist('2*bool,2*uint:7')
                isImWd = not isImWd
                if isImWd:
                    if isStartSlice:
                        hElLoc = 0
                        numHSlice += 1
                        if numHSlice >= 1280:
                            print "Warning: H-slice count exceeds possible range - aborting on ", numHSlice, " of ", ptDat2DS.NSli, " in ", PTCt
                            Location += 1
                            return -1, time2DS, hWorkArray, vWorkArray, ptDat2DS.NSli, Location
                    hWorkArray[numHSlice,hElLoc+on:hElLoc+on+off,:] = (0,0,0)
                    hElLoc += on + off
            Location += (12+(2*word))
# Here if ptDat2DS.HTWF = 1 then read the timing word
            if ptDat2DS.HTWF:
                ptDat2DS.HTwr = unpack("I",dataBuff[Location+2:Location+4]+dataBuff[Location:Location+2])[0]
                Location += 2
                time2DS.timeWord = ptDat2DS.HTwr
                updateCurrentTime(time2DS, "H")
# If there is only V data present, then read it
        if ptDat2DS.NVwd:
            findType = 2
            vElLoc = 0
# Here if ptDat2DS.VTWF = 1 then remove last two 8 bit words from length of NVwd and treat these as the time stamp
            if ptDat2DS.VTWF:
                ptDat2DS.NVwd -= 2
                if ptDat2DS.NVwd < 1:
                    print "Warning: Aborting V image read as there are less than two words including timing information (", ptDat2DS.NVwd, ")"
                    raise GetOutOfLoop
            for word in xrange(0,ptDat2DS.NVwd):
                s = BitStream(bytes=dataBuff[Location+(11+(2*word)):Location+(12+(2*word))]+dataBuff[Location+(10+(2*word)):Location+(11+(2*word))])
                isImWd, isStartSlice, off, on = s.readlist('2*bool,2*uint:7')
                isImWd = not isImWd
                if isImWd:
                    if isStartSlice:
                        vElLoc = 0
                        numVSlice += 1
                        if numVSlice >= 1280:
                            print "Warning: V-slice count exceeds possible range - aborting on ", numVSlice, " of ", ptDat2DS.NSli
                            Location += 1
                            return -1, time2DS, hWorkArray, vWorkArray, ptDat2DS.NSli, Location
                    vWorkArray[numVSlice,vElLoc+on:vElLoc+on+off,:] = (0,0,0)
                    vElLoc += on + off
            Location += (12+(2*word))
# Here if ptDat2DS.VTWF = 1 then read the timing word
            if ptDat2DS.VTWF:
                ptDat2DS.VTwr = unpack("I",dataBuff[Location+2:Location+4]+dataBuff[Location:Location+2])[0]
                Location += 2
                time2DS.timeWord = ptDat2DS.VTwr
                updateCurrentTime(time2DS, "V")
# Update probe time from tick counter based on H or V image packet
        if doCanny:
            edges, boxVals, floodArea = CannyEdge(workArray, dX, dY, sigma, lowThresh, highThresh, currentCPIBackGround, stX, stY)
        return findType, time2DS, hWorkArray, vWorkArray, ptDat2DS.NSli, Location
    except GetOutOfLoop:
        Location += 1
        pass
    return findType, time2DS, hWorkArray, vWorkArray, ptDat2DS.NSli, Location

def decodeHKPacket(hkDat2DS, dataBuff, Location):
    findType = 0
    hkDat2DS.H000 = unpack("h",dataBuff[Location+2:Location+4])[0] * 0.00244140625        #02 - H element 0 voltage
    hkDat2DS.H064 = unpack("h",dataBuff[Location+4:Location+6])[0] * 0.00244140625        #03 - H element 64 voltage
    hkDat2DS.H127 = unpack("h",dataBuff[Location+6:Location+8])[0] * 0.00244140625        #04 - H element 127 voltage
    hkDat2DS.V000 = unpack("h",dataBuff[Location+8:Location+10])[0]* 0.00244140625        #05 - V element 0 voltage
    hkDat2DS.V064 = unpack("h",dataBuff[Location+10:Location+12])[0]*0.00244140625        #06 - V element 64 voltage
    hkDat2DS.V127 = unpack("h",dataBuff[Location+12:Location+14])[0]*0.00244140625        #07 - V element 127 voltage
    hkDat2DS.PS_V = unpack("H",dataBuff[Location+14:Location+16])[0]*0.00488400488        #08 - Positive supply voltage
    hkDat2DS.NS_V = unpack("H",dataBuff[Location+16:Location+18])[0]*0.00488400488        #09 - Negative supply voltage
    hkDat2DS.HTAT = unpack("H",dataBuff[Location+18:Location+20])[0]*0.0244140625 + 1.6   #10 - H transmit arm temp
    hkDat2DS.HRAT = unpack("H",dataBuff[Location+20:Location+22])[0]*0.0244140625 + 1.6   #11 - H receive arm temp
    hkDat2DS.VTAT = unpack("H",dataBuff[Location+22:Location+24])[0]*0.0244140625 + 1.6   #12 - V transmit arm temp
    hkDat2DS.VRAT = unpack("H",dataBuff[Location+24:Location+26])[0]*0.0244140625 + 1.6   #13 - V receive arm temp
    hkDat2DS.HTTT = unpack("H",dataBuff[Location+26:Location+28])[0]*0.0244140625 + 1.6   #14 - H transmit tip temp
    hkDat2DS.HRTT = unpack("H",dataBuff[Location+28:Location+30])[0]*0.0244140625 + 1.6   #15 - H receive tip temp
    hkDat2DS.ROBT = unpack("H",dataBuff[Location+30:Location+32])[0]*0.0244140625 + 1.6   #16 - Rear optics bridge temp
    hkDat2DS.DSPT = unpack("H",dataBuff[Location+32:Location+34])[0]*0.0244140625 + 1.6   #17 - DSP board temp
    hkDat2DS.FV_T = unpack("H",dataBuff[Location+34:Location+36])[0]*0.0244140625 + 1.6   #18 - Forward vessel temp
    hkDat2DS.HL_T = unpack("H",dataBuff[Location+36:Location+38])[0]*0.0244140625 + 1.6   #19 - H laser temp
    hkDat2DS.VL_T = unpack("H",dataBuff[Location+38:Location+40])[0]*0.0244140625 + 1.6   #20 - V laser temp
    hkDat2DS.FP_T = unpack("H",dataBuff[Location+40:Location+42])[0]*0.0244140625 + 1.6   #21 - Front plate temp
    hkDat2DS.PS_T = unpack("H",dataBuff[Location+42:Location+44])[0]*0.0244140625 + 1.6   #22 - Power supply temp
    hkDat2DS.MF_V = unpack("H",dataBuff[Location+44:Location+46])[0]*0.00488400488        #23 - -5V supply (V)
    hkDat2DS.PF_V = unpack("H",dataBuff[Location+46:Location+48])[0]*0.00488400488        #24 - +5V supply (V)
    hkDat2DS.CI_P = unpack("H",dataBuff[Location+48:Location+50])[0]*0.018356 - 3.846     #25 - Can internal pressure
    hkDat2DS.H021 = unpack("H",dataBuff[Location+50:Location+52])[0]*0.00244140625        #26 - H element 21 voltage
    hkDat2DS.H042 = unpack("H",dataBuff[Location+52:Location+54])[0]*0.00244140625        #27 - H element 42 voltage
    hkDat2DS.H085 = unpack("H",dataBuff[Location+54:Location+56])[0]*0.00244140625        #28 - H element 85 voltage
    hkDat2DS.H106 = unpack("H",dataBuff[Location+56:Location+58])[0]*0.00244140625        #29 - H element 106 voltage
    hkDat2DS.V021 = unpack("H",dataBuff[Location+58:Location+60])[0]*0.00244140625        #30 - V element 21 voltage
    hkDat2DS.V042 = unpack("H",dataBuff[Location+60:Location+62])[0]*0.00244140625        #31 - V element 42 voltage
    hkDat2DS.V085 = unpack("H",dataBuff[Location+62:Location+64])[0]*0.00244140625        #32 - V element 85 voltage
    hkDat2DS.V106 = unpack("H",dataBuff[Location+64:Location+66])[0]*0.00244140625        #33 - V element 106 voltage
    hkDat2DS.Vnum = unpack("H",dataBuff[Location+66:Location+68])[0]                      #34 - H particles detected (#)
    hkDat2DS.Hnum = unpack("H",dataBuff[Location+68:Location+70])[0]                      #35 - V particles detected (#)
    hkDat2DS.HTbm = unpack("H",dataBuff[Location+70:Location+72])[0]                      #36 - Active heater zones bool array
    hkDat2DS.HLDV = unpack("H",dataBuff[Location+72:Location+74])[0]*0.001220703          #37 - H laser drive (V)
    hkDat2DS.VLDV = unpack("H",dataBuff[Location+74:Location+76])[0]*0.001220703          #38 - V laser drive (V)
    hkDat2DS.H_MB = unpack("H",dataBuff[Location+76:Location+78])[0]                      #39 - H masked bits (#)
    hkDat2DS.V_MB = unpack("H",dataBuff[Location+78:Location+80])[0]                      #40 - V masked bits (#)
    hkDat2DS.Snum = unpack("H",dataBuff[Location+80:Location+82])[0]                      #41 - Stereo particles found (#)
    hkDat2DS.nTWM = unpack("H",dataBuff[Location+82:Location+84])[0]                      #42 - Timing word mismatches (#)
    hkDat2DS.nSCM = unpack("H",dataBuff[Location+84:Location+86])[0]                      #43 - Slice count mismatches (#)
    hkDat2DS.nHOP = unpack("H",dataBuff[Location+86:Location+88])[0]                      #44 - H overload periods (#)
    hkDat2DS.nVOP = unpack("H",dataBuff[Location+88:Location+90])[0]                      #45 - V overload periods (#)
    hkDat2DS.CCbm = unpack("H",dataBuff[Location+90:Location+92])[0]                      #46 - Compression configuration bool array
    hkDat2DS.nEFF = unpack("H",dataBuff[Location+92:Location+94])[0]                      #47 - Empty FIFO faults (#)
    hkDat2DS.SPRa = unpack("H",dataBuff[Location+94:Location+96])[0]                      #48 - Spare a
    hkDat2DS.SPRb = unpack("H",dataBuff[Location+96:Location+98])[0]                      #49 - Spare b
    hkDat2DS.TASw = unpack("f",dataBuff[Location+100:Location+102]+dataBuff[Location+98:Location+100])[0]       #50+51 - TAS
    hkDat2DS.TMwr = unpack("I",dataBuff[Location+104:Location+106]+dataBuff[Location+102:Location+104])[0]      #52+53 - Timing word
    Location += 104
    writeHKFile = True
    if writeHKFile:
        for entry in hkDat2DS:
            print entry
    return hkDat2DS, Location, findType

# Exception to deal with (alleged) stereo particle events
class GetOutOfLoop(Exception):
     pass

# Method of getting tick counter start time from current data file name
def getStartTimeFromFileName(fileName):
# HINT: Time_NewS=(Header[4]*3600)+(Header[5]*60)+(Header[6]) in IGOR software - is there a header?
    fn = os.path.split(fileName)
    fileName = fn[1]
    year=fileName[4:6]
    month=fileName[6:8]
    day=fileName[8:10]
    hour=fileName[10:12]
    minute=fileName[12:14]
    second=fileName[14:16]
#    print fileName, year, month, day, hour, minute, second
    fileStartTobj = datetime.datetime(2000+int(year),int(month),int(day),int(hour),int(minute),int(second))
    fileStartTime = time.mktime(fileStartTobj.timetuple())
    return fileStartTime

# Add difference in this and previous timeWord to current time
def updateCurrentTime(time2DS, channel):
# Update the shift register components of the time structure
    if channel == "H":
        time2DS.prevTimeStampValueH = time2DS.currentTime
    elif channel == "V":
        time2DS.prevTimeStampValueV = time2DS.currentTime
    elif channel == "HK":
        pass
    else:
        print "Warning: Channel can't happen error"
    time2DS.prevTimeStampValueH = time2DS.currentTime
    countInterval = time2DS.probeResolution / time2DS.TAS # in seconds
    if time2DS.oldTimeWord < 0:
        time2DS.oldTimeWord = time2DS.timeWord
    if time2DS.timeWord == 0 and time2DS.oldTime < (2^32) * countInterval - 1.5:
        print "Warning: Tick count of zero encountered in updateCurrentTime() - aborting time update might cause a timing offest from here"
        raise GetOutOfLoop
    if time2DS.timeWord  > time2DS.oldTimeWord:
        time2DS.currentTime = time2DS.oldTime + (time2DS.timeWord - time2DS.oldTimeWord) * countInterval
    elif time2DS.timeWord < time2DS.oldTimeWord:
        time2DS.currentTime = time2DS.oldTime + ((((2^32) - 1) - time2DS.oldTimeWord) + time2DS.timeWord) * countInterval
    elif time2DS.timeWord == time2DS.oldTimeWord:
        time2DS.currentTime = time2DS.oldTime
    else:
        print "Warning: Possible non-numeric tick count in updateCurrentTime() - aborting time update might cause a timing offest from here"
        raise GetOutOfLoop
    time2DS.oldTimeWord = time2DS.timeWord
    time2DS.PrevTimeStampValue = time2DS.oldTime
    time2DS.oldTime = time2DS.currentTime


def set2DSBkg(workArray, imageDims, bkgColor):
    '''Set up frames and title in 2DS display page'''
    workArray[:,:,] = bkgColor
    for i in xrange(0,imageDims.numStrips+1):
        workArray[imageDims.topPixLoc:imageDims.bottomPixLoc, imageDims.leftPixLoc + i * (imageDims.stripWidth + 1),] = (0,0,0)
    workArray[imageDims.topPixLoc, imageDims.leftPixLoc:imageDims.rightPixLoc,] = (0,0,0)
    workArray[imageDims.bottomPixLoc, imageDims.leftPixLoc:imageDims.rightPixLoc,] = (0,0,0)

def add2DSImage(imArray, dispArray, numSlices, actCol, actSlice, time2DS, channel, imageDims, targetFileName, stampContent, stampLoc):
    '''If this particle fits in the current image strip then put it there'''
    if actSlice + numSlices <= imageDims.bottomPixLoc:
# The following statement only triggers on the first particle in the batch, and prevents a start date of January 1st 1970
        if actCol == 0 and actSlice == imageDims.topPixLoc + 1:
            if channel == "H":
                time2DS.imageStartTimeH = time2DS.currentTime
                stampContent.Hstamp.append(time.strftime("%H:%M:%S", time.localtime(time2DS.currentTime)) + ":" + str(int((time2DS.currentTime % 1) * 1000)))
            elif channel == "V":
                time2DS.imageStartTimeV = time2DS.currentTime
                stampContent.Vstamp.append(time.strftime("%H:%M:%S", time.localtime(time2DS.currentTime)) + ":" + str(int((time2DS.currentTime % 1) * 1000)))
            else:
                print "Warning: Channel can't happen error"
        dispArray[actSlice : actSlice + numSlices, imageDims.leftPixLoc + 1 + actCol * (imageDims.stripWidth + 1) : (imageDims.leftPixLoc + imageDims.stripWidth + 1) + actCol * (imageDims.stripWidth + 1), :] = imArray[0 : numSlices, 0 : imageDims.stripWidth]
        actSlice += numSlices
        imArray[0:1280, 0:128, 0:3] = 255
        return actSlice, actCol
# If this particle is too big to fit on the current strip but there are more strips available on this page, start a new strip
    elif actCol < (imageDims.numStrips - 1):
        actCol += 1
        actSlice = imageDims.topPixLoc + 1
#        print "IMDIMS: ", numSlices, imageDims.stripWidth
        dispArray[actSlice : actSlice + numSlices, imageDims.leftPixLoc + 1 + actCol * (imageDims.stripWidth + 1) : (imageDims.leftPixLoc + imageDims.stripWidth + 1) + actCol * (imageDims.stripWidth + 1), :] = imArray[0 : numSlices, 0 : imageDims.stripWidth]
        actSlice += numSlices
        imArray[0:1280, 0:128, 0:3] = 255
        if channel == "H":
            stampContent.Hstamp.append(time.strftime("%H:%M:%S", time.localtime(time2DS.prevTimeStampValueH)) + ":" + str(int((time2DS.prevTimeStampValueH % 1) * 1000)))
            stampContent.Hstamp.append(time.strftime("%H:%M:%S", time.localtime(time2DS.currentTime)) + ":" + str(int((time2DS.oldTime % 1) * 1000)))
        elif channel == "V":
            stampContent.Vstamp.append(time.strftime("%H:%M:%S", time.localtime(time2DS.oldTime)) + ":" + str(int((time2DS.oldTime % 1) * 1000)))
            stampContent.Vstamp.append(time.strftime("%H:%M:%S", time.localtime(time2DS.prevTimeStampValueV)) + ":" + str(int((time2DS.prevTimeStampValueV % 1) * 1000)))
        return actSlice, actCol
    else:
# Save the (filled) output image to file
        if channel == "H":
            stampContent.Hstamp.append(time.strftime("%H:%M:%S", time.localtime(time2DS.currentTime)) + ":" + str(int((time2DS.currentTime % 1) * 1000)))
            plot2DSImage(dispArray, time2DS, time2DS.imageStartTimeH, targetFileName, channel, imageDims, stampContent, stampLoc)
            stampContent.Hstamp = []
        if channel == "V":
            stampContent.Vstamp.append(time.strftime("%H:%M:%S", time.localtime(time2DS.currentTime)) + ":" + str(int((time2DS.currentTime % 1) * 1000)))
            plot2DSImage(dispArray, time2DS, time2DS.imageStartTimeV, targetFileName, channel, imageDims, stampContent, stampLoc)
            stampContent.Vstamp = []
# Blank the output page and rebuild the image strip outlines
        set2DSBkg(dispArray, imageDims, 255)
# Reset current draw position to start of fresh page
        actCol = 0
        actSlice = imageDims.topPixLoc + 1
# Set the start time for the new image output page
        if channel == "H":
            stampContent.Hstamp.append(time.strftime("%H:%M:%S", time.localtime(time2DS.currentTime)) + ":" + str(int((time2DS.currentTime % 1) * 1000)))
            time2DS.imageStartTimeH = time2DS.currentTime
        elif channel == "V":
            stampContent.Vstamp.append(time.strftime("%H:%M:%S", time.localtime(time2DS.currentTime)) + ":" + str(int((time2DS.currentTime % 1) * 1000)))
            time2DS.imageStartTimeV = time2DS.currentTime
        else:
            print "Warning: Channel can't happen error"
# Draw the first particle into the output page            
        dispArray[actSlice : actSlice + numSlices, imageDims.leftPixLoc + 1 + actCol * (imageDims.stripWidth + 1) : (imageDims.leftPixLoc + imageDims.stripWidth + 1) + actCol * (imageDims.stripWidth + 1), :] = imArray[0 : numSlices, 0 : imageDims.stripWidth]
        actSlice += numSlices
        imArray[0:1280, 0:128, 0:3] = 255
        return actSlice, actCol

def plot2DSImage(dispArray, time2DS, imageStartTime, targetFileName, channel, imageDims, stampContent, stampLoc):
    if channel == "H":
        channelName = "HORIZONTAL"
    if channel == "V":
        channelName = "VERTICAL"
    im=Image.Image()
    im=Image.fromarray(dispArray)
    drawText(im,"2DS DATA - " + channelName + " - time range " + time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(imageStartTime)) + ":" + str(int((imageStartTime % 1) * 1000)) + " to " + time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(time2DS.currentTime)) + ":" + str(int((time2DS.currentTime % 1) * 1000)), 40, 20, 24)
    drawText(im,"RAW FILE: "+targetFileName, 40, 45, 24)
    drawText(im,"Extracted using py2DS - "+u"\u00A9"+" James Dorsey - University of Manchester - 2013", 1350, 25, 10)
    draw = ImageDraw.Draw(im)
    draw.line((1350, 50, 1375, 50), fill=0, width = 2)
    drawText(im,"25 "+u"\u03BC"+"m scale line", 1380, 43, 10)
    for i in xrange (0,(2*(imageDims.numStrips))):
        if channel == "H":
            drawText(im,stampContent.Hstamp[i], stampLoc[i,0], stampLoc[i,1], 12)
        else:
            drawText(im,stampContent.Vstamp[i], stampLoc[i,0], stampLoc[i,1], 12)
    del draw
    imFileName = str("{0}{1:03.0f}-{2}{3:03.0f}-{4}.png".format(time.strftime("%Y%m%d%H%M%S", time.localtime(imageStartTime)), (imageStartTime % 1.0) * 1e3, time.strftime("%Y%m%d%H%M%S", time.localtime(time2DS.currentTime)), (time2DS.currentTime % 1.0) * 1e3, channel))
    imFileName = "output/" + imFileName.replace(":", "")
    im.save(imFileName)
    print "Output: Writing image file ", imFileName

# Direct copy of the function in pyCPI - move this to a common file
def drawText(img, textString, xLoc, yLoc, fontSize):
    font = ImageFont.truetype("/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf",fontSize)
    draw = ImageDraw.Draw(img)
    draw.text((xLoc, yLoc),textString,(0,0,0),font=font)
    draw = ImageDraw.Draw(img)
    draw = ImageDraw.Draw(img)

class houseRecord2DS(object):
    '''ITERABLE data structure to receive 2DS housekeeping data'''
    def __init__(self):
        self.H000 = 63905 #02 - H element 0 voltage
        self.H064 = 63905 #03 - H element 64 voltage
        self.H127 = 63905 #04 - H element 127 voltage
        self.V000 = 63905 #05 - V element 0 voltage
        self.V064 = 63905 #06 - V element 64 voltage
        self.V127 = 63905 #07 - V element 127 voltage
        self.PS_V = 63905 #08 - Positive supply voltage
        self.NS_V = 63905 #09 - Negative supply voltage
        self.HTAT = 63905 #10 - H transmit arm temp
        self.HRAT = 63905 #11 - H receive arm temp
        self.VTAT = 63905 #12 - V transmit arm temp
        self.VRAT = 63905 #13 - V receive arm temp
        self.HTTT = 63905 #14 - H transmit tip temp
        self.HRTT = 63905 #15 - H receive tip temp
        self.ROBT = 63905 #16 - Rear optics bridge temp
        self.DSPT = 63905 #17 - DSP board temp
        self.FV_T = 63905 #18 - Forward vessel temp
        self.HL_T = 63905 #19 - H laser temp
        self.VL_T = 63905 #20 - V laser temp
        self.FP_T = 63905 #21 - Front plate temp
        self.PS_T = 63905 #22 - Power supply temp
        self.MF_V = 63905 #23 - -5V supply (V)
        self.PF_V = 63905 #24 - +5V supply (V)
        self.CI_P = 63905 #25 - Can internal pressure
        self.H021 = 63905 #26 - H element 21 voltage
        self.H042 = 63905 #27 - H element 42 voltage
        self.H085 = 63905 #28 - H element 85 voltage
        self.H106 = 63905 #29 - H element 106 voltage
        self.V021 = 63905 #30 - V element 21 voltage
        self.V042 = 63905 #31 - V element 42 voltage
        self.V085 = 63905 #32 - V element 85 voltage
        self.V106 = 63905 #33 - V element 106 voltage
        self.Vnum = 63905 #34 - H particles detected (#)
        self.Hnum = 63905 #35 - V particles detected (#)
        self.HTbm = 63905 #36 - Active heater zones bool array
        self.HLDV = 63905 #37 - H laser drive (V)
        self.VLDV = 63905 #38 - V laser drive (V)
        self.H_MB = 63905 #39 - H masked bits (#)
        self.V_MB = 63905 #40 - V masked bits (#)
        self.Snum = 63905 #41 - Stereo particles found (#)
        self.nTWM = 63905 #42 - Timing word mismatches (#)
        self.nSCM = 63905 #43 - Slice count mismatches (#)
        self.nHOP = 63905 #44 - H overload periods (#)
        self.nVOP = 63905 #45 - V overload periods (#)
        self.CCbm = 63905 #46 - Compression configuration bool array
        self.nEFF = 63905 #47 - Empty FIFO faults (#)
        self.SPRa = 63905 #48 - Spare a
        self.SPRb = 63905 #49 - Spare b
        self.TASw = 63905 #50+51 - TAS
        self.TMwr = 63905 #52+53 - Timing word

    def __iter__(self):
        for each in self.__dict__.keys():
            yield self.__getattribute__(each)

# Empty data container for single particle data - ACHTUNG - allocated at runtime
class particleRecord2DS:
    pass

class timeStruct2DS:
    currentTime = 0.0
    oldTime = 0.0
    timeWord = 0
    oldTimeWord = -1
    probeResolution = 0
    TAS = 0
    prevTimeStampValueH = 0
    prevTimeStampValueV = 0
    imageStartTimeH = 0
    imageStartTimeV = 0
    buffSize = 0

class outputGeometry:
    topPixLoc = 95
    bottomPixLoc = 1220
    leftPixLoc = 39
    rightPixLoc = 1716
    stripWidth = 128
    numStrips = 13

class imageTimeStamps:
    Hstamp = []
    Vstamp = []
