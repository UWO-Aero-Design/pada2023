from math import sin, cos, sqrt, atan2, radians, degrees

import cv2
from scipy.spatial.transform import Rotation as R
from geographiclib.geodesic import Geodesic

from TargetDetect import TargetDetect

def clamp_zero(x):
    if x > -0.001 and x < 0.001:
        return 0
    return x

if __name__ == "__main__":
    FOCAL_LENGTH_MM = 24
    TEXT_SCALE = 1.5
    TEXT_COLOUR = (255,255,255)
    TEXT_THICKNESS = 3
    att = { "altitude": 15.6,  "lat": 42.9792118, "lon": -81.1439136, 'yaw': 10.334, 'pitch': 1*0, 'roll': -4.4*0 }
    
    detect = TargetDetect()

    frame = cv2.imread('../data/DJI_0154.jpg')
    detect.detect(frame)
    height, width = frame.shape[:2]
    cp = (int(width/2), int(height/2))

    geod = Geodesic.WGS84
    g = geod.Direct(0, 0, 0, 0.25)
    thresh = g['lat2']
    zones = []

    centroids, _ = detect.detect(frame)
    
    print(f"Found {len(centroids)}: {centroids}")

    # camera: x=width, y=height, z=into the page
    # drone: x=out of nose, y=right wing, z=out of belly
    # [1,0,0] -> [0,1,0]
    # [0,1,0] -> [0,-0.7,0.7]
    # [0,0,1] -> [0.7,0,0.7]
    CAMERA_PITCH_DEG = 0
    camera_to_drone = R.from_euler('xyz', [0, 0, 90], degrees=True)
    drone_to_world = R.from_euler('xyz', [att['yaw'], att['pitch'], att['roll']], degrees=True)

    cv2.putText(frame, f"Lat  : {att['lat']}", (50, 40), cv2.FONT_HERSHEY_SIMPLEX, TEXT_SCALE, TEXT_COLOUR, TEXT_THICKNESS, cv2.LINE_AA) 
    cv2.putText(frame, f"Lon  : {att['lon']}", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, TEXT_SCALE, TEXT_COLOUR, TEXT_THICKNESS, cv2.LINE_AA)
    cv2.putText(frame, f"Alt  : {att['altitude']}", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, TEXT_SCALE, TEXT_COLOUR, TEXT_THICKNESS, cv2.LINE_AA) 
    cv2.putText(frame, f"Yaw  : {att['yaw']}", (50, 160), cv2.FONT_HERSHEY_SIMPLEX, TEXT_SCALE, TEXT_COLOUR, TEXT_THICKNESS, cv2.LINE_AA)
    cv2.putText(frame, f"Pitch: {att['yaw']}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, TEXT_SCALE, TEXT_COLOUR, TEXT_THICKNESS, cv2.LINE_AA)
    cv2.putText(frame, f"Roll : {att['roll']}", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, TEXT_SCALE, TEXT_COLOUR, TEXT_THICKNESS, cv2.LINE_AA)

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
        distance = att['altitude']/cos(effective_elevation)

        X = distance * sin(effective_elevation) * cos(azimuth)
        Y = distance * sin(effective_elevation) * sin(azimuth)
        Z = distance * cos(effective_elevation)

        g = geod.Direct(att['lon'], att['lat'], 0, X)
        g = geod.Direct(g['lon2'], g['lat2'], 90, -Y)
        lon = g['lon2']
        lat = g['lat2']

        new = True
        for zone in zones:
            if(abs(zone['lat']-lat) < thresh and abs(zone['lon']-lon) < thresh):
                zone["count"] = zone["count"]+1
                new = False
        if not new:
            zones.append({ 'lat': lat, 'lon': lon, 'count': 1 })
            print(f"New target at {lat},{lon}")

        start = ( int(c['x']-c['w']/2), int(c['y']-c['h']/2) )
        end   = ( int(c['x']+c['w']/2), int(c['y']+c['h']/2) )
        cv2.rectangle(frame, start, end, (36,255,12), 4)
        desc_str = f"X: {c['x']}, Y: {c['y']} Az: {round(degrees(azimuth),2)} El: {round(degrees(elevation),2)} D: {round(distance,2)}, Lat: {round(lat, 7)}, Lon: {round(lon, 7)}"
        cv2.putText(frame, desc_str, (c['x']-700, c['y']-100), cv2.FONT_HERSHEY_SIMPLEX, TEXT_SCALE, TEXT_COLOUR, TEXT_THICKNESS, cv2.LINE_AA)

    WINDOW_NAME = 'Detection'
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.imshow(WINDOW_NAME, frame)
    key = cv2.waitKey(0)
    cv2.destroyAllWindows() 