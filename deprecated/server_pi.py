from flask import Flask, Response, request, jsonify, render_template
import threading
import time
from frames import Frames  # Import shared object
import os

def create_flask_app(frames):
    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')

    # Make sure templates directory exists
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)

    def generate_frames(frame_type):
        """Serves requested frames from shared object"""
        while True:
            frame = frames.get_frame(frame_type)
            if frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.01)  # Adjust frame rate
    
    @app.route('/video_feed/<frame_type>')
    def video_feed_dynamic(frame_type):
        """Provides live video feed for different frame types"""
        return Response(generate_frames(frame_type), 
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    
    @app.route('/')
    def landing_page():
        """Landing page with tabs for scanning and calibration"""
        return render_template("index.html")
    
    @app.route('/api/calibration/start', methods=['POST'])
    def start_calibration():
        """API endpoint to start calibration"""
        # Here you would add code to start the calibration process
        return jsonify({"success": True})
    
    @app.route('/api/calibration/capture', methods=['POST'])
    def capture_calibration():
        """API endpoint to capture a calibration frame"""
        # Here you would add code to capture a calibration frame
        return jsonify({"success": True})
    
    @app.route('/api/calibration/stop', methods=['POST'])
    def stop_calibration():
        """API endpoint to stop calibration"""
        # Here you would add code to stop the calibration process
        return jsonify({"success": True})

    return app

def run_flask(frames):
    """Run Flask server"""
    app = create_flask_app(frames)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)