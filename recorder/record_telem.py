from pymavlink import mavutil
import threading
import json
import time
import cv2
import datetime
import random
import os
 
stop_flag = threading.Event()
 
client = mavutil.mavlink_connection('udp:127.0.0.1:14551', baud=57600)
client.wait_heartbeat()
print("Heartbeat from PADA!")
 
gps_data = []
attitude_data = []
 
def get_offset_time():
    return time.perf_counter() - start_time
 
def save_telemetry_data(path):
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, 'gps_data.json'), 'w') as f:
        json.dump(gps_data, f, indent=4)
    with open(os.path.join(path, 'attitude_data.json'), 'w') as f: # Corrected typo from 'atitude_data.json' to 'attitude_data.json'
        json.dump(attitude_data, f, indent=4)
 
def receive_telemetry(client: mavutil.mavfile, stop_flag: threading.Event):
    while not stop_flag.is_set():
        print(f"Capturing telem")
        message = client.recv_match(type=['ATTITUDE', 'GLOBAL_POSITION_INT'], blocking=True) # Added blocking=True for cleaner thread handling
        if message:
            if message.get_type() == 'ATTITUDE':
                data = {'data': message.to_dict(), 'timestamp': get_offset_time()}
                attitude_data.append(data)
 
            elif message.get_type() == 'GLOBAL_POSITION_INT':
                data = {'data': message.to_dict(), 'timestamp': get_offset_time()}
                gps_data.append(data)
 
def capture_video(folder, stop_flag: threading.Event):
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
 
    if not cap.isOpened():
        print("Error: Could not open stream.")
        return  # Exit the function if the camera didn't open
 
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    output_path = os.path.join(folder, 'output.avi')
    out = cv2.VideoWriter(output_path, fourcc, 30.0, (1920, 1080))
 
    first_frame = True #one time toggle variable
    while not stop_flag.is_set():
        ret, frame = cap.read()
        if ret:
            if first_frame:
                first_frame = False
                video_offset = get_offset_time()
            out.write(frame)
            cv2.imshow("Video", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_flag.set()
   
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    return video_offset
 
folder = 'flights'
now = datetime.datetime.now()
date_str = now.strftime("%Y%m%d")
time_str = now.strftime("%H%M%S")
random_number = random.randint(100, 999)
unique_id = f"{date_str}_{time_str}_{random_number}"
start_time = time.perf_counter()
path = os.path.join(folder, unique_id)
os.makedirs(path, exist_ok=True) # Added exist_ok=True to ensure no exception if directory already exists
telemetry_thread = threading.Thread(target=receive_telemetry, args=(client, stop_flag,), daemon=True)
telemetry_thread.start()
video_offset = capture_video(path, stop_flag)
save_telemetry_data(path)
with open(os.path.join(path,"video_offset.txt"),"w") as file:
    file.write(str(video_offset))
stop_flag.set() # Ensure stop_flag is set for telemetry thread
telemetry_thread.join() # Ensure telemetry thread has finished before exiting
 