#!/usr/bin/python3

import os
import argparse
import subprocess
from time import time, sleep
from threading import Thread, Event
import json
from aiohttp import BodyPartReader

import cv2
from pymavlink import mavutil

def parse_args():
    parser = argparse.ArgumentParser(description="Replay videos and interpolate telemetry")
    parser.add_argument('MAV', type=str, help="The connection URL to use for the mavlink client (eg. udpout:127.0.0.1:5001)")
    parser.add_argument('STREAM', type=str, help="The connection URL to use for the RTMP stream (eg. rtmp://localhost:1935/live/test)")
    parser.add_argument('VIDEO', type=str, help="The path to the video")
    parser.add_argument('GPS', type=str, help="The path to the gps data")
    parser.add_argument('ATTITUDE', type=str, help="The path to the attitude data")

    args = parser.parse_args()
    args.VIDEO = os.path.expanduser(args.VIDEO)
    args.GPS = os.path.expanduser(args.GPS)
    args.ATTITUDE = os.path.expanduser(args.ATTITUDE)

    return args

def combine_tlm(gps: list(), att: list()):
    items = gps + att
    return sorted(items, key=lambda x: x["timestamp"])

def send_tlm(stop_flag: Event, client, gps: list(), attitude: list()):

    tlm = combine_tlm(gps, attitude)
    start_time = time()
    last_hb = 0
    HB_INTERVAL = 0.5

    for item in tlm:
        target_time = start_time + item["timestamp"]

        # wait until target time
        while time() < target_time:
            if(time() - last_hb > HB_INTERVAL):
                client.mav.heartbeat_send(1, 3, 89, 11, 5, 3)
                last_hb = time()
            if stop_flag.is_set():
                break
            sleep(0.01)

        time_boot_ms = int((time()-start_time)*1000)
        data = item['data']
        packet_type = data['mavpackettype']

        print(f"{item['timestamp']}: {item['data']['mavpackettype']}")
        if(packet_type == 'GLOBAL_POSITION_INT'):
            client.mav.global_position_int_send(time_boot_ms, data['lat'], data['lon'], data['alt'], data['relative_alt'], 
                                                data['vx'], data['vy'], data['vz'], data['hdg'])
        elif(packet_type == 'ATTITUDE'):
            client.mav.attitude_send(time_boot_ms, data['roll'], data['pitch'], data['yaw'], data['rollspeed'], data['pitchspeed'], data['yawspeed'])
        else:
            print(f"Unknown packet type: {packet_type}")
    
    print("End of telemetry stream")
    stop_flag.set()

def send_video(stop_flag: Event, video_path: str, stream_url: str) -> None:
    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_delay = 1/cap.get(cv2.CAP_PROP_FPS)
    resolution = f"{width}x{height}"
    
    ffmpeg_command = ['ffmpeg',
                  '-y',                     # Overwrite output file if it exists
                  '-f', 'rawvideo',         # Input format is raw video
                  '-vcodec', 'rawvideo',    # Input codec is raw video
                  '-s', '640x480',          # Size of one frame TODO: dynamic
                  '-pix_fmt', 'bgr24',      # Input pixel format
                  '-r', '25',               # Input frame rate
                  '-i', '-',                # Input comes from stdin
                  '-c:v', 'libx264',        # Codec for video
                  '-pix_fmt', 'yuv420p',    # Pixel format for output
                  '-preset', 'veryfast',    # Preset for faster processing
                  '-b:v', '2500k',          # Video bitrate
                  '-maxrate', '2500k',      # Max bitrate
                  '-bufsize', '5000k',      # Buffer size
                  '-vf', 'format=yuv420p',  # Video filter for pixel format
                  '-g', '50',               # Keyframe interval
                  '-f', 'flv',              # Output format is FLV
                  stream_url]               # Output stream URL
    
    # TODO: grab stderr and optionally print to process stdin
    ffmpeg = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    def monitor_ffmpeg():
        for line in ffmpeg.stderr:
            print("ffmpeg:", line, end='')

    # monitor ffmpeg errors
    Thread(target=monitor_ffmpeg, daemon=True).start()

    while not stop_flag.is_set():
        start = time()
        ret, frame = cap.read()
        if not ret:
            print("End of video stream")
            stop_flag.set()
            break
        try:
            ffmpeg.stdin.write(frame.tobytes())
        except Exception as e:
            print(f"ffmpeg process is down {e}")
        additional_sleep = frame_delay-(time()-start)
        if(additional_sleep > 0):
            sleep(additional_sleep)

    print("Closing video stream")
    cap.release()
    ffmpeg.stdin.close()
    ffmpeg.terminate()

def main():
    args = parse_args()

    if(not os.path.isfile(args.VIDEO)):
        print(f"Error: {args.VIDEO} is not a file")
        exit(0)

    print(f"Using video {args.VIDEO}, GPS file {args.GPS}, attitude file {args.ATTITUDE}")

    with open(args.GPS, 'r') as file:
        gps = json.load(file)

    with open(args.ATTITUDE, 'r') as file:
        attitude = json.load(file)

    client = mavutil.mavlink_connection(args.MAV)

    stop_flag = Event()

    tlm_thread = Thread(target=send_tlm, args=[stop_flag, client, gps, attitude])
    tlm_thread.daemon = True; # makes sure it cleans up on ctrl+c
    tlm_thread.start()

    video_thread = Thread(target=send_video, args=[stop_flag, args.VIDEO, args.STREAM])
    video_thread.daemon = True; # makes sure it cleans up on ctrl+c
    video_thread.start()


    tlm_thread.join()
    video_thread.join()

if __name__ == "__main__":
    main()