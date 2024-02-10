import tkinter as tk
from threading import Thread
import time
from Application import Application
from Message import TelemetryMessage, ParamsMessage, PointMessage
import geocoder
import random

def jitter(x):
    MAX = 0.0009
    MIN = -0.0009
    return x + random.uniform(MIN, MAX)

def algorithm_thread(app):
    yaw, pitch, roll = 0, 0, 0
    g = geocoder.ip('me')
    pos = g.latlng
    centre_pos = (float(pos[0]), float(pos[1]))
    while not app.shutdown_event.is_set():
        # Simulate processing
        yaw += 1
        pitch += 1
        roll += 1

        # Send data to the GUI
        app.inbound_message_queue.put(TelemetryMessage(yaw=yaw, pitch=pitch, roll=roll))
        app.inbound_message_queue.put(PointMessage(
            colour='red',
            x=0,
            y=0,
            width=1,
            height=1,
            lat=jitter(centre_pos[0]),
            lon=jitter(centre_pos[1]),
        ))

        # Check for commands from the GUI
        if not app.outbound_message_queue.empty():
            message = app.outbound_message_queue.get_nowait()
            if isinstance(message, ParamsMessage):
                print(f'Algo received params: {message}')
            else:
                print(f'Algo received unknown message: {type(message)}')
        
        time.sleep(0.5)

        # shutdown algo and GUI with app.shutdown_event.set()

    print('Telemetry thread recevied shutdown signal')

if __name__ == "__main__":
    app = Application()

    # Start the algorithm in its own thread
    algorithm = Thread(target=algorithm_thread, args=(app,))
    algorithm.start()

    app.root.mainloop()

    # After the mainloop ends, ensure the background thread is also stopped
    algorithm.join()
