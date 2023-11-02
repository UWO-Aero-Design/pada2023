import queue
from threading import Thread

from pymavlink import mavutil

class Telemetry:
    conn = None
    dev = None
    thread = None
    telemetry = queue.Queue()

    def __init__(self, conn, timeout=5):
        print(f"Connecting to {conn}")
        self.conn = conn
        self.dev = mavutil.mavlink_connection(self.conn)
        msg = self.dev.wait_heartbeat(timeout=timeout)
        if(msg == None):
            raise Exception(f"Could not find a device on {conn}")
        print(f"Connected to {conn}")

        self.thread = Thread(target=self.handle_messges)
        self.thread.daemon = True; # makes sure it cleans up on ctrl+c
        self.thread.start()
    
    def handle_messges(self):
        while True:
            msg = self.dev.recv_match(blocking=True, timeout=5)
            if msg is not None:
                if msg.get_type() == 'GLOBAL_POSITION_INT':
                    self.telemetry.put(msg)