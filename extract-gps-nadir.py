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



def process_image(image) :
    """_summary_
        Proccesses image to extract x and y pixel coordinates of the center circle
    Args:
        image (_type_): image frame

    Returns:
        _type_: tuple containing x and y coordinates
    """
    # Convert the image to HSV color space, easier to work wtih
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define the color range for the red color in HSV
    lower_red = np.array([0, 70, 50])
    upper_red = np.array([10, 255, 255])

    lower_red_2 = np.array([160,70,50])
    upper_red_2 = np.array([180,255,255])


    # Threshold the HSV image to get only red colors
    # Returns a mask with ones where its red and zeros where its not
    mask1 = cv2.inRange(hsv_image, lower_red, upper_red)
    mask2 = cv2.inRange(hsv_image, lower_red_2, upper_red_2)

    #element wise or
    mask = np.bitwise_or(mask1,mask2)
    return mask
    # # Set up the blob detector parameters
    # params = cv2.SimpleBlobDetector_Params()
    # params.filterByColor = True
    # params.blobColor = 20  # Blobs must be white on a black background

    # # Create a blob detector with the parameters
    # detector = cv2.SimpleBlobDetector_create(params)

    # # Detect blobs in the image
    # keypoints = detector.detect(mask)

    # return keypoints

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
    while cap.isOpened():

        ret, image = cap.read()
        # Get the image from the onboard camera
        print()
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        cv2.imshow('Drone Footage:',image)

        # # Get the plane's state
        # plane_gps = ...  # in format [longitude, latitude]
        # plane_altitude = ...  # in feet

        # # Process the image to find red circles
        mask = process_image(image)
        cv2.imshow('Mask',mask)
        # # For each keypoint, estimate its GPS coordinates
        # for keypoint in keypoints:
        #     circle_gps = estimate_gps(keypoint, plane_gps, plane_altitude)
        #     print(f"Found a circle at {circle_gps}")

    cv2.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()