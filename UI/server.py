from flask import Flask, Response, render_template, request,jsonify
import time
import json


def create_flask_app(shared_data,calibration, controller):
    app = Flask(__name__)

    @app.route('/get_hsv_defaults', methods=['GET'])
    def get_hsv_defaults():
        return controller.get_hsv_values()

    # @app.route('/live_measurements')
    # def live_measurements():
    #     start = time.time()
    #     data = shared_data.get_measurements()

    #     print("📡 Getting measurement at", time.time(), data)

    #     # Add this:
    #     import datetime
    #     if data['width'] == -1000:
    #         print("🕗 Measurement data not yet initialized!")
    #     else:
    #         print("✅ Valid measurement received!")

    #     print(f"📡 Responding after {time.time() - start:.3f}s")
    #     return jsonify(data)

    @app.route('/live_measurements_stream')
    def live_measurements_stream():
        def event_stream():
            while True:
                data = shared_data.get_measurements()
                yield f"data: {json.dumps(data)}\n\n"
                time.sleep(0.1)  # adjust as needed (e.g., 0.2s for 5 Hz)

        return Response(event_stream(), mimetype='text/event-stream')

    @app.route('/get_measurement_thresholds', methods=['GET'])
    def get_measurement_thresholds():
        return controller.get_meassurement_thresholds()

    @app.route('/update_measurement_thresholds', methods=['POST'])
    def update_measurement_thresholds():
        data = request.get_json()
        controller.update_measurement_thresholds(data)
        return '', 204

    @app.route('/update_hsv', methods=['POST'])
    def update_hsv_values():
        data = request.get_json()
        controller.update_hsv_values(data)
        return '', 204

    @app.route('/video_feed/primary')
    def video_feed_primary():
        """Provides live video feed for primary frame"""
        return Response(shared_data.generate_primary_stream(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/video_feed/secondary')
    def video_feed_secondary():
        """Provides live video feed for secondary frame"""
        return Response(shared_data.generate_secondary_stream(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    
    @app.route('/capture', methods=['POST'])
    def capture():
        """Handle capture button press."""
        # You can implement your capture logic here
        print("Capture button pressed!")  # Debugging output
        calibration.caputre_state = True

        return "Image captured"

    @app.route('/calibrate', methods=['POST'])
    def calibrate():
        """Handle capture button press."""
        # You can implement your capture logic here
        print("Calibrate button pressed!")  # Debugging output
        calibration.quit_state = True
        
        return "Image captured"

    @app.route('/start_measurement', methods=['POST'])
    def start_measurement():
        print("🔧 Flask received /start_measurement POST")
        controller.start_measurement()
        print("🔧 Measurement thread started at", time.time())

        # Wait briefly and check the shared data
        time.sleep(1)
        m = shared_data.get_measurements()
        # print("🔍 Measurement after 1s:", m)

        return "Measurement started"


    @app.route('/stop_measurement', methods=['POST'])
    def stop_measurement():
        print("Stopping measurement thread...")
        controller.stop_measurement()
        return "Measurement stopped"

    @app.route('/start_calibration', methods=['POST'])
    def start_calibration():
        print("starting calirbation thread...")
        calibration.start_calibration()
        return "Measurement stopped"
    
    @app.route('/stop_calibration', methods=['POST'])
    def stop_calibration():
        print("Stopping calibration thread...")
        calibration.stop_calibration()
        return "Measurement stopped"


    @app.route('/')
    def index():
        """Landing page with dual video streams and capture button"""
        return render_template('index.html')

    return app

def run_flask(shared_data,calibration,controller):
    """Run Flask server"""
    print("Starting Flask server...")
    app = create_flask_app(shared_data,calibration,controller)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)