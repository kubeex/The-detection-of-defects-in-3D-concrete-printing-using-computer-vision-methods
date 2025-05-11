from data import DataLogger
from scanner import Scanner
from time import time, sleep
import cv2
import threading
from printer_communication import PrinterCommunication

class QualityControl:
    def __init__(self,camera,shared_data):
        self.camera = camera
        self.scanner =  Scanner(camera)
        self.shared_data = shared_data
        self.control_thread = None
        self.running = threading.Event()  # Thread control flag
        self.printer = PrinterCommunication(None)  # Placeholder for printer communication
        self.width_target = 100
        self.height_target = 200
        self.max_width_error = 5
        self.max_height_error = 10
        

    def control_loop(self):
        """
        Main control loop for the scanner.
        This method should be called in a separate thread.
        """
        previous_time = time()
        data_logger = DataLogger()
        print("starting control loop thread")
        while self.running.is_set():
            # Capture and process frames
            current_time = time()
            dt = current_time-previous_time
            previous_time = current_time
            fps = 1/dt
            t  = time()
            frame = self.camera.get__undisorted_frame()
            # print("time it takes to get frame",time()-t)
            width, height, frame, laser_lines_mask = self.scanner.measure_width_height(frame)
            cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            # if width is not None and height is not None:
            #     cv2.putText(frame,f"width:{int(width)}",(self.camera.width//2,100),1, 1, (255,255,255),thickness=2)
            #     cv2.putText(frame,f"height:{int(height)}",(self.camera.width//2,130),1, 1, (255,255,255),thickness=2)
    
            # Update shared frames
            quality_bool, status_message = self.evaluate_print_quality(width,height)
            self.shared_data.update_frames(frame, laser_lines_mask)
            self.shared_data.update_measurements(width,height,quality_bool,status_message)
            #Log messured data
            # print(self.get_hsv_values())
            coords = self.printer.get_current_coords()
            data_logger.log(coords, width, height, quality_bool)
            sleep(0.01)
    
    def start_measurement(self):
        """
        Start the control loop in a separate thread.
        """
        print(f"Thread check: control_thread={self.control_thread}, alive={self.control_thread.is_alive() if self.control_thread else 'None'}")
        if self.control_thread is None or not self.control_thread.is_alive():
            self.running.set()
            self.control_thread = threading.Thread(target=self.control_loop)
            self.control_thread.start()

    def stop_measurement(self):
        """
        End the control loop.
        """
        if self.control_thread is not None:
            self.running.clear()
            self.control_thread.join()
            self.control_thread = None

    def evaluate_print_quality(self, width, height):
        width_error = False
        height_error = False
        status_messages = []

        # Width evaluation
        if width is not None:
            if width > self.width_target + self.max_width_error:
                width_error = True
                status_messages.append(
                    "Vrstva je příliš široká:\n"
                    "- Možná nadměrná extruze\n"
                    "- Ucpávání trysky\n"
                    "- Nestabilní podklad tisku"
                )
            elif width < self.width_target - self.max_width_error:
                width_error = True
                status_messages.append(
                    "Vrstva je příliš úzká:\n"
                    "- Možná nedostatečná extruze\n"
                    "- Blokace materiálu\n"
                    "- Nesprávná rychlost podávání"
                )

        # Vyhodnocení výšky
        if height is not None:
            if height > self.height_target + self.max_height_error:
                height_error = True
                status_messages.append(
                    "Vrstva je příliš vysoká:\n"
                    "- Nerovný podklad\n"
                    "- Problém s kalibrací osy Z\n"
                    "- Nadměrný tok materiálu"
                )
            elif height < self.height_target - self.max_height_error:
                height_error = True
                status_messages.append(
                    "Vrstva je příliš nízká:\n"
                    "- Nedostatečná extruze\n"
                    "- Tryska příliš blízko předchozí vrstvy\n"
                    "- Usazování materiálu"
        )


        quality_ok = not (width_error or height_error)
        status = "OK" if quality_ok else "\n\n".join(status_messages)

        return quality_ok, status

    
    def get_hsv_values(self):
        return self.scanner.laser.get_hsv_values()

    def update_hsv_values(self,values):
        self.scanner.laser.update_hsv_values(values)
    
    def get_meassurement_thresholds(self):
        return {
            "width_target": self.width_target,
            "height_target": self.height_target,
            "max_width_error": self.max_width_error,
            "max_height_error": self.max_height_error
        }

    def update_measurement_thresholds(self,values):
        self.width_target = values["width_target"]
        self.height_target = values["height_target"]
        self.max_width_error = values["max_width_error"]
        self.max_height_error = values["max_height_error"]