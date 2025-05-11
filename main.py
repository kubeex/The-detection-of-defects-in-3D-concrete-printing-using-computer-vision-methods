import threading
import time
from data import SharedData
from UI.server import run_flask
from camera import Camera, Calibration
from scanner import Scanner
from quality_control import QualityControl

if __name__ == "__main__":
    # Create a single shared Frames instance
    shared_frames = SharedData()
    camera = Camera()
    calibration = Calibration(camera,shared_frames)
    controller = QualityControl(camera,shared_frames)
    thread_flask = threading.Thread(target=run_flask, args=(shared_frames,calibration,controller), daemon=True)
    thread_flask.start()
