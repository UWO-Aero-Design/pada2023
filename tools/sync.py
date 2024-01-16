import cv2
import os


import argparse
import os
import cv2
import subprocess
import os
import json

def parse_args():
    parser = argparse.ArgumentParser(description="Tool to help synchronize DJI video's with Mavlink telemetry")
    parser.add_argument('VIDEO', type=str, help="The path to the DJI video file")
    parser.add_argument('MAV_TLM', type=str, help="The path to the mavlink telemetry file (.tlog file)")

    args = parser.parse_args()
    args.VIDEO = os.path.realpath(args.VIDEO)
    args.MAV_TLM = os.path.realpath(args.MAV_TLM)

    return args

def print_lines(frame, lines, colour):
    y = 30
    for line in lines:
        cv2.putText(frame, line, (50, y), cv2.FONT_HERSHEY_SIMPLEX, 1, colour, 2, cv2.LINE_AA)
        y = y + 30
    return frame

def show_frame(name, frame, fps):
    cv2.namedWindow(name, cv2.WINDOW_NORMAL)
    cv2.imshow(name, frame)
    key = cv2.waitKey(int(1000./float(fps)))
    if key == ord('q') or key == 27 or cv2.getWindowProperty(name, cv2.WND_PROP_VISIBLE) < 1: # q, esc, or window closed
        return False
    return True

def fetch_mavlink_messages(filepath):
    MAVLOGDUMP = os.path.expanduser('~/code/pymavlink/tools/mavlogdump.py')

    ret = subprocess.check_output(['python3', MAVLOGDUMP, filepath, '--format', 'json'])
    json_lines = ret.decode().split('\n')

    if(len(json_lines) == 0):
        raise Exception(f"Could not find any messages in mav file '{filepath}'")

    mav_msgs = [json.loads(x) for x in json_lines if len(x.strip()) > 0]

    return sorted(mav_msgs, key = lambda x:x['meta']['timestamp'])

def find_before_val(items, val):
    prev_index = 0
    prev_item = items[0]
    for i, item in enumerate(items):
        if item['time'] > val:
            return (prev_index, prev_item)
        prev_item = item
        prev_index = i
    return (prev_index, prev_item)

def get_frame(cap, i):
    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
    ret, frame = cap.read()
    if ret == False:
        raise Exception(f"Error loading frame from video file")
    return frame

def main():
    args = parse_args()

    WINDOW_NAME = args.VIDEO
    TEXT_COLOUR = (255, 255, 255)

    mav_msgs = fetch_mavlink_messages(args.MAV_TLM)
    pos_msgs = [x for x in mav_msgs if x['meta']['type'] == 'GLOBAL_POSITION_INT']

    print(f"Loaded mavlink file from '{args.MAV_TLM}' (Messages: {len(mav_msgs)})")
        
    mav_start = pos_msgs[0]['data']['time_boot_ms']
    pos_msgs = [dict(item, **{ 'time': (item['data']['time_boot_ms']-mav_start)/1000.0 }) for item in pos_msgs]

    cap = cv2.VideoCapture(args.VIDEO)
    if (cap.isOpened() == False):
        raise Exception(f"Could not load video from '{args.VIDEO}'")
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Loaded video from '{args.VIDEO}' (Frame size: {width}x{height}, FPS: {fps}, frames: {frames})")
    
    
    # FIRST_FRAME = int(60*fps)
    # cap.set(cv2.CAP_PROP_POS_FRAMES, FIRST_FRAME)
    # fi 549 when time_boot_ms == 620102
    # TLM_DELAY_S = 186-27+10+5+5+5+1+0.1
    TLM_DELAY_S = 185.1

    frame_num = 0
    paused = False
    frame = None
    tlm_index = 0
    while True:
        if not paused:
            frame = get_frame(cap, frame_num)
        frame_num = cap.get(cv2.CAP_PROP_POS_FRAMES)
        
        fs = frame_num*1/fps
    
        if(tlm_index+1 == len(pos_msgs)):
            print("End of telemetry")
            break
        
        _, tlm = find_before_val(pos_msgs, fs+TLM_DELAY_S)

        time_boot = tlm['data']['time_boot_ms']
        vx = tlm['data']['vx']/100
        vy = tlm['data']['vy']/100
        vz = tlm['data']['vz']/100
        h = tlm['data']['relative_alt']/1000
        lat = tlm['data']['lat']/1E7
        lon = tlm['data']['lon']/1E7

        lines = [
            f"Off: {TLM_DELAY_S:3.2f}s",
            f"Fi:  {int(frame_num)}",
            f"F_t: {fs:.2f}s",
            f"D_t: {time_boot}ms",
            f"Vx:  {vx:2.2f}m/s",
            f"Vy:  {vy:2.2f}m/s",
            f"Vz:  {vz:2.2f}m/s",
            f"H:   {h:3.2f}m",
            f"{lat:3.5f}, {lon:3.5f}",
        ]
        frame_annotated = print_lines(frame, lines, TEXT_COLOUR)

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.imshow(WINDOW_NAME, frame_annotated)
        key = cv2.waitKey(int(1000./float(fps)))
        if key == ord('q') or key == 27 or cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1: # q, esc, or window closed
            break
        elif key == ord('p'):
            paused = not paused
        elif key == ord('a'):
            frame_num = frame_num - 1 - 1
            frame = get_frame(cap, frame_num)
        elif key == ord('d'):
            frame_num = frame_num + 1 - 1
            frame = get_frame(cap, frame_num)
        elif key == ord('j'):
            frame_num = frame_num - int(5*fps) - 1
            frame = get_frame(cap, frame_num)
        elif key == ord('l'):
            frame_num = frame_num + int(5*fps) - 1
            frame = get_frame(cap, frame_num)




if __name__ == "__main__":
    main()
