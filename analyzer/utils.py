"""Utility functions for Image & Video Analyzer"""

import logging
import time
from pathlib import Path
from functools import wraps
from typing import Dict, List, Any
import json
import csv
from config import Config

# Setup logging
logger = logging.getLogger(__name__)

class Timer:
    """Context manager for timing operations"""
    def __init__(self, name="Operation"):
        self.name = name
        self.start = None
        self.elapsed = 0
    
    def __enter__(self):
        self.start = time.time()
        return self
    
    def __exit__(self, *args):
        self.elapsed = time.time() - self.start
        logger.info(f"{self.name} took {self.elapsed:.2f}s")

def timeit(func):
    """Decorator to time function execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        with Timer(func.__name__):
            return func(*args, **kwargs)
    return wrapper

def validate_file(filepath: str, file_type: str = "image") -> bool:
    """Validate file type and size"""
    path = Path(filepath)
    
    if not path.exists():
        logger.error(f"File not found: {filepath}")
        return False
    
    file_size = path.stat().st_size
    extension = path.suffix.lstrip('.').lower()
    
    if file_type == "image":
        if extension not in Config.ALLOWED_IMAGE_EXTENSIONS:
            logger.error(f"Invalid image format: {extension}")
            return False
        if file_size > Config.MAX_IMAGE_SIZE:
            logger.error(f"Image too large: {file_size / 1024 / 1024:.1f}MB")
            return False
    elif file_type == "video":
        if extension not in Config.ALLOWED_VIDEO_EXTENSIONS:
            logger.error(f"Invalid video format: {extension}")
            return False
        if file_size > Config.MAX_VIDEO_SIZE:
            logger.error(f"Video too large: {file_size / 1024 / 1024:.1f}MB")
            return False
    
    return True

def save_results(results: Dict[str, Any], filename: str, format: str = "json") -> str:
    """Save analysis results in specified format"""
    output_path = Config.RESULTS_FOLDER / f"{Path(filename).stem}"
    
    try:
        if format == "json":
            filepath = f"{output_path}.json"
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2)
        
        elif format == "txt":
            filepath = f"{output_path}.txt"
            with open(filepath, 'w') as f:
                f.write(f"Analysis Results for: {filename}\n")
                f.write("=" * 50 + "\n\n")
                for key, value in results.items():
                    if key != "objects":
                        f.write(f"{key.upper()}: {value}\n")
                if "objects" in results:
                    f.write("\nDETECTED OBJECTS:\n")
                    for obj in results["objects"]:
                        f.write(f"  - {obj['label']}: {obj['confidence']:.2%}\n")
        
        elif format == "csv":
            filepath = f"{output_path}.csv"
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Field", "Value"])
                for key, value in results.items():
                    if key != "objects":
                        writer.writerow([key, value])
        
        logger.info(f"Results saved to {filepath}")
        return filepath
    
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        return None

def format_analysis_result(analysis: Dict[str, Any], format: str = "json") -> str:
    """Format analysis result for display"""
    if format == "json":
        return json.dumps(analysis, indent=2)
    
    elif format == "text":
        text = ""
        text += f"Caption: {analysis.get('caption', 'N/A')}\n"
        text += f"Prompt: {analysis.get('prompt', 'N/A')}\n\n"
        text += "Detected Objects:\n"
        for obj in analysis.get('objects', []):
            text += f"  - {obj['label']}: {obj['confidence']:.2%}\n"
        return text
    
    return json.dumps(analysis)

def cleanup_old_files(folder: Path, max_age_hours: int = 24) -> int:
    """Remove files older than specified hours"""
    import os
    current_time = time.time()
    deleted_count = 0
    
    try:
        for filepath in folder.glob("*"):
            if filepath.is_file():
                file_age = (current_time - filepath.stat().st_mtime) / 3600
                if file_age > max_age_hours:
                    filepath.unlink()
                    deleted_count += 1
        logger.info(f"Cleaned up {deleted_count} old files")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
    
    return deleted_count

def get_gpu_info() -> Dict[str, Any]:
    """Get GPU information"""
    import torch
    
    info = {
        "gpu_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
    }
    
    if torch.cuda.is_available():
        info["current_device"] = torch.cuda.current_device()
        info["device_name"] = torch.cuda.get_device_name(0)
        props = torch.cuda.get_device_properties(0)
        info["total_memory_gb"] = props.total_memory / 1e9
        info["current_memory_gb"] = torch.cuda.memory_allocated() / 1e9
    
    return info
