import cv2
import numpy as np

limit = [(np.array([300, 50, 50]), np.array([360, 255, 255]))]

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

def varChange(clr, pos, val):
    def change(v):
        limit[clr][pos][val] = v
    return change

trackbar = True

if __name__ == "__main__":


    while True:
        frame = capLoop()
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, limit[0][0], limit[0][1])

        res = cv2.bitwise_and(frame, frame, mask=mask)
        cv2.imshow('frame',frame)
        cv2.imshow('mask',mask)
        cv2.imshow('res',res)
        if trackbar:
            cv2.createTrackbar('h1', 'res', 1, 180, varChange(0,0,0))
            cv2.createTrackbar('s1', 'res', 1, 255, varChange(0,0,1))
            cv2.createTrackbar('v1', 'res', 1, 255, varChange(0,0,2))
            cv2.createTrackbar('h2', 'res', 1, 180, varChange(0,1,0))
            cv2.createTrackbar('s2', 'res', 1, 255, varChange(0,1,1))
            cv2.createTrackbar('v2', 'res', 1, 255, varChange(0,1,2))
            trackbar = False

        if(cv2.waitKey(1) == ord('q')):
            break
        