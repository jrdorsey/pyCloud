from __future__ import print_function

def checkImLocList(imList, hkList, roiList, pdsList):
# Some execution control stuff
    pedantic = False
    printLocList = False
    makeMergedList = True
# Some initialisation
    if makeMergedList: mergedImList = []
    byteNumber = 0
# Some code
    if False: print("IMG", len(imList), "HK", len(hkList), "ROI:", len(roiList), "PDS:", len(pdsList))
# Loop over all image frames
    for imFrame in imList:
        (blockType, blockVersion, Location, nROI) = imFrame
# Check this image is later in the file than the last data frame
        if byteNumber < Location:
            byteNumber = Location
# If it isn't, do something about it
        else:
            print("Image frame sequencing error")
            if pedantic: return []
        if printLocList: print(nROI, imFrame)
# Add this image to the merged list if it seems to be in the right place and the list is requested
        if makeMergedList: mergedImList.append(imFrame)
# Loop through the number of ROI frames referred to in the image frame header
        for roi in xrange(nROI):
            roiItem = roiList.pop(0)
# Check this ROI is later in the file than the last data frame
            if byteNumber < roiItem[1]:
                byteNumber = roiItem[1]
# If it isn't, do something about it
            else:
                print("ROI frame sequencing eerror")
                if pedantic: return[]
            if printLocList: print(roiItem)
# Add this ROI to the merged list if it seems to be in the right place and the list is requested
            if makeMergedList: mergedImList.append(roiItem)
# Check there are no ROIs left waiting in the queue
    if len(roiList)>0:
# If there are, do something about it
        print("Warning - ", len(roiList), " left over ROI frames in buffer - data file is corrupted")
        if pedantic: return []
# If there aren't, return the merged list if requested, or an empty list if not
    if makeMergedList:
        return mergedImList
    else:
        return []
