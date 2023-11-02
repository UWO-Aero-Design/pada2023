#!/usr/bin/python3

import queue
import argparse
from math import sin, cos, tan, pi, sqrt, atan2, radians, degrees

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

def clamp_zero(x):
    if x > -0.001 and x < 0.001:
        return 0
    return x

def main():

    args = parse_args()

    WINDOW_NAME = 'Tracking'
    FOCAL_LENGTH_MM = 24
    CAMERA_PITCH_DEG = -45 # negative is pitch down
    TARGET_THRESH_M = 4

    att = None

    try:
        tlm = Telemetry(args.MAV)
        video = Video(args.STREAM)
    except Exception as err:
        print(err)
        exit(0)

    detect = TargetDetect()
    cp = video.get_centre_point()
    camera_to_drone = R.from_euler('xyz', [-1*CAMERA_PITCH_DEG, 0, 90], degrees=True)

    geod = Geodesic.WGS84
    g = geod.Direct(0, 0, 0, TARGET_THRESH_M)
    thresh = g['lat2']
    zones = []

    while True:
        try:
            att = tlm.telemetry.get(block=False)
        except queue.Empty:
            pass

        try:
            frame = video.frames.get(block=False)

            centroids, _ = detect.detect(frame)

            if att:
                drone_to_world = R.from_euler('xyz', [att.hdg*0, 0, 0], degrees=True)
                for c in centroids:
                    # clamp -0.0 (idk why atan2 treats it differently)
                    Xc = clamp_zero((c['x']-cp[0])/(FOCAL_LENGTH_MM))
                    Yc = clamp_zero((c['y']-cp[1])/(FOCAL_LENGTH_MM))
                    Zc = 1
                    Pc = [Xc, Yc, Zc]

                    Pd = camera_to_drone.apply(Pc)
                    Pd = [clamp_zero(x) for x in Pd]
                    
                    Pw = drone_to_world.apply(Pd)
                    Pw = [clamp_zero(x) for x in Pw]

                    azimuth = atan2(Pw[1], Pw[0])
                    elevation = atan2(-Pw[2], sqrt(Pw[0]**2 + Pw[1]**2))
                    effective_elevation = elevation-radians(CAMERA_PITCH_DEG)
                    distance = att.alt/cos(effective_elevation)

                    shift = geod.Direct(0, 0, degrees(azimuth), distance)
                    lon = att.lon/1E7 + shift['lon2']
                    lat = att.lat/1E7 + shift['lat2']

                    new = True
                    for zone in zones:
                        if(abs(zone['lat']-lat) < thresh and abs(zone['lon']-lon) < thresh):
                            zone["count"] = zone["count"]+1
                            new = False
                    if new:
                        zones.append({ 'lat': lat, 'lon': lon, 'count': 1 })
                        print(f"New target at {lat},{lon}")

                    start = ( int(c['x']-c['w']/2), int(c['y']-c['h']/2) )
                    end   = ( int(c['x']+c['w']/2), int(c['y']+c['h']/2) )
                    cv2.rectangle(frame, start, end, (36,255,12), 4)
                    desc_str = f"X: {c['x']}, Y: {c['y']} Az: {round(degrees(azimuth),2)} El: {round(degrees(elevation),2)} D: {round(distance,2)}, Lat: {round(lat, 7)}, Lon: {round(lon, 7)}"
                    cv2.putText(frame, desc_str, (c['x']-300, c['y']-30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2, cv2.LINE_AA)

            if att:    
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