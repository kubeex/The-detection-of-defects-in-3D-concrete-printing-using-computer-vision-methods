import cv2
import numpy as np
from time import time
from data import SharedData  # Import shared object

class Scanner:
    def __init__(self,camera):
        self.D = 142   #[mm] distance parameter betweeeb center of the laser ant the inlet point of the lens 
        self.alpha = np.radians(51) #[deg]angle of the camera with common plane 
        self.camera = camera 
        self.frame_dimensions = np.array([self.camera.width,self.camera.height])
        self.frame_center = self.frame_dimensions //2
        self.K = [self.camera.sensor_size[0]/self.frame_dimensions[0], self.camera.sensor_size[1]/self.frame_dimensions[1]]
        self.laser = LaserLine()
        self.vertical_constant = 45

    def calculate_real_coords_on_sensor(self,pixel_coords):
        """
        Computes real coordinates of the point on the sensor from know sensor size and 2D frame coordinates
        """
        
        cx_px = self.camera.principal_point_new[0]
        cy_px = self.camera.principal_point_new[1]
        centered_x = -pixel_coords[0] + cx_px
        centered_y = -pixel_coords[1] + cy_px

        # centered_x = -pixel_coords[0]+self.frame_center[0]
        # centered_y = -pixel_coords[1]+self.frame_center[1]

        # print(centered_x,centered_y)
        real_x = centered_x * self.K[0]
        real_y = centered_y * self.K[1]
        return real_x, real_y

    
    def calculate_profile_3D_coordinates(self, profile_curve):
        """
        Computes 3D coordinates of the profile curve.
        param profile_curve: array of 2D coordinates of points forming the curve
        
        Returns:
        """
        profile_points_3D = []
        for point in profile_curve:
            self.calculate_3D_coordinates(point)
            profile_points_3D.append(self.calculate_3D_coordinates(point))
        return np.array(profile_points_3D)

    def calculate_3D_coordinates(self,pixel_coords):
        """
        Computes x, y, and z coordinates of one point
        Returns:
        - (x, y, z): 3D coordinates
        """
        # print(self.camera.focal_lengths_mm)
        # print(self.camera.principal_point_mm)

        self.f_x =  self.camera.focal_lengths_new_mm[0]
        self.f_y = self.camera.focal_lengths_new_mm[1]
        # self.f_y = self.camera.focal_lengths_mm[1]
        # self.f_x =  self.camera.focal_lengths_mm[0]
        # self.f = (self.f_x + self.f_y)/2

        # self.f_x =  8.8
        # self.f_y = 8.8


        self.f_y = 9.08
        cx_mm = self.camera.principal_point_new_mm[0]
        cy_mm = self.camera.principal_point_new_mm[1]

        x_k, y_k = self.calculate_real_coords_on_sensor(pixel_coords)
        #Compute z
        z = self.D * np.tan(self.alpha - np.arctan2(y_k,self.f_y))

        angle_diff = self.alpha - np.arctan2(y_k, self.f_y)

        # # Compute x        
        # x_zlomek = x_k/(self.f_y*np.sin(self.alpha)-y_k*np.cos(self.alpha))
        # x = z*x_zlomek

        x_zlomek = x_k/(self.f_y*np.cos(self.alpha)+y_k*np.sin(self.alpha))
        x = self.D*x_zlomek

        y =  0

        return x, y, z


    def measure_width_height(self,frame):   
        """
        Function to measure width and height of the laser line
        """         
        if frame is not None:
            laser_lines_mask = self.laser.extract_mask(frame)
            contours, _ = cv2.findContours(laser_lines_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            # print(self.laser.get_hsv_values())
            if len(contours) > 0:
                curve_points = self.laser.get_curve_points(contours)
                cv2.polylines(frame, [curve_points], isClosed=False, color=(0, 255, 0), thickness=2) #draw detected profile of the laser line
                
                # if False:
                if curve_points is not None:
                    #Find extrems of x coordinates - boundary points - measure width and height
                    min_x_point = curve_points[curve_points[:,0].argmin()]
                    max_x_point = curve_points[curve_points[:,0].argmax()]
                    reaL_coords_min = self.calculate_3D_coordinates(min_x_point)
                    reaL_coords_max = self.calculate_3D_coordinates(max_x_point)
                    draw_point_with_2d_3d_coords(frame,min_x_point,reaL_coords_min)
                    draw_point_with_2d_3d_coords(frame,max_x_point,reaL_coords_max)
                    width = reaL_coords_min[0] - reaL_coords_max[0]
                    height = (reaL_coords_max[2]+reaL_coords_min[2])/2 + self.vertical_constant #calculate average height of the laser line
                    
                
                else:
                    width = None
                    height = None
                # rgb_msk = cv2.cvtColor(laser_lines_mask, cv2.COLOR_GRAY2BGR)
                # laser_lines_mask = cv2.drawContours(rgb_msk, contours, -1, (0, 255, 0),2)
                # laser_lines_mask =  cv2.polylines(rgb_msk, [curve_points], isClosed=False, color=(0, 255, 0), thickness=2)

                return width, height, frame, laser_lines_mask

        return None, None, frame, None


    def measure_profile(self,frame):  
        """
        Function to measure the profile of the laser line in the frame.
        Returns:
        - profile_points_3D: 3D coordinates of the profile points
        - frame: The frame with the laser line drawn on it
        - laser_lines_mask: The mask of the laser line
        """

        if frame is not None:
            laser_lines_mask = self.laser.extract_mask(frame)
            contours, _ = cv2.findContours(laser_lines_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if len(contours) > 0:
                curve_points = self.laser.get_curve_points(laser_lines_mask)
                cv2.polylines(frame, [curve_points], isClosed=False, color=(0, 255, 0), thickness=2) #draw detected profile of the laser line

                if curve_points is not None:
                    profile_points_3D = self.calculate_profile_3D_coordinates(curve_points)
                else:
                    profile_points_3D = None
    
                return profile_points_3D, frame, laser_lines_mask

        return None, None, frame, None

        

class LaserLine:

    def __init__(self):
        #Threshold params for thresholding the laser line out of the frame depending on the color, may be auto in the future
        #Red is in the hsv in this  <0,10> a <160,180>
        self.low_red1 = np.array([0,125, 75])   
        self.high_red1= np.array([20, 255, 255])
        self.low_red2 = np.array([160, 125, 75])
        self.high_red2 = np.array([180, 255, 255])
        
        #Hough transform parameters
        self.rho = 1                #pixel resolution 1..every pixel is considered
        self.theta = 5*np.pi / 180    #angle resolution 
        self.point_threshold = 50   #minimum number of points to consider a line 
        self.minLineLength = 30     #min length of the line 
        self.maxLineGap = 10        #Merges close line segments into one
    
    def extract_mask(self,frame):
        """
        Function to extract red laser line from the frame 
        now with hardcoded threshold values
        """
        hsv = cv2.cvtColor(frame,cv2.COLOR_RGB2HSV)
        
        mask1 = cv2.inRange(hsv, self.low_red1, self.high_red1) # Maska in the lower spectrum of the hsv
        mask2 = cv2.inRange(hsv, self.low_red2, self.high_red2) # Mask in the upper spectrum of the hsv
        # Combine masks
        mask = cv2.bitwise_or(mask1, mask2)
        return mask 
    
    # def get_curve_points(self,line_mask,polynom=2):
    #     contours, _ = cv2.findContours(line_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #     # Set minimum length threshold
    #     min_length = 100

    #     # Calculate perimeters for all contours at once
    #     perimeters = np.array([cv2.arcLength(cnt, closed=False) for cnt in contours])

    #     # Create a boolean mask of contours that meet the length requirement
    #     mask = perimeters >= min_length

    #     # Filter the contours using the mask
    #     filtered_contours = [contours[i] for i in np.where(mask)[0]]
    #     contours = sorted(filtered_contours, key=lambda c: cv2.boundingRect(c)[1]) #Sorting the contours by y position in the frame
    #     if len(contours) >0:
    #         highest_contour = contours[0]   #Getting only the highest positioned contour - profile should be the highest point laser touches
    #         x = highest_contour[:, :, 0].flatten()
    #         y = highest_contour[:, :, 1].flatten()
    #         poly = np.poly1d(np.polyfit(x, y, polynom))
    #         self.curve_points = np.array([[_x, int(poly(_x))] for _x in range(min(x), max(x), 5)], dtype=np.int32)
    #         return self.curve_points
    #     else:
    #         return None

    def get_curve_points(self,contours):
        # contours, _ = cv2.findContours(line_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        min_length = 100

        perimeters = np.array([cv2.arcLength(cnt, closed=False) for cnt in contours])
        mask = perimeters >= min_length
        filtered_contours = [contours[i] for i in np.where(mask)[0]]
        contours = sorted(filtered_contours, key=lambda c: cv2.boundingRect(c)[1])  # Sort by y

        if len(contours) > 0:
            highest_contour = contours[0] 
            bottom_points = {}
            for pt in highest_contour:
                x, y = pt[0]
                if x not in bottom_points or y > bottom_points[x]:
                    bottom_points[x] = y

            # Now sort points by x
            sorted_bottom_curve = np.array([[x, bottom_points[x]] for x in sorted(bottom_points.keys())], dtype=np.int32)

            # Převod na np array
            self.curve_points = np.array(sorted_bottom_curve, dtype=np.int32).reshape((-1, 2))

            return self.curve_points
        else:
            return None


    def get_hsv_values(self):
        """
        Get the HSV values for the laser line.
        :return: A dictionary of HSV values.
        """
        return {
            "low_red1": self.low_red1.tolist(),
            "high_red1": self.high_red1.tolist(),
            "low_red2": self.low_red2.tolist(),
            "high_red2": self.high_red2.tolist()
        }

    def update_hsv_values(self,values):
        """
        Get the HSV values for the laser line.
        :return: A dictionary of HSV values.
        """
        self.low_red1 = np.array(values["low_red1"])
        self.high_red1 = np.array(values["high_red1"])
        self.low_red2 = np.array(values["low_red2"])
        self.high_red2 = np.array(values["high_red2"])
            




def draw_point_with_2d_3d_coords(frame, point_2d, point_3d, point_color=(0, 0, 255), text_color=(255, 255, 255),
                               point_radius=5, font_scale=0.5, thickness=2):
    """
    Draw a point on the frame with both 2D and 3D coordinates shown as text.
    Text is placed to the left of the point to avoid edge issues.
    
    Args:
        frame: The frame on which to draw
        point_2d: 2D coordinates (x, y) of the point
        point_3d: 3D coordinates (X, Y, Z) of the corresponding point
        point_color: Color of the circle (BGR format)
        text_color: Color of the text (BGR format)
        point_radius: Radius of the circle
        font_scale: Font scale for the text
        thickness: Thickness of the circle and text
        
    Returns:
        The frame with the point and text drawn on it
    """
    h,w = frame.shape[:2]
    # Make sure 2D point coordinates are integers
    x, y = int(point_2d[0]), int(point_2d[1])
    
    # Draw the circle at the 2D point
    cv2.circle(frame, (x, y), point_radius, point_color, thickness)
    
    # Get 3D coordinates
    X, Y, Z = point_3d
    
    # Prepare text strings
    text_2d = f"[{x},{y}]"
    text_2d_centered = f"[{x -int((w/2))},{y - int((h/2))}]"
    text_3d = f"[{X:.2f},{Y:.2f},{Z:.2f}]"
    
    # Get text sizes to better place them
    (text_2d_width, text_2d_height), _ = cv2.getTextSize(text_2d, cv2.FONT_HERSHEY_SIMPLEX, 
                                                       font_scale, thickness)
    (text_3d_width, text_3d_height), _ = cv2.getTextSize(text_3d, cv2.FONT_HERSHEY_SIMPLEX, 
                                                       font_scale, thickness)
    
    # Calculate text positions - place text to the left of the point
    # Ensure text doesn't go off the left edge of the frame
    text_x = max(x - text_3d_width - 10, 5)  # 10px left of point, minimum 5px from left edge
    
    # Position 3D text slightly above the point's y-coordinate
    text_3d_y = y - 5
    
    # Position 2D text below the 3D text
    text_2d_y = text_3d_y + text_3d_height + 5
    
    # Draw the texts
    # cv2.putText(frame, text_3d, (text_x, text_3d_y), cv2.FONT_HERSHEY_SIMPLEX,
    #             font_scale, text_color, thickness)
    
    # cv2.putText(frame, text_2d, (text_x, text_2d_y), cv2.FONT_HERSHEY_SIMPLEX,
    #             font_scale, text_color, thickness)

    # cv2.putText(frame, text_2d_centered, (text_x, text_2d_y+text_3d_height + 5), cv2.FONT_HERSHEY_SIMPLEX,
    #             font_scale, text_color, thickness)
    
    return frame

    

if __name__ == "__main__":
    # Create a single shared Frames instance
    capture_and_process(SharedData())
