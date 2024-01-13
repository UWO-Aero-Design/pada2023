import cv2
import numpy as np

class TargetDetect:
    def __init__(self):
        pass

# AA:creates the mask of the color red 
    def detect(self, frame):
        # blur to remove high frequency noise
        blurred = cv2.GaussianBlur(frame,(3,3),0)

        # convert to hsv to make it easier to mask colours
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HLS)
# AA: the 2 sets of ranges 
        # mask 1
        lower_lower_red = np.array([0,50,50])
        lower_upper_red = np.array([10,255,255])
        # mask 2
        upper_lower_red = np.array([160,50,50])
        upper_upper_red = np.array([180,255,255])
# AA: using the ranges to make a mask
        mask1 = cv2.inRange(hsv,lower_lower_red,lower_upper_red)
        mask2 = cv2.inRange(hsv, upper_lower_red,upper_upper_red)

        mask = np.bitwise_or(mask1,mask2)

        red_pixels = cv2.bitwise_and(frame,frame,mask=mask)
        gray = cv2.cvtColor(red_pixels, cv2.COLOR_BGR2GRAY) # AA: need to be gray scale
# AA:understand^
        cnts = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]

        centroids = []
        for c in cnts:
            x,y,w,h = cv2.boundingRect(c)
            A = w*h
            if(A < 400):
                continue
            M = cv2.moments(c)
            if M["m00"] == 0:
                continue
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            centre = { 'x': int(x+w/2), 'y': int(y+h/2), 'w': w, 'h': h, 'A': A }
            centroids.append(centre)

        return (centroids, { 'blurred': blurred, 'red_pixels': red_pixels, 'contours': cnts })