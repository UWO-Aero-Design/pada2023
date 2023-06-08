import cv2
import numpy as np
from pyproj import Transformer

# Constants
CAMERA_VERTICAL_FOV = 83  
CAMERA_HORIZONTAL_FOV = 83 
IMAGE_WIDTH = 0  # Width of the image captured by the camera (pixels)
IMAGE_HEIGHT = 0  # Height of the image captured by the camera (pixels)
VIDEO_PATH = 'data-set\90degree_2.MP4'
# Initialize a transformer from pyproj, this will be used to convert between longitude and latitude to x and y coordinates.
transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)



def create_blob_detector():
    # Set up the blob detector parameters
    params = cv2.SimpleBlobDetector_Params()
    params.filterByColor = True
    params.blobColor = 255  # Blobs must be white on a black background
    # Create a blob detector with the parameters
    return cv2.SimpleBlobDetector_create(params)

def process_image(image, detector):
    """_summary_
        Processes image to extract x and y pixel coordinates of the center circle
    Args:
        image (_type_): image frame
        detector : blob detector

    Returns:
        _type_: tuple containing x and y coordinates
    """
    # Convert the image to HSV color space, easier to work with
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define the color range for the red color in HSV
    lower_red = np.array([0, 70, 50])
    upper_red = np.array([10, 255, 255])

    lower_red_2 = np.array([160,70,50])
    upper_red_2 = np.array([180,255,255])

    lower_blue = np.array([90, 70, 50])
    upper_blue = np.array([150, 255, 255])

    # Threshold the HSV image to get only red colors
    # Returns a mask with ones where its red and zeros where its not
    mask1 = cv2.inRange(hsv_image, lower_red, upper_red)
    mask2 = cv2.inRange(hsv_image, lower_red_2, upper_red_2)
    
    # element wise or
    mask = np.bitwise_or(mask1, mask2)
    
    # mask for blue
    mask_blue = cv2.inRange(hsv_image, lower_blue, upper_blue)
    
    # Detect blobs in the image
    red_keypoints = detector.detect(mask)
    blue_keypoints = detector.detect(mask_blue)

    keypoints_red = np.array([[int(k.pt[0]), int(k.pt[1]), 'r'] for k in red_keypoints])
    keypoints_blue = np.array([[int(k.pt[0]), int(k.pt[1]), 'b'] for k in blue_keypoints])

    # In case no keypoints were found, create an empty array with the appropriate shape
    if keypoints_red.size == 0:
        keypoints_red = np.empty((0, 3))
    if keypoints_blue.size == 0:
        keypoints_blue = np.empty((0, 3))
    
    return np.concatenate((keypoints_red, keypoints_blue), axis=0)

def estimate_gps(keypoint, plane_gps, plane_altitude, camera_pitch, camera_yaw):
    """Extracts the GPS coordinate of the center of a circle"""
    # Convert the altitude to meters (assuming it was in feet)
    plane_altitude_m = plane_altitude * 0.3048

    # Compute the ground distance covered by each pixel in the image (in meters)
    ground_distance_per_pixel_x = (2 * plane_altitude_m * np.tan(np.radians(CAMERA_VERTICAL_FOV / 2))) / IMAGE_WIDTH
    ground_distance_per_pixel_y = (2 * plane_altitude_m * np.tan(np.radians(CAMERA_HORIZONTAL_FOV / 2))) / IMAGE_HEIGHT

    # Compute the offset of the circle (keypoint) from the center of the image (in pixels)
    offset_pixels_x = keypoint.pt[0] - (IMAGE_WIDTH / 2)
    offset_pixels_y = keypoint.pt[1] - (IMAGE_HEIGHT / 2)

    # Convert the offset to ground distance (in meters)
    offset_meters_x = offset_pixels_x * ground_distance_per_pixel_x
    offset_meters_y = offset_pixels_y * ground_distance_per_pixel_y

    # Convert the plane's GPS coordinates to meters
    plane_x_m, plane_y_m = transformer.transform(plane_gps[1], plane_gps[0])

    # Compute the GPS coordinates of the circle
    circle_x_m = plane_x_m + offset_meters_x * np.cos(np.radians(camera_yaw))
    circle_y_m = plane_y_m + offset_meters_y * np.sin(np.radians(camera_yaw))

    # Convert the circle's coordinates back to GPS
    circle_gps = transformer.transform(circle_x_m, circle_y_m, direction='INVERSE')

    return circle_gps

def main():
    # Main function
    cap = cv2.VideoCapture(VIDEO_PATH)
    IMAGE_WIDTH = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    IMAGE_HEIGHT = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    detector = create_blob_detector()

    # store trace of detection paths
    historical_detection = []
    while cap.isOpened():

        ret, image = cap.read()
        # Get the image from the onboard camera
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        

        # # Get the plane's state
        # plane_gps = ...  # in format [longitude, latitude]
        # plane_altitude = ...  # in feet

        # # Process the image to find red circles
        keypoints = process_image(image,detector)
        
        # For each keypoint, estimate its GPS coordinates
        for keypoint in keypoints:

            historical_detection.append(keypoint)

        if historical_detection is not None:
            for trace_point in historical_detection:
                if(trace_point[2]=='r'):
                    cv2.circle(image, (int(trace_point[0]), int(trace_point[1])), 5, (0, 0, 255), -1)
                elif(trace_point[2]=='b'):
                    cv2.circle(image, (int(trace_point[0]), int(trace_point[1])), 5, (255, 0, 0), -1)


            # circle_gps = estimate_gps(keypoint, plane_gps, plane_altitude)
            # print(f"Found a circle at {circle_gps}")
        cv2.imshow('Drone Footage:',image)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()