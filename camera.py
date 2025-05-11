from picamera2 import Picamera2
import cv2
import os 
import threading
from threading import Lock
import numpy as np 
from time import sleep, time

data_path = os.path.dirname(os.path.abspath(__file__)) + "/calib/"
class Camera:
    def __init__(self,config=None):
        self.camera = Picamera2()
        print(self.camera.sensor_resolution)
        self.width = 1014
        self.height = 750
        self.sensor_size = [6.287 , 4.712]
        self.config =  self.camera.create_video_configuration(
                main={"size": ( self.width, self.height), "format": "RGB888"},
                controls={"FrameDurationLimits": (16666, 16666)}  # 30 FPS
            )
        self.camera.configure(self.config)
        self.mtx = None
        self.new_mtx = None
        self.dist_coeffs = None
        self.load_calibration_data()
        self.camera.start()
        self.lock = threading.Lock()
        self.latest_frame = self._capture_array()
        self.start_thread()

    def load_calibration_data(self):
        file_path = data_path+'calibration.npz'
        if os.path.exists(file_path):
            print(f"The file {file_path} exists")
            data = np.load(file_path)
            
        
            # Load matrices and coefficients
            self.mtx = data['mtx']
            self.new_mtx = data['new_mtx']
            self.dist_coeffs = data['dist_coeffs']
            
            # Load focal lengths and principal points
            self.focal_lengths = data['focal_lengths']
            self.principal_point = data['principal_point']
            self.focal_lengths_new = data['focal_lengths_new']
            self.principal_point_new = data['principal_point_new']
            
            # Load mm values
            self.focal_lengths_mm = data['focal_lengths_mm']
            self.principal_point_mm = data['principal_point_mm']
            self.focal_lengths_new_mm = data['focal_lengths_new_mm']
            self.principal_point_new_mm = data['principal_point_new_mm']

            print("Calibration data loaded:")
            print("mtx:", self.mtx)
            print("new_mtx:", self.new_mtx)
            print("dist_coeffs:", self.dist_coeffs)
            print("focal_lengths:", self.focal_lengths)
            print("principal_point:", self.principal_point)
            print("focal_lengths_new:", self.focal_lengths_new)
            print("principal_point_new:", self.principal_point_new)
            print("focal_lengths_mm:", self.focal_lengths_mm)
            print("principal_point_mm:", self.principal_point_mm)
            print("focal_lengths_new_mm:", self.focal_lengths_new_mm)
            print("principal_point_new_mm:", self.principal_point_new_mm)
                            

        else:
            print("No calibration data!")

    def _capture_array(self):
        frame = self.camera.capture_array()
        with self.lock:
            self.latest_frame = frame
        return self.latest_frame

    def camera_loop(self):
        print(self.camera.camera_configuration())
        while True:
            self._capture_array()
            sleep(0.02)

    def start_thread(self):
        camera_thread = threading.Thread(target=self.camera_loop)
        camera_thread.start()
        
    def get_frame(self):
        bgr_frame = cv2.cvtColor(self.latest_frame.copy(), cv2.COLOR_RGB2BGR)
        return bgr_frame

    def get__undisorted_frame(self):
        with self.lock:
            bgr_frame = cv2.cvtColor(self.latest_frame.copy(), cv2.COLOR_RGB2BGR)
            if self.mtx is not None:
                undistorted_image = cv2.undistort(
                    bgr_frame, self.mtx, self.dist_coeffs, None, self.new_mtx
                )
                return undistorted_image
                # return bgr_frame


            else:
                return bgr_frame

