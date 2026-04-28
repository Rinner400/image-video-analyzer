"""Video Analysis Module"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import torch
import cv2
from PIL import Image
from tqdm import tqdm
from config import Config
from .image_analyzer import ImageAnalyzer
from .utils import Timer, timeit, validate_file

logger = logging.getLogger(__name__)

class VideoAnalyzer:
    """Analyze videos and generate prompts"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.image_analyzer = ImageAnalyzer(config)
    
    @timeit
    def analyze(self, video_path: str, max_frames: Optional[int] = None, 
                fps: Optional[int] = None) -> Dict[str, Any]:
        """Analyze a video and generate comprehensive analysis"""
        
        if not validate_file(video_path, "video"):
            raise ValueError(f"Invalid video file: {video_path}")
        
        max_frames = max_frames or self.config.MAX_VIDEO_FRAMES
        fps = fps or self.config.VIDEO_SAMPLE_FPS
        
        with Timer("Video Analysis"):
            try:
                # Extract frames
                frames = self._extract_frames(video_path, max_frames, fps)
                logger.info(f"Extracted {len(frames)} frames")
                
                if not frames:
                    return {
                        "status": "error",
                        "error": "No frames extracted from video",
                        "video_path": str(video_path)
                    }
                
                # Analyze frames
                frame_analyses = self._analyze_frames(frames)
                
                # Get video metadata
                metadata = self._get_metadata(video_path)
                
                # Generate summary
                summary = self._generate_summary(frame_analyses)
                
                # Generate video prompt
                prompt = self._generate_prompt(summary, frame_analyses)
                
                return {
                    "status": "success",
                    "video_path": str(video_path),
                    "total_frames_extracted": len(frames),
                    "frame_analyses": frame_analyses,
                    "summary": summary,
                    "prompt": prompt,
                    "metadata": metadata
                }
            
            except Exception as e:
                logger.error(f"Video analysis failed: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "video_path": str(video_path)
                }
    
    def _extract_frames(self, video_path: str, max_frames: int, fps: int) -> List[Image.Image]:
        """Extract frames from video"""
        frames = []
        
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise ValueError("Failed to open video file")
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            video_fps = cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"Video: {total_frames} frames at {video_fps} FPS")
            
            # Calculate frame interval
            frame_interval = max(1, int(video_fps / fps))
            frame_indices = list(range(0, total_frames, frame_interval))[:max_frames]
            
            logger.info(f"Sampling frames: {len(frame_indices)} frames with interval {frame_interval}")
            
            for idx in tqdm(frame_indices, desc="Extracting frames"):
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                
                if ret:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(frame_rgb)
                    frames.append(pil_image)
            
            cap.release()
            
        except Exception as e:
            logger.error(f"Frame extraction failed: {e}")
        
        return frames
    
    def _analyze_frames(self, frames: List[Image.Image]) -> List[Dict[str, Any]]:
        """Analyze extracted frames"""
        analyses = []
        
        for idx, frame in enumerate(tqdm(frames, desc="Analyzing frames"), 1):
            try:
                # Get caption
                caption = self.image_analyzer._get_caption(frame)
                
                # Detect objects
                objects = self.image_analyzer._detect_objects(frame)
                
                analyses.append({
                    "frame_number": idx,
                    "caption": caption,
                    "objects": objects
                })
            
            except Exception as e:
                logger.error(f"Frame {idx} analysis failed: {e}")
                analyses.append({
                    "frame_number": idx,
                    "error": str(e)
                })
        
        return analyses
    
    def _get_metadata(self, video_path: str) -> Dict[str, Any]:
        """Extract video metadata"""
        path = Path(video_path)
        
        try:
            cap = cv2.VideoCapture(video_path)
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            duration = total_frames / fps if fps > 0 else 0
            
            cap.release()
            
            metadata = {
                "file_name": path.name,
                "file_size_mb": round(path.stat().st_size / 1024 / 1024, 2),
                "total_frames": total_frames,
                "fps": round(fps, 2),
                "duration_seconds": round(duration, 2),
                "resolution": {
                    "width": width,
                    "height": height,
                    "aspect_ratio": round(width / height, 2) if height > 0 else 0
                },
                "created_date": str(path.stat().st_ctime),
                "modified_date": str(path.stat().st_mtime)
            }
        
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            metadata = {"error": str(e)}
        
        return metadata
    
    def _generate_summary(self, frame_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary from frame analyses"""
        
        captions = []
        all_objects = {}
        
        for analysis in frame_analyses:
            if "caption" in analysis:
                captions.append(analysis["caption"])
            
            if "objects" in analysis:
                for obj in analysis["objects"]:
                    label = obj['label']
                    if label not in all_objects:
                        all_objects[label] = {"count": 0, "confidences": []}
                    all_objects[label]["count"] += 1
                    all_objects[label]["confidences"].append(obj['confidence'])
        
        # Calculate object frequencies and average confidence
        object_summary = []
        for label, data in sorted(all_objects.items(), key=lambda x: x[1]["count"], reverse=True):
            avg_confidence = sum(data["confidences"]) / len(data["confidences"])
            object_summary.append({
                "label": label,
                "frequency": data["count"],
                "avg_confidence": round(avg_confidence, 3)
            })
        
        # Get most common caption
        most_common_caption = max(set(captions), key=captions.count) if captions else "No caption"
        
        return {
            "most_common_caption": most_common_caption,
            "total_frames_analyzed": len(frame_analyses),
            "common_objects": object_summary[:10],
            "caption_count": len(captions)
        }
    
    def _generate_prompt(self, summary: Dict[str, Any], 
                        frame_analyses: List[Dict[str, Any]]) -> str:
        """Generate a video prompt based on analysis"""
        
        caption = summary.get("most_common_caption", "Unknown scene")
        objects = summary.get("common_objects", [])
        
        prompt = f"Generate a video showing {caption}"
        
        if objects:
            object_names = [obj['label'] for obj in objects[:5]]
            prompt += f" with {', '.join(object_names)}"
        
        prompt += ". Make it dynamic and engaging. Duration: 10 seconds."
        
        return prompt
