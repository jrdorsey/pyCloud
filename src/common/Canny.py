import math
import copy
from PIL import Image
import collections
import cv2
import qhull_2d
import min_bounding_rect
from PIL import ImageDraw as imdr
import numpy as np
from numpy import ones
from numpy import column_stack as colstack
from matplotlib import pyplot as plt
from scipy import ndimage
from skimage import filters

def CannyEdge(workArray, dX, dY, sigma, lowThresh, highThresh, currentCPIBackGround, stX, stY):
# These flags control edge detection execution. Beware - they're not all independent.
# e.g. You can do plotSingleParticles without doing a doFloodFill, and you can't
# doPrintBoundingBox without a doBoundingBox. Also you can't doCCA without doClosing.
    doBckgndThreshold = 0
    useCV2 = 0
    doClosing = 0
    doCCA = 0
    doFloodFill = 1
    plotSingleParticles = 0
    minPlotSize = 10
    doBoundingBox = 1
    doPrintBoundingBox = 0
    
    floodArea = 0
    
    im = workArray[0:dY,0:dX,0]
    img = workArray[0:dY,0:dX,:]
    composite = copy.deepcopy(im)
    binObj = copy.deepcopy(im)
    xMaxLoc,yMaxLoc = np.unravel_index(im.argmax(), im.shape)
    xMinLoc,yMinLoc = np.unravel_index(im.argmin(), im.shape)
#    exposure.equalize(im)
    lt = lowThresh * (im.max() - im.min())
    ht = highThresh * (im.max() - im.min())
    
    if doBckgndThreshold:
        pass
        
# Compute the Canny filter for two values of sigma
    if useCV2:
        xCV, yCV = im.shape
        imCV = im.copy()
        edges = im.copy()
        edges[:,:] = 0
        imCV = cv2.GaussianBlur(img,(0,0),sigma)
# cv2.bilateralFilter(src, d, sigmaColor, sigmaSpace)
#        imCV = cv2.bilateralFilter(img, 0, 3, 5)
        cv2.Canny(imCV,lt,ht,edges)
        contours, heirarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        plt.figure(figsize=(8, 3))

        plt.subplot(131)
        plt.imshow(im, cmap=plt.cm.gray) # Was im
        plt.axis('off')
        plt.title('Data', fontsize=20)

        plt.subplot(132)
        plt.imshow(imCV, cmap=plt.cm.gray)
        plt.axis('off')
        plt.title('Outline', fontsize=20)

        plt.subplot(133)
        plt.imshow(edges, cmap=plt.cm.gray)
        plt.axis('off')
        plt.title('Binary', fontsize=20)

        plt.subplots_adjust(wspace=0.02, hspace=0.02, top=0.9,bottom=0.02, left=0.02, right=0.98)

        plt.show()
        print "CLEN: ", len(contours)
        if len(contours) == 1:
            contours = np.asarray(contours)
            print type(contours), contours.shape
            box = cv2.minAreaRect(contours)
            print box
        else:
            print "More than one border identified - abort image"
    else:
# edges = filter.canny(im,3,5,30) Seems to be a reliable default for CPI images
        edges = filter.canny(im, sigma, lt, ht)
    if doClosing:
        closingStruct = ones((4,4),'uint8')
        edges = ndimage.binary_closing(edges,closingStruct)
    lowNum = im.min()
    highNum = im.max()
    if doCCA:
        ConnectedComponentAnalysis(edges)
    if doFloodFill:
        binObj = copy.deepcopy(edges)
        floodFill(xMinLoc, yMinLoc, 1, binObj)
        floodArea = sum(sum(binObj))
# display results
    if plotSingleParticles and doFloodFill:
        if (im.shape[0] > minPlotSize or im.shape[1] > minPlotSize):
            
            composite[edges] = im.max()
            
            plt.figure(figsize=(8, 3))

            plt.subplot(131)
            plt.imshow(im, cmap=plt.cm.gray) # Was im
            plt.axis('off')
            plt.title('Data', fontsize=20)

            plt.subplot(132)
            plt.imshow(composite, cmap=plt.cm.gray)
            plt.axis('off')
            plt.title('Outline', fontsize=20)

            plt.subplot(133)
            plt.imshow(binObj, cmap=plt.cm.gray)
            plt.axis('off')
            plt.title('Binary', fontsize=20)

            plt.subplots_adjust(wspace=0.02, hspace=0.02, top=0.9,bottom=0.02, left=0.02, right=0.98)

            plt.show()
    if doBoundingBox:
        edgeXLoc, edgeYLoc = np.where(edges==1)
        edgeLoc = colstack((edgeYLoc, edgeXLoc))
        hull_points = qhull_2d.qhull2D(edgeLoc)
        (rot_angle, area, width, height, centre_point, corner_points) = min_bounding_rect.minBoundingRect(hull_points)
        box_retvals = {'theta': rot_angle, 'width': width, 'height': height, 'area': width*height, 'centre': centre_point, 'corners': corner_points}
#        box_retvals = (rot_angle, area, width, height, centre_point, corner_points)
        if doPrintBoundingBox:
#            print 'Convex hull points: \n', hull_points, "\n"
            print "\n Start minimum area bounding box:"
            print "Rotation angle:", rot_angle, "rad (", rot_angle*(180/math.pi), "deg )"
            print "Width:", width, " Height:", height, " Area:", area
            print "Centre point: \n", centre_point
            print "Corner points: \n", corner_points
        return edges, box_retvals, floodArea
    return edges, (0, 0, 0, 0, 0, 0)

def ConnectedComponentAnalysis(image):
    s = [[1,1,1],[1,1,1],[1,1,1]]
    entities, number_of_entities = ndimage.label(image, structure = s)
    if (number_of_entities > 1):
        print '# distinct entities:', number_of_entities
    if doShowEachEntity:
        plt.imshow(entities)
        plt.show()

def floodFill(x, y, newColour, image):
    xLim, yLim = image.shape
    toFill = set()
    toFill.add((x,y))
    image[x][y] = newColour
    while len(toFill) > 0:
        x,y = toFill.pop()
        if image[x][y] != newColour:
            image[x][y] = newColour
        if x > 0 and image[x-1][y] != newColour:
            toFill.add((x-1,y))
        if x < xLim - 1 and image[x+1][y] != newColour:
            toFill.add((x+1,y))
        if y > 0 and image[x][y-1] != newColour:
            toFill.add((x,y-1))
        if y < yLim - 1 and image[x][y+1] != newColour:
            toFill.add((x,y+1))
