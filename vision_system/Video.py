import queue
from threading import Thread, Condition

import cv2

class Video:
    conn: str = None
    thread = None
    cap = None
    width: int = None
    height: int = None
    frame = None
    debug_print: bool = False
    cv = Condition()
    new_frame_available = False

    def __init__(self, conn: str, debug_print: bool = False, save_file: str = None):
        self.conn = conn
        self.debug_print = debug_print

        if debug_print:
            print(f"Connecting to {self.conn}")
        self.cap = cv2.VideoCapture(self.conn)
        if (self.cap.isOpened() == False):
            raise Exception(f"Could not connect to stream {self.conn}")
        
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if debug_print:
            print(f"Connected to {self.conn} (Frame size: {self.width}x{self.height})")

        self.thread = Thread(target=self.capture_video, args=(self.cv, save_file))
        self.thread.daemon = True; # makes sure it cleans up on ctrl+c
        self.thread.start()

    def capture_video(self):
        while True:
            ret, frame = self.cap.read()
            if(ret == False):
                print(f"Error receiving frame from stream {self.conn}")
                continue

            self.frame = frame

            # notify that a new frame is available
            self.new_frame_available = True
            self.condition.notify()

            # wait until frame has been retreived by user
            self.condition.wait()

    def get_resolution(self):
        return (self.width, self.height)
    
    def get_centre_point(self):
        width, height = self.get_resolution()
        return (int(width/2), int(height/2))
    
    def cleanup(self):
        self.cap.release()

    def get_frame(self):
        with self.condition:
            if not self.new_frame_available:
                self.condition.wait()  # Wait until a new frame is available

            self.new_frame_available = False

            # Notify the capture thread that it can capture the next frame
            self.condition.notify()
            return self.frame