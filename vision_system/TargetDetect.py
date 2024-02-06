import cv2
import numpy as np
from scipy.spatial.transform import Rotation as R
from geographiclib.geodesic import Geodesic
from math import cos, sqrt, atan2, degrees
from typing import List, Tuple
class TargetDetect:
    """Detects targets in a CV2 frame

    """

    # focal length of the camera
    FOCAL_LENGTH_MM = 24

    # minimum pixel area to consider in targets
    MINUMUM_AREA_PX = 400

    def __init__(self):
        # TODO: we'll probably want to accept some parameters here rather than hardcoding things
        #       eg. the colours to use, the minimum allowable area, etc.
        
        self.colour_ranges = {
            "red": [
                [(0,50,50),(10,255,255)],
                [(345,50,50),(360,255,255)]
            ],
            "orange": [
                [(15,50,50), (45,255,255)]
            ],
            "yellow": [
                [(50,50,50), (75,255,255)]
            ],
            "blue": [
                [(180,50,50), (240, 255,255)],
            ],
            "purple": [
                [(260, 50, 50), (280, 255,255)]
            ]
        }
        

    @staticmethod
    def clampZero(x, thresh=0.001):
        """ Clamps values close to zero to zero
            If a float value is within a specified threshold to zero, assign it to zero
            This is useful if another function has returned -0.0 instead of 0.0 and the sign
            of the number causes other issues (eg. with atan2)

        Args:
            x (float): The value to clamp
            thresh (float, optional): _description_. The threshold to use (Defaults to 0.001)

        Returns:
            float: x if abs(x) > thresh, otherwise return zero
        """
        if abs(x) > thresh:
            x = 0
        return x

    def detect_color(self, frame: cv2.typing.MatLike, hls: cv2.typing.MatLike, ranges: List[List[Tuple]], color: str):
        """_summary_

        Args:
            frame (cv2.typing.MatLike): cv2 frame to process
            hls (cv2.typing.MatLike): frame converted to hls
            ranges (List[List[Tuple]]): lower and upper bounds for colors in hls
        """
        # create masks for list of upper and lower bounds
        masks = []
        for range in ranges:
            mask = cv2.inRange(hls, range[0], range[1])
            masks.append(mask)

        # combine masks
        mask = np.zeros(masks[0].shape)
        for _mask in masks:
            mask = np.bitwise_or(mask, _mask) 

        pixels = cv2.bitwise_and(frame, frame, mask=mask)
        gray = cv2.cvtColor(pixels, cv2.COLOR_BGR2GRAY)

        cnts = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1] # if an older verison of findContours()

        centroids = []
        for c in cnts:
            x,y,w,h = cv2.boundingRect(c)
            A = w*h

            # TODO: allow configurable the maximum area threshold
            # skip centroids with an area below this value (might be a false positive)
            if(A < self.MINUMUM_AREA_PX):
                continue

            centre = { 'x': int(x+w/2), 'y': int(y+h/2), 'w': w, 'h': h, 'A': A, "color": color}
            centroids.append(centre)  

        return centroids
      
    def detect(self, frame):
        """_summary_

        Args:
            frame (cv2.frame): The CV2 frame to process 

        Returns: A tuple where the first element is a list of centroids
                    Each centroid is a dict => { 'x': int, 'y': int, 'w': int, 'h': int, A: float }
                 The second tuple is a dict with addtional information
                 'blurred' => the blurred cv2.frame
                 'masked' => the array of masked colours
                 'contours' => the contours from cv2.findContours
            tuple: (list(centroids), additional)
        """
        '''
        Find centroids in a give CV2 frame

        :param frame: The CV2 frame to process
        '''
        # blur to remove high frequency noise
        blurred = cv2.GaussianBlur(frame,(3,3),0)

        # convert to hls to make it easier to mask colours
        hls = cv2.cvtColor(blurred, cv2.COLOR_BGR2HLS)

        centroids = []
        for colour, color_range in self.colour_ranges.items():
            _centroids = self.detect_color(blurred, hls, color_range, colour)
            centroids.extend(_centroids)

        # return the centroids along with other info that might be useful for debugging
        return centroids

    def pixels2camera(self, x: int, y: int, camera_origin):
        """Convert pixel coordinates to camera space

        Args:
            x (int): pixel's x value
            y (int): pixel's y value
            camera_origin (_type_): The camera rotation matrix

        Returns:
            tuple: x, y, z coodinates in camera space
        """

        # TODO: camera_origin should be a class instance variable passed in __init__

        # we need to clamp -0.0 to +0.0 since atan2 treats the two differently
        x = TargetDetect.clampZero((x-camera_origin[0])/(self.FOCAL_LENGTH_MM))
        y = TargetDetect.clampZero((y-camera_origin[1])/(self.FOCAL_LENGTH_MM))
        z = 1
        return (x, y, z)
    
    # TODO: create a dataclass to hold (x,y,img_width,img_height) and (vec_alt, vec_lat, vec_lon, vec_hdg, vec_pitch, vec_roll)
    #       so that there's only two arguments here (eg. camera2coords(coordinate: CameraPoint, vehicle: VehiclePosition) )
    def pixels2coords(self, x: int, y: int, img_width: int, img_height: int, vec_alt: float, vec_lat: float, vec_lon: float, vec_hdg: float, vec_pitch: float, vec_roll: float) -> dict:
        """Convert pixel coordinates (x, y) to GPS coordinates

        Args:
            x (int): The x pixel coordinate
            y (int): The y pixel coordinate
            img_width (int): The width of the image (pixels)
            img_height (int): The height of the image (pixels)
            vec_alt (float): The vehicle's altitude (degrees)
            vec_lat (float): The vehicle's latitude (decimal degrees)
            vec_lon (float): The vehicle's longitude (decimal degrees)
            vec_hdg (float): The vehicle's heading (degrees)
            vec_pitch (float): The vehicle's pitch (degrees)
            vec_roll (float): The vehicle's roll (degrees)

        Returns:
            dict: the estimated lat and lon of the target (keys: lat, lon)
        """
        # camera origin is the centre of the image
        camera_origin = (int(img_width/2), int(img_height/2))

        # calculate transform from drone to world using yaw, pitch, roll
        # TODO: incorporate pitch and roll
        drone_to_world = R.from_euler('xyz', [vec_hdg, vec_pitch, vec_roll], degrees=True)

        # point in camera reference frame
        point_camera = self.pixels2camera(x, y, camera_origin)

        # point in drone reference frame
        point_drone = self.camera_to_drone.apply(point_camera)
        point_drone = [TargetDetect.clamp_zero(x) for x in point_drone]
        
        # point in world (inertial) reference frame
        point_world = drone_to_world.apply(point_drone)
        point_world = [TargetDetect.clamp_zero(x) for x in point_world]

        # calculate angles using trig
        azimuth = atan2(point_world[1], point_world[0])
        elevation = atan2(-point_world[2], sqrt(point_world[0]**2 + point_world[1]**2))

        # calculate distance to target with more trif
        distance = vec_alt/cos(elevation)

        # shift the vehicle lat, lon by the distance in the direction of azimuth
        geod = Geodesic.WSG84
        shift = geod.Direct(vec_lat, vec_lon, degrees(azimuth), distance)

        # TODO: save to file

        return { 'lat': shift['lat2'], 'lon': shift['lon2'] }

            