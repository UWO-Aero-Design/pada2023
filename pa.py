import tkinter as tk
from threading import Thread
import queue
import time
from pymavlink import mavutil

# TODO: add mode to screen

class AltitudeApp:
    def __init__(self, root, mav_conn):
        FONT = 'Arial'
        FONT_SIZE = 100

        self.root = root
        self.root.title("Western Aero Design PADA Drop Control")
        
        self.altitude = 0
        self.release_altitude = 0
        self.altitude_var = tk.StringVar(value=f"Altitude: {self.altitude:3.2f} ft")
        self.release_altitude_var = tk.StringVar(value=f"Release Altitude: {self.release_altitude:3.2f} ft")
        self.mav_mode_var = tk.StringVar(value=f"Mode: ---")
        
        tk.Label(root, textvariable=self.altitude_var, font=(FONT, FONT_SIZE)).pack()
        tk.Label(root, textvariable=self.release_altitude_var, font=(FONT, FONT_SIZE)).pack()
        tk.Label(root, textvariable=self.mav_mode_var, font=(FONT, FONT_SIZE)).pack()
        tk.Button(root, text="Release", font=(FONT, FONT_SIZE), command=self.send_release_signal).pack()
        
        self.altitude_queue = queue.Queue()
        self.mode_queue = queue.Queue()
        self.release_queue = queue.Queue()
        
        self.thread = Thread(target=self.mavlink_thread, daemon=True, args=[mav_conn])
        self.thread.start()
        
        self.update_gui_from_queue()
    
    def mavlink_thread(self, conn):

        client = mavutil.mavlink_connection(conn, baud=57600)
        client.wait_heartbeat()

        print("Connected to mavlink")

        while True:
            msg = client.recv_match(type=['GLOBAL_POSITION_INT', 'HEARTBEAT'], blocking=True, timeout=0.1)
            if msg:
                if msg.get_type() == 'GLOBAL_POSITION_INT':
                    self.altitude_queue.put(msg.relative_alt/1000)
                elif msg.get_type() == 'HEARTBEAT':
                    print(msg)
            if not self.release_queue.empty():
                release_signal = self.release_queue.get()
                if release_signal:
                    print("Release signal received in child thread.")
                    break
    
    def update_gui_from_queue(self):
        try:
            while not self.altitude_queue.empty():
                self.altitude = self.altitude_queue.get_nowait()
                if(self.altitude):
                    self.altitude_var.set(f"Altitude: {self.altitude:3.2f} ft")
                self.release_altitude_var.set(f"Release Altitude: {self.release_altitude:3.2f} ft")
        except queue.Empty:
            pass
        self.root.after(100, self.update_gui_from_queue)
    
    def send_release_signal(self):
        self.release_altitude = self.altitude
        self.release_queue.put(True)

if __name__ == "__main__":
    MAV_CONN = '/dev/cu.usbserial-D30AFHY6'
    root = tk.Tk()
    app = AltitudeApp(root, MAV_CONN)
    root.mainloop()
