import threading
import cv2
import time

class SharedData:
    def __init__(self):
        self.lock = threading.Lock()
        self.primary_frame = None
        self.secondary_frame = None
        self.primary_jpeg = None
        self.secondary_jpeg = None
        self.measurements = {
            'width': -1000,
            'height': -1000,
            'quality': False,
            'status': ""
        }

    def update_measurements(self, width, height, quality_bool,status):
        with self.lock:
            # print(f"📡 Updating measurement at {time.time()} w={width:.2f}, h={height:.2f}")
            self.measurements = {
                'width': width,
                'height': height,
                'quality': quality_bool,
                'status':status
            }
    
    def get_measurements(self):
        
        return self.measurements.copy()  # return a safe copy

    def update_frames(self, primary_frame, secondary_frame=None):
        with self.lock:
            self.primary_frame = primary_frame.copy()

        _, buffer = cv2.imencode('.jpg', cv2.cvtColor(self.primary_frame, cv2.COLOR_BGR2RGB))
        self.primary_jpeg = buffer.tobytes()

        if secondary_frame is not None:
            with self.lock:
                self.secondary_frame = secondary_frame.copy()
            _, buffer = cv2.imencode('.jpg', cv2.cvtColor(self.secondary_frame, cv2.COLOR_BGR2RGB))
            self.secondary_jpeg = buffer.tobytes()

    def generate_primary_stream(self):
        while True:
            with self.lock:
                frame_bytes = self.primary_jpeg
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.03)  # 30 FPS max

    def generate_secondary_stream(self):
        while True:
            with self.lock:
                frame_bytes = self.secondary_jpeg
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.03)

            