class Calibration:
    def __init__(self,camera,shared_data,config):
        self.data_path = os.path.dirname(os.path.abspath(__file__)) + "/calib/"
        self.color = (255,255,255)
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.aruco_dict = cv2.aruco.DICT_6X6_250
        self.dictionary = cv2.aruco.getPredefinedDictionary(self.aruco_dict)
        self.paperWidth, self.paperHeight = int(8.27 * 300), int(11.69 * 300)  #definuje velikost A4 pri 300 dpi
        self.board = self.generateChArUcoBoard(filename=None)
        self.charuco_corners = []
        self.charuco_ids = []
        self.camera = camera
        self.lock = Lock()
        
        #Shared bools
        self.caputre_state = False
        self.quit_state = False
        self.shared_data = shared_data
        self.running = threading.Event()
        self.calibration_thread = None  



    def start_calibration(self):
        """
        Start the control loop in a separate thread.
        """
        if self.calibration_thread is None or not self.calibration_thread.is_alive():
            self.running.set()
            self.calibration_thread = threading.Thread(target=self.charlibration)
            self.calibration_thread.start()

    def stop_calibration(self):
        """
        End the control loop.
        """
        if self.calibration_thread is not None:
            self.running.clear()
            self.calibration_thread.join()
            self.calibration_thread = None

    def generateChArUcoBoard(self,squaresX=5, squaresY=7, filename = "charuco_board.png"):
        
        #velikost ctvercu a markeru
        squareLength = int((self.paperWidth-100) / squaresX)
        markerLength = int(squareLength * 0.7)
        # print(f"Square length: {squareLength}")
        # print(f"Marker length: {markerLength}")


        self.board =cv2.aruco.CharucoBoard((squaresX, squaresY), 26, 18, self.dictionary)
        if filename is not None:
            img = self.board.generateImage((self.paperWidth, self.paperHeight))
            cv2.imwrite(self.data_path + filename, img)
            print("Board generated")
        return self.board
        
    def charlibration(self):
        self.charucoCorners = []
        self.charucoIds = []
        self.caputre_state = False
        self.quit_state = False

        while self.running.is_set():
            # print("Charlibration!")
            frame = self.camera.get_frame()
            corners, ids, _ = cv2.aruco.detectMarkers(frame, self.dictionary)
            if len(corners) > 0:
                ret, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(corners, ids, frame, self.board)
                # Pokud je deska nalezena(vic jak 15 rohů)
                if ret > 15:
                    cv2.aruco.drawDetectedCornersCharuco(frame, charuco_corners,charuco_ids)
                    #Vypise text ze deska byla nalezena
                    cv2.putText(frame, 'Board detected', (10, 50),self.font, 1, self.color, 2)
                    #Pokud je stisknuta klavesa 0
                    if self.caputre_state:

                        self.charucoCorners.append(charuco_corners)
                        self.charucoIds.append(charuco_ids)
                        self.caputre_state = False
                else:
                    cv2.putText(frame, 'No board detected', (10, 50),self.font, 1, self.color, 2)

            # Pokud neni nalezen zadny marker vypise text
            else:
                cv2.putText(frame, 'ArUco nedetekovano', (10, 50),self.font, 1, self.color, 2)

            cv2.putText(frame, f'Vzorky: {len(self.charucoCorners)}', (10, 100), self.font, 1, self.color, 2)
            self.shared_data.update_frames(frame)
            #Zobrazeni vysledneho obrazku
            #Pokud je stisknuta klavesa + ukonci se program
            if self.quit_state:
                print('Quitting...')
                break

        self.calculate_camera_matrix()

    def calculate_camera_matrix(self):

        if len(self.charucoCorners) >2:
            print("Calibrating camera...")
            h, w = self.camera.height,self.camera.width
            ret, mtx, dist_coeffs,R,T = cv2.aruco.calibrateCameraCharuco(self.charucoCorners, self.charucoIds, self.board, (w,h), None, None)
            new_mtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist_coeffs, (w,h), 1, (w,h))
            
            fx, fy = mtx[0, 0], mtx[1, 1]
            cx, cy = mtx[0, 2], mtx[1, 2]
            fx_new, fy_new = new_mtx[0, 0], new_mtx[1, 1]
            cx_new, cy_new = new_mtx[0, 2], new_mtx[1, 2]

            # Calculate parameters in mm (using your sensor dimensions)
            sensor_width, sensor_height =self.camera.sensor_size
            fx_mm, fy_mm = fx * (sensor_width / w), fy * (sensor_height / h)
            cx_mm, cy_mm = cx * (sensor_width / w), cy * (sensor_height / h)
            fx_new_mm, fy_new_mm = fx_new * (sensor_width / w), fy_new * (sensor_height / h)
            cx_new_mm, cy_new_mm = cx_new * (sensor_width / w), cy_new * (sensor_height / h)

            # Create parameter lists
            focal_lengths = [fx, fy]
            principal_point = [cx, cy]
            focal_lengths_new = [fx_new, fy_new]
            principal_point_new = [cx_new, cy_new]
            focal_lengths_mm = [fx_mm, fy_mm]
            principal_point_mm = [cx_mm, cy_mm]
            focal_lengths_new_mm = [fx_new_mm, fy_new_mm]
            principal_point_new_mm = [cx_new_mm, cy_new_mm]
            np.savez(self.data_path+'calibration.npz', 
                    mtx=mtx, 
                    dist_coeffs=dist_coeffs, 
                    new_mtx=new_mtx,
                    focal_lengths=focal_lengths,
                    principal_point=principal_point,
                    focal_lengths_new=focal_lengths_new,
                    principal_point_new=principal_point_new,
                    focal_lengths_mm=focal_lengths_mm,
                    principal_point_mm=principal_point_mm,
                    focal_lengths_new_mm=focal_lengths_new_mm,
                    principal_point_new_mm=principal_point_new_mm)
                        
            print("Calibration computation complete!")

            print("mtx:", mtx)
            print("dist_coeffs:", dist_coeffs)
            print("new_mtx:", new_mtx)
            print("focal_lengths:", focal_lengths)
            print("principal_point:", principal_point)
            print("focal_lengths_new:", focal_lengths_new)
            print("principal_point_new:", principal_point_new)
            print("focal_lengths_mm:", focal_lengths_mm)
            print("principal_point_mm:", principal_point_mm)
            print("focal_lengths_new_mm:", focal_lengths_new_mm)
            print("principal_point_new_mm:", principal_point_new_mm)


        else:
            print("Not enough calibration data")



if __name__ == "__main__":
    # Create a single shared Frames instance
    camera = Camera()
    calib = Calibration(camera)
    calib.generateChArUcoBoard()