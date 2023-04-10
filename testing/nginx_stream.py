import cv2
import numpy as np
import ffmpeg
import sys
# Define the video stream URL
stream_url = "rtmp://localhost:1935/live/test"

print("Starting")
# Probe the input stream to get its format and codec information

probe = ffmpeg.probe(stream_url)


video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
width = int(video_info['width'])
height = int(video_info['height'])

# Create the input and output streams
in_stream = ffmpeg.input(stream_url)
out_stream = ffmpeg.output(in_stream, "pipe:", format='rawvideo', pix_fmt='bgr24')

# Start the ffmpeg process
process = ffmpeg.run_async(out_stream, pipe_stdout=True)

# Main loop
while True:
    print("Running")
    # Read a video frame
    raw_frame = process.stdout.read(width * height * 3)

    # Check if the frame was read successfully
    if not raw_frame:
        break

    # Convert the raw frame to a numpy array and reshape it
    frame = np.frombuffer(raw_frame, np.uint8).reshape(height, width, 3)

    # Process the video frame using OpenCV (for example, converting to grayscale)
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Display the processed video frame
    cv2.imshow("Processed Video Feed", gray_frame)

    # Exit the loop if 'q' is pressed
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

# Release resources
process.wait()
cv2.destroyAllWindows()
