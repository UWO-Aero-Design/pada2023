import cv2

# Define the RTMP stream URL
rtmp_url = "rtmp://localhost:1935/live/test"

# Initialize the video capture object
cap = cv2.VideoCapture(rtmp_url)

# Loop through the frames of the video stream
while True:
    # Read a frame from the video stream
    ret, frame = cap.read()
    
    # If the frame was successfully read
    if ret:
        # Display the frame
        cv2.imshow("RTMP Stream", frame)

    hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)

    # Wait for the user to press a key
    key = cv2.waitKey(1)

    # If the user presses the 'q' key, exit the loop
    if key == ord('q'):
        break

# Release the video capture object and close the window
cap.release()
cv2.destroyAllWindows()
