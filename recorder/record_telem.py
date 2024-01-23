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
altitude_data = []

def get_offset_time():
    return time.time() - start_time

def save_telemetry_data(path):
    os.makedirs(path, exist_ok=True) 
    with open(os.path.join(path, 'gps_data.json'), 'w') as f:
        json.dump(gps_data, f)
    with open(os.path.join(path, 'altitude_data.json'), 'w') as f:
        json.dump(altitude_data, f)

def receive_telemetry(client: mavutil.mavfile, stop_flag: threading.Event):
    while not stop_flag.is_set():
        print(f"Capturing telem")
        message = client.recv_match(type=['ATTITUDE', 'GLOBAL_POSITION_INT'])
        if message:
            if message.get_type() == 'ATTITUDE':
                data = {'data': message.to_dict(), 'timestamp': get_offset_time()}
                altitude_data.append(data)

            elif message.get_type() == 'GLOBAL_POSITION_INT':
                data = {'data': message.to_dict(), 'timestamp': get_offset_time()}
                gps_data.append(data)

def capture_video(folder, stop_flag: threading.Event):
    cap = cv2.VideoCapture(1)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    output_path = os.path.join(folder, 'output.avi')
    out = cv2.VideoWriter(output_path, fourcc, 20.0, (640, 480))

    while not stop_flag.is_set():
        print(f"Capturing video")
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        cv2.imshow("Video", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_flag.set()
        
    cap.release()
    out.release()
    cv2.destroyAllWindows()



folder = 'flights'
now = datetime.datetime.now()
date_str = now.strftime("%Y%m%d")
time_str = now.strftime("%H%M%S")
random_number = random.randint(100, 999)
unique_id = f"{date_str}_{time_str}_{random_number}"
start_time = time.time()
path = os.path.join(folder, unique_id)
os.makedirs(path) 
threading.Thread(target=receive_telemetry, args=(client, stop_flag,), daemon=True).start()
capture_video(path, stop_flag)
save_telemetry_data(path)