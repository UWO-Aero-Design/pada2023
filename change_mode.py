import time
from pymavlink import mavutil

# Connect to QGroundControl via MAVLink
mav = mavutil.mavlink_connection('udp:0.0.0.0:14550')

# Send MAV_CMD_DO_SET_MODE message to switch to auto mode
mav.mav.command_long_send(
    1,                                # target system ID (1 for QGroundControl)
    1,                                # target component ID (1 for autopilot)
    mavutil.mavlink.MAV_CMD_DO_SET_MODE, # command ID
    0,                                # confirmation
    4,                                # mode (MAV_MODE_AUTO)
    0, 0, 0, 0, 0, 0)                # unused parameters

# Wait for response from Ardupilot system
while True:
    msg = mav.recv_match(type='COMMAND_ACK', blocking=True)
    if msg.command == mavutil.mavlink.MAV_CMD_DO_SET_MODE:
        if msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
            print('Mode change successful')
        else:
            print('Mode change failed')
        break

# Close the MAVLink connection
mav.close()