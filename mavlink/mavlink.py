from pymavlink import mavutil

# Create a connection to the UDP port
master = mavutil.mavlink_connection('udp:127.0.0.1:14550')

while True:
    # Receive a RADIO_STATUS message
    radio_status = master.recv_match(type='RADIO_STATUS', blocking=False)
    print(radio_status)
    # # Extract and print the relevant information from the message
    # rssi = radio_status.rssi
    # noise = radio_status.noise
    # remrssi = radio_status.remrssi
    # rxerrors = radio_status.rxerrors
    # fixed = radio_status.fixed
    
    # print(f"RSSI: {rssi}")
    # print(f"Noise: {noise}")
    # print(f"Remote RSSI: {remrssi}")
    # print(f"Receive errors: {rxerrors}")
    # print(f"Fixed errors: {fixed}")
    # print("------")



# Wait for a heartbeat to ensure the connection is established
master.wait_heartbeat()
print("Heartbeat detected!")