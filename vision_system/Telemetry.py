from threading import Thread, Event
from queue import Queue
from Message import AttitudeMessage, PositionMessage
from math import degrees

from pymavlink import mavutil

class Telemetry:
    GLOBAL_POSITION_INT = 'GLOBAL_POSITION_INT'
    ATTITUDE = 'ATTITUDE'

    conn: str = None
    dev = None
    thread: Thread = None
    telemetry: dict = {}
    debug_print: bool = False

    def __init__(self, conn: str, timeout: int = 5, conn_print: bool = True, debug_print: bool = False):
        self.shutdown_event = Event()
        self.telemetry_queue = Queue()

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

        self.thread = Thread(target=self.handle_messges)
        self.thread.daemon = True; # makes sure it cleans up on ctrl+c
        self.thread.start()
    
    def handle_messges(self):
        while not self.shutdown_event.is_set():
            msg = self.dev.recv_match(blocking=True)

            # verify message was received
            if not msg:
                continue

            if msg.get_type() == "BAD_DATA":
                if mavutil.all_printable(msg.data):
                    print(f"Error with mavlink message: {msg.data}")

            # check if this is a message we're configured to listen to
            msg_type = msg.get_type().upper()
            if msg_type == self.GLOBAL_POSITION_INT:
                self.telemetry_queue.put(self.convert_position_msg(msg))
            elif msg_type == self.ATTITUDE:
                self.telemetry_queue.put(self.convert_attitude_msg(msg))

    def convert_attitude_msg(self, msg) -> AttitudeMessage:
        return AttitudeMessage(
            time_boot_ms = msg.time_boot_ms/1000,
            roll = degrees(msg.roll),
            pitch = degrees(msg.pitch),
            yaw = degrees(msg.yaw),
            rollspeed = degrees(msg.rollspeed),
            pitchspeed = degrees(msg.pitchspeed),
            yawspeed = degrees(msg.yawspeed)
        )
    
    def convert_position_msg(self, msg) -> PositionMessage:
        return PositionMessage(
            time_boot_ms = msg.time_boot_ms/1000,
            lat = msg.lat/1E7,
            lon = msg.lon/1E7,
            alt = msg.alt/1E3,
            relative_alt = msg.relative_alt/1E3,
            vx = msg.vx/100,
            vy = msg.vy/100,
            vz = msg.vz/100,
            hdg = msg.hdg/100
        )