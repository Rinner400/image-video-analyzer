"""Image Analysis Module"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import torch
from PIL import Image
from transformers import pipeline, AutoProcessor, AutoModelForCausalLM
from config import Config
from .utils import Timer, timeit, validate_file

logger = logging.getLogger(__name__)

class ImageAnalyzer:
    """Analyze images and generate prompts"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.device = self.config.get_device()
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize Hugging Face models"""
        logger.info(f"Initializing models on device: {self.device}")
        
        try:
            # Image Captioning Model
            logger.info(f"Loading image caption model: {self.config.IMAGE_CAPTION_MODEL}")
            self.image_captioner = pipeline(
                "image-to-text",
                model=self.config.IMAGE_CAPTION_MODEL,
                device=0 if self.device.type == "cuda" else -1
            )
            logger.info("✓ Image caption model loaded")
        except Exception as e:
            logger.error(f"Failed to load image caption model: {e}")
            self.image_captioner = None
        
        try:
            # Object Detection Model
            logger.info(f"Loading object detection model: {self.config.OBJECT_DETECTION_MODEL}")
            self.object_detector = pipeline(
                "object-detection",
                model=self.config.OBJECT_DETECTION_MODEL,
                device=0 if self.device.type == "cuda" else -1
            )
            logger.info("✓ Object detection model loaded")
        except Exception as e:
            logger.error(f"Failed to load object detection model: {e}")
            self.object_detector = None
    
    @timeit
    def analyze(self, image_path: str) -> Dict[str, Any]:
        """Analyze an image and generate comprehensive analysis"""
        
        if not validate_file(image_path, "image"):
            raise ValueError(f"Invalid image file: {image_path}")
        
        with Timer("Image Analysis"):
            try:
                image = Image.open(image_path).convert('RGB')
                
                # Get caption
                caption = self._get_caption(image)
                logger.info(f"Caption: {caption}")
                
                # Detect objects
                objects = self._detect_objects(image)
                logger.info(f"Detected {len(objects)} objects")
                
                # Get image metadata
                metadata = self._get_metadata(image_path, image)
                
                # Generate prompt
                prompt = self._generate_prompt(caption, objects)
                
                return {
                    "status": "success",
                    "caption": caption,
                    "objects": objects,
                    "prompt": prompt,
                    "metadata": metadata,
                    "image_path": str(image_path)
                }
            
            except Exception as e:
                logger.error(f"Image analysis failed: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "image_path": str(image_path)
                }
    
    def _get_caption(self, image: Image.Image) -> str:
        """Generate image caption"""
        if self.image_captioner is None:
            return "N/A"
        
        try:
            with torch.no_grad():
                result = self.image_captioner(image, max_new_tokens=100)
            caption = result[0]['generated_text'] if result else "No caption generated"
            return caption
        except Exception as e:
            logger.error(f"Caption generation failed: {e}")
            return "Error generating caption"
    
    def _detect_objects(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Detect objects in image"""
        if self.object_detector is None:
            return []
        
        try:
            with torch.no_grad():
                detections = self.object_detector(image, threshold=self.config.CONFIDENCE_THRESHOLD)
            
            # Filter and sort by confidence
            objects = [
                {
                    "label": detection['label'],
                    "confidence": round(detection['score'], 3),
                    "box": detection.get('box', {})
                }
                for detection in detections
            ]
            
            # Sort by confidence and limit
            objects = sorted(objects, key=lambda x: x['confidence'], reverse=True)
            objects = objects[:self.config.MAX_OBJECTS]
            
            return objects
        
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return []
    
    def _get_metadata(self, image_path: str, image: Image.Image) -> Dict[str, Any]:
        """Extract image metadata"""
        path = Path(image_path)
        
        metadata = {
            "file_name": path.name,
            "file_size_mb": round(path.stat().st_size / 1024 / 1024, 2),
            "format": image.format,
            "mode": image.mode,
            "size": {
                "width": image.width,
                "height": image.height,
                "aspect_ratio": round(image.width / image.height, 2) if image.height > 0 else 0
            },
            "created_date": str(path.stat().st_ctime),
            "modified_date": str(path.stat().st_mtime)
        }
        
        return metadata
    
    def _generate_prompt(self, caption: str, objects: List[Dict[str, Any]]) -> str:
        """Generate a creative prompt based on analysis"""
        
        if caption == "N/A":
            return "Unable to generate prompt"
        
        prompt = f"Generate an image of {caption}"
        
        if objects:
            object_names = [obj['label'] for obj in objects[:5]]
            prompt += f" featuring {', '.join(object_names)}"
        
        prompt += ". High quality, detailed."
        
        return prompt
    
    def batch_analyze(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """Analyze multiple images"""
        results = []
        for idx, image_path in enumerate(image_paths, 1):
            logger.info(f"Processing image {idx}/{len(image_paths)}: {image_path}")
            result = self.analyze(image_path)
            results.append(result)
        return results
