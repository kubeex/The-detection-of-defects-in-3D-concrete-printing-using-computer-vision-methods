import threading
import time
import yaml
from data import SharedData
from UI.server import run_flask
from camera import Camera, Calibration
from scanner import Scanner
from quality_control import QualityControl


with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

if __name__ == "__main__":
    # Create a single shared Frames instance

    shared_frames = SharedData()
    camera = Camera(config)
    controller = QualityControl(camera,shared_frames,config)
    if config["mode"] != 'headless':
        calibration = Calibration(camera,shared_frames,config)
        thread_flask = threading.Thread(target=run_flask, args=(shared_frames,calibration,controller,config), daemon=True)
        thread_flask.start()
    
    else:
        print("Starting headless meassurement.")
        controller.start_measurement()
        