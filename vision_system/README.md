# PADA Vision System

## Simulator / Replay System
*File: sim_client.py*

This program will allow developers to send saved Mavlink messages and video frames as if they were currently being captured from the PADA. This is useful for running the vision system without connecting any hardware and flying the PADA. It uses FFMPEG to stream video to an RTMP client and streams interpolated Mavlink GPS fused data (`GLOBAL_POSITION_INT`) to a Mavlink connection (typically a UDP port).

The start and end GPS coordinates are currently hardcoded in the script but this will eventually be modifed to accept some sort of telemetry log.

Note: an RTMP server must already be running. If Docker is installed, an RTMP server can easily be started with `docker run --rm -p 1935:1935 --name nginx-rtmp tiangolo/nginx-rtmp`

Usage: `python3 sim_client.py <mavlink connection> <rtmp stream> <input file>`

Example: `python3 sim_client.py udpout:127.0.0.1:5001 rtmp://localhost:1935/live/test ~/45degree_1.mp4`

## Vision System
*File: vision_system.py*

This is the main program for running the PADA vision system using an RTMP stream for video and Mavlink telemetry stream. It is an early work-in-progress with many issues that still need to be addressed. The main goal is to extract GPS coordinates of target landing zones using the video and telemetry streams. The PADA/PA will then use these coordinates to attempt a landing at one of the zones. 

Usage: `python3 vision_system.py <mavlink connection> <rtmp stream>`

Example: `python3 vision_system.py udpin:127.0.0.1:5001 rtmp://localhost:1935/live/test`