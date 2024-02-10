import tkinter as tk
from threading import Thread
from Application import Application
import argparse
from Telemetry import Telemetry
from Video import Video
from TargetDetect import TargetDetect
from Message import PositionMessage, VideoMessage

def parse_args():
    parser = argparse.ArgumentParser(description="Analyze PADA video and telemetry to attempt lamding at markers")
    parser.add_argument('MAV', type=str, help="The connection URL to connect to for mavlink messages (eg. udpin:127.0.0.1:5001)")
    parser.add_argument('STREAM', type=str, help="The connection URL to use for the RTMP stream (eg. rtmp://localhost:1935/live/test)")

    args = parser.parse_args()

    return args

def algorithm_thread(app, tlm, video, detect):
    first_set_gps = True

    while not app.shutdown_event.is_set():
        while not tlm.telemetry_queue.empty():
                msg = tlm.telemetry_queue.get_nowait()
                if(msg is not None):
                    app.inbound_message_queue.put(msg)

                    if (isinstance(msg, PositionMessage) and first_set_gps and msg.lat != 0 and msg.lon != 0):
                        app.set_centre(msg.lat, msg.lon)
                        first_set_gps = False

        frame = video.get_frame()

        if(frame is None):
            print("Video stream complete")
            break

        app.inbound_message_queue.put(VideoMessage(img=frame))

        centroids, _ = detect.detect(frame)

    tlm.shutdown_event.set()
    app.shutdown_event.set()
    print('Closing video')

    print('Telemetry thread recevied shutdown signal')




def main():

    args = parse_args()

    try:
        tlm = Telemetry(args.MAV, conn_print=True, debug_print=True)
        video = Video(args.STREAM, debug_print=True)
        detect = TargetDetect()
    except Exception as err:
        print(err)
        exit(0)

    app = Application()

    # Start the algorithm in its own thread
    algorithm = Thread(target=algorithm_thread, args=(app, tlm, video, detect))
    algorithm.start()

    app.root.mainloop()

    # After the mainloop ends, ensure the background thread is also stopped
    algorithm.join()

if __name__ == "__main__":
    main()
