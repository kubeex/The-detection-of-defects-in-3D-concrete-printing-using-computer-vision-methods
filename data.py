import csv
import os
from datetime import datetime
import threading
import cv2
import time

class DataLogger:
    def __init__(self, config):
        """
        :param base_folder: Hlavní složka pro uložení všech měření.
        :param filename: Název CSV souboru.
        :param save_interval_frames: Po kolika snímcích ukládat (volitelné).
        :param save_interval_time: Minimální čas mezi ukládáním v sekundách (volitelné).
        """
        self.base_folder = config['output_path']
        self.filename = 'measurements.csv'
        self.save_interval_time = config['save_interval_time']
        self.buffer = []
        self.counter = 0
        self.last_save_time = datetime.now()
        
        self._setup_folders()
        self.filepath = os.path.join(self.task_folder, self.filename)
        
        with open(self.filepath, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                'timestamp', 'x_position', 'y_position', 'z_position',
                'layer_width', 'layer_height', 'defect_detected'
            ])
    
    def _setup_folders(self):
        """Creates new folder for every new task"""
        if not os.path.exists(self.base_folder):
            os.makedirs(self.base_folder)
        
        # Generating folder name
        now = datetime.now()
        folder_name = f"task_{now.day:02d}_{now.month:02d}_{now.year}_{now.hour}_{now.minute}"
        self.task_folder = os.path.join(self.base_folder, folder_name)
        
        os.makedirs(self.task_folder, exist_ok=True)
    
    def log(self, coords, width, height, quality_ok):
        """
        Adds new log to the buffer
        :param coords: list with x,y,z coordinates 
        :param width: meassured width 
        :param height: emassured height 
        :param quality_ok: quality bool
        """
        x,y,z = coords
        timestamp = datetime.now()
        record = [
            timestamp.isoformat(),
            x, y, z,
            width, height,
            quality_ok
        ]
        
        should_save = False
        
        # Time set interval of saving 
        if self.save_interval_time is not None:
            elapsed_time = (timestamp - self.last_save_time).total_seconds()
            if elapsed_time >= self.save_interval_time:
                should_save = True
                self.last_save_time = timestamp
        
        if should_save:
            self.buffer.append(record)
            with open(self.filepath, mode='a', newline='') as file:
                for row in self.buffer:
                    writer = csv.writer(file)
                    writer.writerow(row)
                self.buffer.clear()
        else:
            self.buffer.append(record)
    
    def flush(self):
        """Saves all buffered records to the file at once. For ending the task."""
        if not self.buffer:
            return
        
        with open(self.filepath, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(self.buffer)
        
        self.buffer.clear()



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
