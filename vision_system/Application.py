import tkinter as tk
from threading import Event
from queue import Queue
from Message import TelemetryMessage, ParamsMessage
import tkintermapview

class Application:
    def __init__(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Thread communication
        self.command_queue = Queue()
        self.data_queue = Queue()
        self.outbound_message_queue = Queue()
        self.inbound_message_queue = Queue()
        self.shutdown_event = Event()

        self.setup_ui()

    def setup_ui(self):
        self.root.title("Western Aero Design PADA")

        # Divide the window into two sections: Left for Webcam and Map, Right for Yaw-Pitch-Roll and Controls
        self.left_frame = tk.Frame(self.root)
        self.left_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.right_frame = tk.Frame(self.root)
        self.right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        self.setup_camera_view(self.left_frame)
        self.setup_map_view(self.left_frame)
        self.setup_control_view(self.right_frame)
        self.setup_telemetry_view(self.right_frame)

        # Start updating the GUI with data from the algorithm
        self.update_gui()

    def setup_camera_view(self, parent):
        # Webcam view (Top Left)
        self.webcam_frame = tk.LabelFrame(parent, text="Webcam View")
        self.webcam_frame.pack(expand=True, fill=tk.BOTH)

        # Placeholder for Webcam view
        tk.Label(self.webcam_frame, text="Webcam feed goes here").pack(expand=True)

    def setup_map_view(self, parent):
        # Map view (Bottom Left)
        # map_widget = tkintermapview.TkinterMapView(self.left_frame, width=800, height=600, corner_radius=0)
        # map_widget.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.map_frame = tk.LabelFrame(parent, text="Map View")
        self.map_frame.pack(expand=True, fill=tk.BOTH)

        # Placeholder for Map view
        tk.Label(self.map_frame, text="Map display goes here").pack(expand=True)

    def setup_telemetry_view(self, parent):
        # Yaw-Pitch-Roll Display (Top Right)
        self.ypr_frame = tk.LabelFrame(parent, text="Yaw-Pitch-Roll")
        self.ypr_frame.pack(expand=True, fill=tk.BOTH)

        self.yaw_label = tk.Label(self.ypr_frame, text="Yaw: ")
        self.yaw_label.pack()

        self.pitch_label = tk.Label(self.ypr_frame, text="Pitch: ")
        self.pitch_label.pack()

        self.roll_label = tk.Label(self.ypr_frame, text="Roll: ")
        self.roll_label.pack()

    def setup_control_view(self, parent):
        # Control Panel (Bottom Right)
        self.control_frame = tk.LabelFrame(parent, text="Controls")
        self.control_frame.pack(expand=True, fill=tk.BOTH)

        self.arm_button = tk.Button(self.control_frame, text="Arm", command=lambda: print('Arm'))
        self.arm_button.pack()

        self.angle_degree_label = tk.Label(self.control_frame, text="Angle Degree")
        self.angle_degree_label.pack()

        self.angle_degree_entry = tk.Entry(self.control_frame)
        self.angle_degree_entry.pack()

        self.pada_frame_var = tk.BooleanVar()
        self.consider_pada_frame_checkbox = tk.Checkbutton(self.control_frame, text="Consider PADA frame", variable=self.pada_frame_var, command=lambda: print('Consider PADA'))
        self.consider_pada_frame_checkbox.pack()

        self.save_button = tk.Button(self.control_frame, text="Save", command=lambda: print('Save'))
        self.save_button.pack()
    
    def update_gui(self):
        if self.check_shutdown():
            return
        
        try:
            while not self.inbound_message_queue.empty():
                message = self.inbound_message_queue.get_nowait()
                if isinstance(message, TelemetryMessage):
                    print(f'GUI received telemetry: {message}')
                    self.yaw_label.config(text=f"Yaw: {message.yaw}")
                    self.pitch_label.config(text=f"Pitch: {message.pitch}")
                    self.roll_label.config(text=f"Roll: {message.roll}")
                else:
                    print(f'GUI received unknown message: {type(message)}')
        finally:
            self.root.after(50, self.update_gui)

    def check_shutdown(self):
        if self.shutdown_event.is_set():
            print("GUI received shutdown signal")
            self.shutdown_event.set()
            self.root.destroy()
            return True
        return False

    def on_close(self):
        """Signal the algorithm to stop and close the GUI."""
        self.shutdown_event.set()
        self.root.destroy()
        