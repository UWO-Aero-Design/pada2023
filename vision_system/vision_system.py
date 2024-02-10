#!/usr/bin/python3

import queue
import argparse

import cv2
import numpy as np
from scipy.spatial.transform import Rotation as R
from geographiclib.geodesic import Geodesic

from Telemetry import Telemetry
from Video import Video
from TargetDetect import TargetDetect

def parse_args():
    parser = argparse.ArgumentParser(description="Analyze PADA video and telemetry to attempt lamding at markers")
    parser.add_argument('MAV', type=str, help="The connection URL to connect to for mavlink messages (eg. udpin:127.0.0.1:5001)")
    parser.add_argument('STREAM', type=str, help="The connection URL to use for the RTMP stream (eg. rtmp://localhost:1935/live/test)")

    args = parser.parse_args()

    return args

def placeBoundingBox(frame, x, y, w, h, colour=(255,255,255), thickness=4):
        start = ( int(x-w/2), int(y-h/2) )
        end   = ( int(x+w/2), int(y+h/2) )
        cv2.rectangle(frame, start, end, colour, thickness)

def main():

    args = parse_args()
    GLOBAL_POSITION_INT = 'GLOBAL_POSITION_INT'
    ATTITUDE = 'ATTITUDE'

    WINDOW_NAME = 'Tracking'
    att = None
    messages = [GLOBAL_POSITION_INT, ATTITUDE]

    try:
        # tlm = Telemetry(args.MAV, messages, conn_print=True, debug_print=True)
        video = Video(args.STREAM, debug_print=True)
        detect = TargetDetect()
    except Exception as err:
        print(err)
        exit(0)

    # width and height of image stream
    res = video.get_resolution()

    while True:
        # msgs = tlm.get_msgs()
        # pos = msgs[GLOBAL_POSITION_INT]
        # att = msgs[ATTITUDE]

        frame = video.get_frame()

        if(frame is None):
            print("Video stream complete")
            break

        centroids = detect.detect(frame)
        for c in centroids:
            start = ( int(c['x']-c['w']/2), int(c['y']-c['h']/2) )
            end   = ( int(c['x']+c['w']/2), int(c['y']+c['h']/2) )
            cv2.rectangle(frame, start, end, (36,255,12), 4)
            cv2.putText(frame, c["color"], start, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
            
        # if pos and att:    
        #     # TODO: wrap this up in a function in the Video class
        #     cv2.putText(frame, f"{pos.time_boot_ms}", (50, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA) 
        #     cv2.putText(frame, f"Lat  : {pos.lat/1E7}", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA) 
        #     cv2.putText(frame, f"Lon  : {pos.lon/1E7}", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA) 
        #     cv2.putText(frame, f"Hdg  : {pos.hdg}", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.imshow(WINDOW_NAME, frame)

        key = cv2.waitKey(1)
        if key == ord('q') or key == 27 or cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1: # q, esc, or window closed
            break

    print('Closing video')
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()