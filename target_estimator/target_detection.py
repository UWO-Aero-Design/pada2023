import cv2
import numpy as np

# Define the RTMP stream URL
rtmp_url = "rtmp://localhost:1935/live/test"

# Initialize the video capture object
cap = cv2.VideoCapture(0)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print(f"Frame size: {width} x {height}")
# Loop through the frames of the video stream
while True:
    # Read a frame from the video stream
    ret, frame = cap.read()
    
    frame = cv2.GaussianBlur(frame,(3,3),0)
    hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HLS)

    #mask 1
    lower_lower_red = np.array([0,50,50])
    lower_upper_red = np.array([10,255,255])
    #mask 2
    upper_lower_red = np.array([160,50,50])
    upper_upper_red = np.array([180,255,255])

    mask1 = cv2.inRange(hsv,lower_lower_red,lower_upper_red)
    mask2 = cv2.inRange(hsv, upper_lower_red,upper_upper_red)

    mask = np.bitwise_or(mask1,mask2)

    red_pixels = cv2.bitwise_and(frame,frame,mask=mask)


    edges = cv2.Canny(red_pixels, threshold1=100,threshold2=200)
    circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, 1, 50, param1=100, param2=20, minRadius=40, maxRadius=300)
    # If the frame was successfully read
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x,y,r) in circles:
            cv2.circle(frame,(x,y),r,(0,0,255),5)
    

    
    if ret:
        # Display the frame
        cv2.imshow("Frame", frame)
        cv2.imshow("Mask",mask)
        cv2.imshow("Eges",edges)

    # Wait for the user to press a key
    key = cv2.waitKey(1)


    # If the user presses the 'q' key, exit the loop
    if key == ord('q'):
        break

# Release the video capture object and close the window
cap.release()
cv2.destroyAllWindows()
