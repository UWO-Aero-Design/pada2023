#!/usr/bin/python3

import os
import argparse
import subprocess
import time
from threading import Thread, Semaphore

import cv2
from pymavlink import mavutil

# roughly 100m
start_gps = (52.0000000, 21.0000000)
end_gps = (52.8991000, 21.0000000)

def parse_args():
    parser = argparse.ArgumentParser(description="Replay videos and interpolate telemetry")
    parser.add_argument('MAV', type=str, help="The connection URL to use for the mavlink client (eg. udpout:127.0.0.1:5001)")
    parser.add_argument('STREAM', type=str, help="The connection URL to use for the RTMP stream (eg. rtmp://localhost:1935/live/test)")
    parser.add_argument('VIDEO', type=str, help="The path to the video")

    args = parser.parse_args()
    args.VIDEO = os.path.expanduser(args.VIDEO)

    return args


def get_video_length_ms(filename):
    video = cv2.VideoCapture(filename)
    fps = video.get(cv2.CAP_PROP_FPS)
    frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
    return frames / fps

time_boot = time.time()
def time_ms():
    return int((time.time()-time_boot)*1000)

def gps_lerp(gpsA, gpsB, t):
    return (t*(gpsB[0]-gpsA[0]) + gpsA[0], t*(gpsB[1]-gpsA[1]) + gpsA[1])

def send_tlm(client, sem, duration, start_gps, end_gps):
    start_time = time.time()
    last_print = time.time()

    while True:
        if(sem.acquire(timeout=0.25)):
            break

        time_boot_ms = int((time.time()-start_time)*1000)
        gps = gps_lerp(start_gps, end_gps, (time.time()-start_time)/duration)

        client.mav.global_position_int_send(time_boot_ms, int(gps[0]*1E7), int(gps[1]*1E7), 1, 10, 5, 2, 4, 0)
        client.mav.heartbeat_send(1, 3, 89, 11, 5, 3)

        if(time.time() - last_print > 0.5):
            print(f"[{time_boot_ms}] Lat: {gps[0]}, Lon: {gps[1]}")
            last_print = time.time()

def send_video(sem, video_path, stream_url):
    print("Starting video")
    subprocess.run(
        ['ffmpeg', '-re', '-i', os.path.expanduser(video_path), '-c:v', 'copy', '-c:a', 'aac', '-ar', '44100', '-ac', '1', '-f', 'flv', stream_url],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT)
    sem.release()
    print("Stopping video")

def main():
    args = parse_args()

    if(not os.path.isfile(args.VIDEO)):
        print(f"Error: {args.VIDEO} is not a file")
        exit(0)

    length = get_video_length_ms(args.VIDEO)

    print(f"Using video {args.VIDEO}")

    client = mavutil.mavlink_connection(args.MAV)

    while True:
        sem = Semaphore(0)
        tlm_thread = Thread(target=send_tlm, args=[client, sem, length, start_gps, end_gps])
        tlm_thread.daemon = True; # makes sure it cleans up on ctrl+c

        video_thread = Thread(target=send_video, args=[sem, args.VIDEO, args.STREAM])
        video_thread.daemon = True; # makes sure it cleans up on ctrl+c

        video_thread.start()
        tlm_thread.start()

        tlm_thread.join()
        video_thread.join()

if __name__ == "__main__":
    main()