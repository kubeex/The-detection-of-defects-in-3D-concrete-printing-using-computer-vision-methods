document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and content
            tabButtons.forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and its content
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Calibration button functionality
    const startButton = document.getElementById('start-calibration');
    const captureButton = document.getElementById('capture-frame');
    const stopButton = document.getElementById('stop-calibration');
    
    if (startButton && captureButton && stopButton) {
        startButton.addEventListener('click', function() {
            // Show capture and stop buttons, hide start button
            startButton.style.display = 'none';
            captureButton.style.display = 'flex';
            stopButton.style.display = 'flex';
            
            // Here you would add code to start the calibration process
            console.log('Calibration started');
        });
        
        captureButton.addEventListener('click', function() {
            // Here you would add code to capture a calibration frame
            console.log('Frame captured');
        });
        
        stopButton.addEventListener('click', function() {
            // Show start button, hide capture and stop buttons
            startButton.style.display = 'flex';
            captureButton.style.display = 'none';
            stopButton.style.display = 'none';
            
            // Here you would add code to stop the calibration process
            console.log('Calibration stopped');
        });
    }
});