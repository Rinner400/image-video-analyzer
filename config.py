import torch
import os
from pathlib import Path

class Config:
    """Configuration for Image & Video Analyzer"""
    
    # ==================== Model Configuration ====================
    # Image Captioning
    IMAGE_CAPTION_MODEL = "Salesforce/blip-image-captioning-large"
    # IMAGE_CAPTION_MODEL = "Salesforce/blip-image-captioning-base"  # Faster alternative
    
    # Object Detection
    OBJECT_DETECTION_MODEL = "facebook/detr-resnet50"
    # OBJECT_DETECTION_MODEL = "facebook/detr-resnet50-panoptic"  # For panoptic segmentation
    
    # Visual Similarity (CLIP)
    CLIP_MODEL = "openai/clip-vit-base-patch32"
    # CLIP_MODEL = "openai/clip-vit-large-patch14"  # Larger, more accurate
    
    # ==================== Processing Configuration ====================
    # Video Processing
    MAX_VIDEO_FRAMES = 30  # Maximum frames to extract from video
    VIDEO_SAMPLE_FPS = 2   # Frames per second to sample
    MIN_VIDEO_DURATION = 0.5  # Minimum video duration in seconds
    
    # Object Detection
    CONFIDENCE_THRESHOLD = 0.5  # Min confidence for detected objects
    MAX_OBJECTS = 10  # Maximum objects to report
    
    # Image Processing
    IMAGE_SIZE = 224  # Standard image size for models
    MAX_ASPECT_RATIO = 4.0  # Max aspect ratio for images
    
    # ==================== Hardware Configuration ====================
    # Device Selection
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    USE_GPU = torch.cuda.is_available()
    
    # Memory Management
    BATCH_SIZE = 1
    NUM_WORKERS = 4
    
    # ==================== File Upload Configuration ====================
    # Upload Limits
    MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
    MAX_BATCH_ITEMS = 50  # Max items in batch request
    
    # Allowed File Types
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm'}
    
    # ==================== Flask Configuration ====================
    # Flask Settings
    FLASK_DEBUG = False
    FLASK_PORT = 5000
    FLASK_HOST = "0.0.0.0"
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # Upload Folder
    UPLOAD_FOLDER = Path("uploads")
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    
    # Results Folder
    RESULTS_FOLDER = Path("results")
    RESULTS_FOLDER.mkdir(exist_ok=True)
    
    # ==================== Logging Configuration ====================
    LOG_LEVEL = "INFO"
    LOG_FILE = "analyzer.log"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ==================== Cache Configuration ====================
    CACHE_MODELS = True
    HF_CACHE_DIR = os.environ.get("HF_HOME", "./models_cache")
    
    # ==================== Output Configuration ====================
    OUTPUT_FORMATS = ['json', 'txt', 'csv']
    DEFAULT_OUTPUT_FORMAT = 'json'
    
    # ==================== Timeout Configuration ====================
    IMAGE_TIMEOUT = 60  # seconds
    VIDEO_TIMEOUT = 300  # seconds
    
    @classmethod
    def get_device(cls):
        """Get the compute device (cuda or cpu)"""
        return torch.device(cls.DEVICE)
    
    @classmethod
    def print_config(cls):
        """Print current configuration"""
        print("\n=== Configuration ===")
        print(f"Device: {cls.DEVICE}")
        print(f"GPU Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"GPU Name: {torch.cuda.get_device_name(0)}")
            print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        print(f"Image Caption Model: {cls.IMAGE_CAPTION_MODEL}")
        print(f"Object Detection Model: {cls.OBJECT_DETECTION_MODEL}")
        print(f"Max Video Frames: {cls.MAX_VIDEO_FRAMES}")
        print(f"Video Sample FPS: {cls.VIDEO_SAMPLE_FPS}")
        print(f"Max Image Size: {cls.MAX_IMAGE_SIZE / 1024 / 1024}MB")
        print(f"Max Video Size: {cls.MAX_VIDEO_SIZE / 1024 / 1024}MB")
        print("=" * 25 + "\n")
