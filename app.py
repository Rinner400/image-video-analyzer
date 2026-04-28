"""Flask Web Application for Image & Video Analyzer"""

import logging
import os
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename
from config import Config
from analyzer.image_analyzer import ImageAnalyzer
from analyzer.video_analyzer import VideoAnalyzer
from analyzer.utils import save_results, cleanup_old_files

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=Config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

app.config['MAX_CONTENT_LENGTH'] = max(Config.MAX_IMAGE_SIZE, Config.MAX_VIDEO_SIZE)
app.config['UPLOAD_FOLDER'] = str(Config.UPLOAD_FOLDER)
app.secret_key = Config.SECRET_KEY

# Initialize analyzers
config = Config()
image_analyzer = ImageAnalyzer(config)
video_analyzer = VideoAnalyzer(config)

logger.info("Application initialized")

# ==================== Routes ====================

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get available models"""
    return jsonify({
        "image_caption_model": Config.IMAGE_CAPTION_MODEL,
        "object_detection_model": Config.OBJECT_DETECTION_MODEL,
        "clip_model": Config.CLIP_MODEL,
        "device": str(Config.DEVICE),
        "gpu_available": Config.USE_GPU
    })

@app.route('/api/analyze/image', methods=['POST'])
def analyze_image():
    """Analyze image endpoint"""
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Validate file
    if not allowed_file(file.filename, 'image'):
        return jsonify({"error": "Invalid image format"}), 400
    
    try:
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logger.info(f"Image uploaded: {filepath}")
        
        # Analyze
        result = image_analyzer.analyze(filepath)
        
        # Save results
        output_format = request.form.get('format', 'json')
        if result['status'] == 'success':
            save_results(result, filename, output_format)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze/video', methods=['POST'])
def analyze_video():
    """Analyze video endpoint"""
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Validate file
    if not allowed_file(file.filename, 'video'):
        return jsonify({"error": "Invalid video format"}), 400
    
    try:
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logger.info(f"Video uploaded: {filepath}")
        
        # Get parameters
        max_frames = int(request.form.get('max_frames', Config.MAX_VIDEO_FRAMES))
        fps = int(request.form.get('fps', Config.VIDEO_SAMPLE_FPS))
        
        # Analyze
        result = video_analyzer.analyze(filepath, max_frames, fps)
        
        # Save results
        output_format = request.form.get('format', 'json')
        if result['status'] == 'success':
            save_results(result, filename, output_format)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Video analysis error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/batch', methods=['POST'])
def batch_analyze():
    """Batch analysis endpoint"""
    
    if 'files' not in request.files:
        return jsonify({"error": "No files provided"}), 400
    
    files = request.files.getlist('files')
    file_type = request.form.get('type', 'image')
    
    if not files or len(files) == 0:
        return jsonify({"error": "No files selected"}), 400
    
    if len(files) > Config.MAX_BATCH_ITEMS:
        return jsonify({"error": f"Too many files (max {Config.MAX_BATCH_ITEMS})"}), 400
    
    results = []
    
    try:
        for file in files:
            if file.filename == '':
                continue
            
            if not allowed_file(file.filename, file_type):
                results.append({
                    "file": file.filename,
                    "status": "error",
                    "error": "Invalid file format"
                })
                continue
            
            # Save file
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Analyze
            try:
                if file_type == 'image':
                    result = image_analyzer.analyze(filepath)
                else:
                    result = video_analyzer.analyze(filepath)
                results.append(result)
            except Exception as e:
                results.append({
                    "file": file.filename,
                    "status": "error",
                    "error": str(e)
                })
        
        return jsonify({
            "status": "success",
            "total_files": len(files),
            "results": results
        })
    
    except Exception as e:
        logger.error(f"Batch analysis error: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== Utilities ====================

def allowed_file(filename: str, file_type: str = "image") -> bool:
    """Check if file is allowed"""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if file_type == "image":
        return ext in Config.ALLOWED_IMAGE_EXTENSIONS
    elif file_type == "video":
        return ext in Config.ALLOWED_VIDEO_EXTENSIONS
    
    return False

# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({"error": "File too large"}), 413

# ==================== Startup ====================

if __name__ == '__main__':
    # Create necessary directories
    Config.UPLOAD_FOLDER.mkdir(exist_ok=True)
    Config.RESULTS_FOLDER.mkdir(exist_ok=True)
    
    # Print configuration
    Config.print_config()
    
    # Cleanup old files on startup
    cleanup_old_files(Config.UPLOAD_FOLDER, max_age_hours=24)
    cleanup_old_files(Config.RESULTS_FOLDER, max_age_hours=24)
    
    logger.info(f"Starting Flask app on {Config.FLASK_HOST}:{Config.FLASK_PORT}")
    
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG,
        threaded=True
    )
