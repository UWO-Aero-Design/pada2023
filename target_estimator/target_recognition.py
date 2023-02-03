import cv2
import numpy as np

limits = [(np.array([0, 72, 64]), np.array([13, 227, 255]))]

cap = cv2.VideoCapture(0)


def checkCapture():
    if not cap.isOpened():
        print("can't open")

def capLoop():
    ret, frame = cap.read()
    if not ret:
        print("bad stream")
        exit()

    return frame

if __name__ == "__main__":


    while True:
        frame = capLoop()
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        for limit in limits:

            mask = cv2.inRange(hsv, limit[0], limit[1])
            res = cv2.bitwise_and(frame, frame, mask=mask)

        blur_mask = cv2.GaussianBlur(mask,(15,15),0)
        ret, thresh = cv2.threshold(blur_mask,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        d = 100
        for cntr in contours:
            x,y,w,h = cv2.boundingRect(cntr)
            cv2.rectangle(res, (x, y), (x+w, y+h), (0, 0, 255), 2)
            dw = 330 / w
            dh = 330 / h
            dt = dw
            if dh > dw:
                dt = dh
            if dt < d:
                d = dt
        print("distance:" + str(d)) 

        cv2.imshow('frame',frame)
        cv2.imshow('mask',mask)
        cv2.imshow('res',res)

        cv2.imshow('threshold', thresh)

        if(cv2.waitKey(1) == ord('q')):
            break
        