import queue
from threading import Thread

import cv2

class Video:
    conn = None
    thread = None
    cap = None
    frames = queue.Queue() # TODO: make this a circular buffer
    width = None
    height = None

    def __init__(self, conn):
        self.conn = conn

        print(f"Connecting to {self.conn}")
        self.cap = cv2.VideoCapture(self.conn)
        if (self.cap.isOpened() == False):
            raise Exception(f"Could not connect to stream {self.conn}")
        
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"Connected to {self.conn} (Frame size: {self.width}x{self.height})")

        self.thread = Thread(target=self.capture_video)
        self.thread.daemon = True; # makes sure it cleans up on ctrl+c
        self.thread.start()

    def capture_video(self):
        while True:
            ret, frame = self.cap.read()
            if(ret == False):
                print(f"Error receiving frame from stream {self.conn}")
            else:
                while True:
                    try:
                        self.frames.get(block=False)
                    except queue.Empty:
                        break
                    pass
                self.frames.put(frame)

    def get_resolution(self):
        return (self.width, self.height)
    
    def get_centre_point(self):
        width, height = self.get_resolution()
        return (int(width/2), int(height/2))
    
    def cleanup(self):
        self.cap.release()