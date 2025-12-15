from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
import threading
from datetime import datetime
from config import Config
from image_stitcher import DistributedImageStitcher

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Enable CORS and WebSocket
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Store active stitching jobs
active_jobs = {}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Handle file uploads"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files')

    if len(files) < 2:
        return jsonify({'error': 'At least 2 images are required for stitching'}), 400

    # Create a unique job ID
    job_id = str(uuid.uuid4())
    job_folder = os.path.join(Config.UPLOAD_FOLDER, job_id)
    os.makedirs(job_folder, exist_ok=True)

    # Save uploaded files
    uploaded_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(job_folder, filename)
            file.save(filepath)
            uploaded_files.append(filepath)

    if len(uploaded_files) < 2:
        return jsonify({'error': 'Invalid files. Please upload at least 2 valid images.'}), 400

    # Store job info
    active_jobs[job_id] = {
        'id': job_id,
        'status': 'uploaded',
        'files': uploaded_files,
        'created_at': datetime.now().isoformat(),
        'progress': 0
    }

    return jsonify({
        'job_id': job_id,
        'num_files': len(uploaded_files),
        'message': 'Files uploaded successfully'
    })


@app.route('/api/stitch/<job_id>', methods=['POST'])
def start_stitching(job_id):
    """Start the stitching process for a job"""
    if job_id not in active_jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = active_jobs[job_id]

    if job['status'] == 'processing':
        return jsonify({'error': 'Job is already processing'}), 400

    # Get feature detector from request
    data = request.get_json() or {}
    feature_detector = data.get('feature_detector', 'SIFT')

    # Update job status
    job['status'] = 'processing'
    job['progress'] = 0

    # Start stitching in a background thread
    thread = threading.Thread(
        target=process_stitching,
        args=(job_id, job['files'], feature_detector)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'message': 'Stitching started',
        'job_id': job_id
    })


def process_stitching(job_id, image_paths, feature_detector):
    """Background task to process image stitching"""
    try:
        # Progress callback to emit updates via WebSocket
        def progress_callback(progress_data):
            progress_data['job_id'] = job_id
            socketio.emit('progress_update', progress_data)

            # Update job progress
            if job_id in active_jobs:
                active_jobs[job_id]['progress'] = progress_data.get('percent', 0)

        # Create stitcher
        stitcher = DistributedImageStitcher(
            feature_detector=feature_detector,
            progress_callback=progress_callback
        )

        # Process stitching
        output_filename = f'panorama_{job_id}.jpg'
        output_path = os.path.join(Config.OUTPUT_FOLDER, output_filename)

        stats = stitcher.stitch_and_save(image_paths, output_path)

        # Update job with results
        if job_id in active_jobs:
            active_jobs[job_id]['status'] = 'completed'
            active_jobs[job_id]['output'] = output_filename
            active_jobs[job_id]['stats'] = stats
            active_jobs[job_id]['progress'] = 100

        # Emit completion event
        socketio.emit('stitch_complete', {
            'job_id': job_id,
            'output': output_filename,
            'stats': stats
        })

    except Exception as e:
        # Handle errors
        error_msg = str(e)
        if job_id in active_jobs:
            active_jobs[job_id]['status'] = 'failed'
            active_jobs[job_id]['error'] = error_msg

        socketio.emit('stitch_error', {
            'job_id': job_id,
            'error': error_msg
        })


@app.route('/api/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get the status of a stitching job"""
    if job_id not in active_jobs:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(active_jobs[job_id])


@app.route('/api/result/<filename>')
def get_result(filename):
    """Serve the stitched panorama image"""
    filepath = os.path.join(Config.OUTPUT_FOLDER, filename)

    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    return send_file(filepath, mimetype='image/jpeg')


@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all jobs"""
    jobs_list = [{
        'id': job_id,
        'status': job['status'],
        'progress': job.get('progress', 0),
        'created_at': job.get('created_at'),
        'num_files': len(job.get('files', []))
    } for job_id, job in active_jobs.items()]

    return jsonify({'jobs': jobs_list})


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'message': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')


if __name__ == '__main__':
    print("=" * 60)
    print("Distributed Image Stitching and Panorama Generator")
    print("=" * 60)
    print(f"Feature Detector: {Config.FEATURE_DETECTOR}")
    print(f"Max Workers: {Config.MAX_WORKERS}")
    print(f"Upload Folder: {Config.UPLOAD_FOLDER}")
    print(f"Output Folder: {Config.OUTPUT_FOLDER}")
    print("=" * 60)
    print("\nStarting server on http://127.0.0.1:5000")
    print("Press CTRL+C to quit\n")

    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
