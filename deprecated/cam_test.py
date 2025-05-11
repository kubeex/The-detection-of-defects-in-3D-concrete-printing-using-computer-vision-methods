from picamera2 import Picamera2

picam2 = Picamera2()
picam2.configure(picam2.create_still_configuration(main={"size": (4056, 3040)}))
picam2.start()
picam2.capture_file("full_sensor.jpg")
