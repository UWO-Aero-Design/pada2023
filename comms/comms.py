# Tasks:
# - Display QGroundControl
# - Communicate with PADA
    # Requires MAVLINK Router
# - Computer Vision Algo decides when to send Land Command
# - Send Land Command

from pymavlink import mavutil
from queue import Queue
from pymavlink.dialects.v10 import all as mavlink
import logging

client = mavutil.mavlink_connection('udp:127.0.0.1:14551', baud=57600)

client.wait_heartbeat()
print("Heart beat from PADA!")

attiude_queue = Queue()
gps_queue = Queue()

def get_telemetry(client: mavutil.mavfile):
    message = client.recv_match(type=['ATTITUDE', 'GLOBAL_POSITION_INT'])
    if message:
        if message.get_type() == 'ATTITUDE':
            attiude_queue.put(message)

        elif message.get_type() == 'GLOBAL_POSITION_INT':
            gps_queue.put(message)

def process_telemetry():
    if not attiude_queue.empty():
        print(attiude_queue.get())

    if not gps_queue.empty():
        print(gps_queue.get())

def send_landing(client: mavlink.MAVLink):
    # Replace with your desired landing coordinates
    landing_lat = 42.978990
    landing_lon = -81.144590
    landing_alt = 0  # altitude in meters
    # Clear any existing missions
    client.waypoint_clear_all_send()

    # Set mission count to 1 (for landing)
    client.waypoint_count_send(1)

    # Wait for the request for the waypoint
    msg = client.recv_match(type=['MISSION_REQUEST'], blocking=True)

    # Send landing waypoint
    client.mav.mission_item_send(
        client.target_system,
        client.target_component,
        0,  # waypoint index
        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,  # frame
        mavutil.mavlink.MAV_CMD_NAV_LAND,  # command
        0,  # current waypoint - set to 0 to indicate this is not the current waypoint
        1,  # autocontinue - set to 1 to indicate autocontinue
        0,  # param1 - not used
        0,  # param2 - not used
        0,  # param3 - not used
        0,  # param4 - not used
        landing_lat,  # x - latitude
        landing_lon,  # y - longitude
        landing_alt   # z - altitude
    )


    # Wait for mission acknowledgement
    client.recv_match(type=['MISSION_ACK'], blocking=True)

    # Set mode to AUTO to start the mission
    client.mav.set_mode_send(
        client.target_system,
        mavutil.mavlink.MAV_MODE_AUTO_ARMED,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
    )

    # Start the mission
    client.mav.command_long_send(
        client.target_system,
        client.target_component,
        mavutil.mavlink.MAV_CMD_MISSION_START,
        0,  # confirmation
        0, 0, 0, 0, 0, 0,0  # unused parameters
    )

    print("Mission started, vehicle is landing...")

send_landing(client)
while True:
    get_telemetry(client)
    process_telemetry()

        
        