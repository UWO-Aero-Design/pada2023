from datetime import datetime
from threading import Thread

from pymavlink import mavutil

class Telemetry:
    conn: str = None
    dev = None
    thread: Thread = None
    telemetry: dict = {}
    debug_print: bool = False

    def __init__(self, conn: str, msg_types, timeout: int = 5, conn_print: bool = True, debug_print: bool = False):
        if(conn_print):
            print(f"Connecting to {conn}")
        self.debug_print = debug_print
        self.conn = conn
        self.dev = mavutil.mavlink_connection(self.conn)
        msg = self.dev.wait_heartbeat(timeout=timeout)
        if(msg == None):
            raise Exception(f"Could not find a device on {conn}")
        
        if(conn_print):
            print(f"Connected to {conn}")

        # create a dictionary to store the most recent telemetry
        # message for each message type that was requested
        self.telemetry = { msg_type.upper(): None for msg_type in msg_types }

        self.thread = Thread(target=self.handle_messges)
        self.thread.daemon = True; # makes sure it cleans up on ctrl+c
        self.thread.start()
    
    def handle_messges(self):
        while True:
            msg = self.dev.recv_match(blocking=True, timeout=1)

            # verify message was received
            if msg is None:
                continue

            # check if this is a message we're configured to listen to
            msg_type = msg.get_type().upper()
            if msg_type not in self.telemetry:
                continue

            # save the message 
            self.telemetry[msg_type] = msg

    def get_msg(self, msg_type):
        if msg_type not in self.telemetry:
            return None
        return self.telemetry[msg_type]
        
    
    def get_msgs(self):
        return self.telemetry