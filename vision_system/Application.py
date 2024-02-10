import tkinter as tk
from threading import Event
from queue import Queue
from Message import PositionMessage, AttitudeMessage, PointMessage, VideoMessage
from tkintermapview import TkinterMapView
import cv2
import pathlib
from PIL import Image, ImageTk
import geocoder

class Application:
    ICON_LOCATION = str((pathlib.Path(__file__) / '../logo.png').resolve())
    def __init__(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.img = tk.PhotoImage(file=self.ICON_LOCATION)
        self.root.iconphoto( False, self.root.img )

        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # replace either screen_width and screen_height to change the appropriate dimension
        self.root.geometry(f"{self.screen_width}x{self.screen_height}")

        # Thread communication
        self.command_queue = Queue()
        self.data_queue = Queue()
        self.outbound_message_queue = Queue()
        self.inbound_message_queue = Queue()
        self.shutdown_event = Event()

        pos = geocoder.ip('me').latlng
        self.centre_pos = (float(pos[0]), float(pos[1]))

        self.DOT_SIZE = 6
        self.cirlce_image = self.create_circle_image(self.DOT_SIZE)

        self.markers = []

        self.setup_ui()

    def add_point(self, point: PointMessage):
        self.markers.append(self.map_widget.set_marker(point.lat, point.lon, icon=self.cirlce_image))

    def remove_points(self):
        for marker in self.markers:
            marker.delete()
        self.markers = []

    def setup_ui(self):
        self.root.title("Western Aero Design PADA")

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.camera_frame = tk.Frame(self.root, bd=2, relief="groove")
        self.camera_frame.grid(row=0, column=0, sticky="nsew", ipadx=0, ipady=0, padx=0, pady=0)
        self.root.after(150, self.setup_camera_view, self.camera_frame)

        self.map_frame = tk.Frame(self.root, bd=2, relief="groove")
        self.map_frame.grid(row=1, column=0, sticky="nsew")
        self.setup_map_view(self.map_frame)

        self.telemetry_frame = tk.Frame(self.root, bd=2, relief="groove")
        self.telemetry_frame.grid(row=0, column=1, sticky="nsew")
        self.setup_telemetry_view(self.telemetry_frame)

        self.control_frame = tk.Frame(self.root, bd=2, relief="groove")
        self.control_frame.grid(row=1, column=1, sticky="nsew")
        self.setup_control_view(self.control_frame)

        # Start updating the GUI with data from the algorithm
        self.update_gui()

    def setup_camera_view(self, parent):
        self.image_label = tk.Label(parent, borderwidth=0, padx=0, pady=0)
        self.image_label.pack(fill='both', expand=True)

    def setup_map_view(self, parent):
        self.map_widget = TkinterMapView(parent, corner_radius=0)
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        self.map_widget.set_position(self.centre_pos[0], self.centre_pos[1])
        self.map_widget.set_zoom(17)
        self.map_widget.pack(expand=True, fill="both")

    def setup_telemetry_view(self, parent):
        self.yaw_label = tk.Label(parent, text="Yaw: ")
        self.yaw_label.pack()

        self.pitch_label = tk.Label(parent, text="Pitch: ")
        self.pitch_label.pack()

        self.roll_label = tk.Label(parent, text="Roll: ")
        self.roll_label.pack()

        self.lat_label = tk.Label(parent, text="Lat: ")
        self.lat_label.pack()

        self.lon_label = tk.Label(parent, text="Lon: ")
        self.lon_label.pack()

        self.hdg_label = tk.Label(parent, text="Hdg: ")
        self.hdg_label.pack()

    def setup_control_view(self, parent):

        self.off_nadir_label = tk.Label(parent, text="Off-Nadir Threshold (°)")
        self.off_nadir_label.pack()

        self.off_nadir_entry = tk.Entry(parent)
        self.off_nadir_entry.pack()

        self.area_threshold_label = tk.Label(parent, text="Area Threshold (px)")
        self.area_threshold_label.pack()

        self.area_threshold_entry = tk.Entry(parent)
        self.area_threshold_entry.pack()

        self.pada_frame_var = tk.BooleanVar()
        self.consider_pada_frame_checkbox = tk.Checkbutton(parent, text="Consider PADA frame", variable=self.pada_frame_var)
        self.consider_pada_frame_checkbox.pack()

        self.save_button = tk.Button(parent, text="Save", command=self.handle_submit)
        self.save_button.pack()

        self.arm_button = tk.Button(parent, text="Arm", command=self.handle_arm)
        self.arm_button.pack()
    
    def handle_submit(self):
        off_nadir = self.off_nadir_entry.get()
        area_threshold = self.area_threshold_entry.get()
        consider_pada = self.pada_frame_var.get()
        print(f'Submit: {off_nadir} {area_threshold} {consider_pada}')

    def handle_arm(self):
        print('Arm')
    
    def update_gui(self):
        if self.check_shutdown():
            return
        
        try:
            while not self.inbound_message_queue.empty():
                message = self.inbound_message_queue.get_nowait()
                if isinstance(message, AttitudeMessage):
                    self.yaw_label.config(text=f"Yaw: {message.yaw}")
                    self.pitch_label.config(text=f"Pitch: {message.pitch}")
                    self.roll_label.config(text=f"Roll: {message.roll}")
                elif isinstance(message, PositionMessage):
                    self.lat_label.config(text=f"Lat: {message.lat}")
                    self.lon_label.config(text=f"Lon: {message.lon}")
                    self.hdg_label.config(text=f"Hdg: {message.hdg}")
                elif isinstance(message, VideoMessage):
                    img = self.cv2totk(message.img)
                    self.image_label.config(image=img, borderwidth=0, padx=0, pady=0)
                    self.image_label.image = img  # Keep a reference, prevent garbage-collection
                elif isinstance(message, PointMessage):
                    self.add_point(message)
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

    def set_centre(self, lat, lon):
        print(lat, lon, self.centre_pos[0], self.centre_pos[1])
        self.centre_pos = (lat, lon)
        self.map_widget.set_position(self.centre_pos[0], self.centre_pos[1])
    
    def cv2totk(self, cv2_img):
        # Calculate the desired size based on the parent's width and the image's aspect ratio
        self.camera_frame.update_idletasks()  # Make sure parent's width is up to date
        desired_width = int(self.camera_frame.winfo_width() / 2)
        (original_height, original_width) = cv2_img.shape[:2]
        aspect_ratio = original_height / original_width
        desired_height = int(desired_width * aspect_ratio)

        # Resize image to fit the width of the cell and maintain aspect ratio
        cv2_img_resized = cv2.resize(cv2_img, (desired_width, desired_height))

        # rearrange color channels
        cv2_img_resized = cv2.cvtColor(cv2_img_resized, cv2.COLOR_BGR2RGB)

        # Convert CV2 image to Image
        pil_image = Image.fromarray(cv2_img_resized)

        # Convert Image to TkPhoto
        return ImageTk.PhotoImage(pil_image)
    
    def create_circle_image(self, size):
        circle_image = tk.PhotoImage(width=size, height=size)
        center_x, center_y = size // 2, size // 2
        radius = min(center_x, center_y) - 1

        # TODO: make a separate image for each target colour

        # Use the put method to draw a red circle
        for x in range(size):
            for y in range(size):
                if (x - center_x)**2 + (y - center_y)**2 <= radius**2:
                    circle_image.put("red", (x, y))
        return circle_image
