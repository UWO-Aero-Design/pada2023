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
        tlm = Telemetry(args.MAV, messages, conn_print=True, debug_print=True)
        video = Video(args.STREAM, debug_print=True)
        detect = TargetDetect()
    except Exception as err:
        print(err)
        exit(0)

    # width and height of image stream
    res = video.get_resolution()

    while True:
        msgs = tlm.get_msgs()
        print(msgs)
        pos = msgs[GLOBAL_POSITION_INT]
        att = msgs[ATTITUDE]

        try:
            frame = video.get_frame()

            centroids, _ = detect.detect(frame)

            if att:

                vec_alt = att.alt
                vec_lat = att.lat/1E7
                vec_lon = att.lon/1E7
                vec_hdg = 0
                vec_pitch = 0
                vec_roll = 0
                for c in centroids:
                    target_coords = detect.pixels2coords(c['x'], c['y'], res[0], res[1], att.alt*1000, att.lat/1E7, att.lon/1E7, vec_hdg, vec_pitch, vec_roll)
                    lat = target_coords['lat']
                    lon = target_coords['lon']

                    placeBoundingBox(frame, c['x'], c['y'], c['w'], c['h'])
                    desc_str = f"X: {c['x']}, Y: {c['y']} Az: {round(degrees(azimuth),2)} El: {round(degrees(elevation),2)} D: {round(distance,2)}, Lat: {round(lat, 7)}, Lon: {round(lon, 7)}"
                    cv2.putText(frame, desc_str, (c['x']-300, c['y']-30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2, cv2.LINE_AA)

            if att:    
                # TODO: wrap this up in a function in the Video class
                cv2.putText(frame, f"{att.time_boot_ms}", (50, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA) 
                cv2.putText(frame, f"Lat  : {att.lat/1E7}", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA) 
                cv2.putText(frame, f"Lon  : {att.lon/1E7}", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA) 
                cv2.putText(frame, f"Hdg  : {att.hdg}", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                cv2.putText(frame, f"Tlm  : {tlm.telemetry.qsize()}", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA) 
                cv2.putText(frame, f"Frame: {video.frames.qsize()}", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA) 

            cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1)
            if key == ord('q') or key == 27 or cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1: # q, esc, or window closed
                break
        except queue.Empty:
            pass

    print('Closing video')
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()