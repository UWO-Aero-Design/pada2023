#!/usr/bin/python3

import signal
import argparse
import os

from pymavlink import mavutil

def parse_args():
    parser = argparse.ArgumentParser(description="Save a list of message types from a mavlink device")
    parser.add_argument('MAV', type=str, help="The connection URL to use for the mavlink client (eg. /dev/ttyUSB0)")
    parser.add_argument('OUT', type=str, help="The file to save the messages to")

    args = parser.parse_args()
    args.OUT = os.path.realpath(args.OUT)

    return args

def main():
    msg_types = {}

    def signal_handler(sig, frame):
        with open(args.OUT, 'w') as file:
            for msg in list(msg_types.values()):
                file.write(f"{msg}\n")
        print(f"Wrote {len(msg_types)} messages to {args.OUT}")
        exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    args = parse_args()

    print(f"Connecting to {args.MAV}")

    try:
        device = mavutil.mavlink_connection(args.MAV)
    except Exception as err:
        print(err)
        exit(0)

    msg = device.wait_heartbeat(timeout=3)
    if(msg == None):
        print(f"Could not find a device on {args.MAV}")
        exit(0)

    print(f"Connected to {args.MAV}")

    while True:
        msg = device.recv_match(blocking=True, timeout=5)
        if msg is not None:
            typ = msg.get_type()
            if(typ not in msg_types):
                print(f"Read new message type '{typ}' (Total: {len(msg_types)+1})")
            msg_types[typ] = msg

if __name__ == "__main__":
    main()
