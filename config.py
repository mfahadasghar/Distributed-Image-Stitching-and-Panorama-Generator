import os

class Config:
    """Configuration settings for the application"""

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Upload settings
    UPLOAD_FOLDER = 'uploads'
    OUTPUT_FOLDER = 'outputs'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff'}

    # Image stitching settings
    MIN_MATCH_COUNT = 10  # Minimum number of good matches required
    FEATURE_DETECTOR = 'SIFT'  # Options: SIFT, ORB, AKAZE
    RANSAC_THRESHOLD = 5.0

    # Parallel processing settings
    MAX_WORKERS = os.cpu_count() or 4  # Number of parallel workers
    CHUNK_SIZE = 2  # Number of images to process in each chunk

    # Progress tracking
    ENABLE_PROGRESS_TRACKING = True

    @staticmethod
    def init_app(app):
        """Initialize application with config"""
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
