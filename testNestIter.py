imList = [("Img", "21", 102368454, 1),("ROI", 102368558, 1892),("Img", "21", 102370592, 4),("ROI", 102370696, 2670),("ROI", 102373540, 4403),("ROI", 102378154, 1920),("ROI", 102380217, 1845),("Img", "21", 102382203, 0),("Img", "21", 102382307, 1),("ROI", 102382411, 2900),("Img", "21", 102385474, 1),("ROI", 102385578, 2754),("Img", "21", 102388492, 1),("ROI", 102388596, 2640),("Img", "21", 102391394, 1),("ROI", 102391498, 2116),("Img", "21", 102393761, 2),("ROI", 102393865, 2592),("ROI", 102396614, 3536),("Img", "21", 102400325, 1),("ROI", 102400429, 2162)]

for item in imList:
    if item[0] == "Img":
        print "ReadCPIImage ", item[2]
        for item in xrange(item[3]):
            print "ReadCPIROI ", item
