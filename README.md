# Image & Video Analyzer 🎬📸

A comprehensive Python application that analyzes images and videos using state-of-the-art Hugging Face models. Provides intelligent prompt generation, object detection, and detailed analysis through Web UI, REST API, and CLI.

## Features

✨ **Core Capabilities:**
- 🖼️ **Image Analysis**: Captioning, object detection, metadata extraction
- 🎥 **Video Analysis**: Frame extraction, temporal analysis, video description
- 🌐 **Web Interface**: User-friendly Flask-based UI with drag-and-drop upload
- 📡 **REST API**: JSON endpoints for programmatic access
- 💻 **CLI Tool**: Command-line interface for batch processing
- ⚡ **GPU Support**: CUDA acceleration for faster processing
- 📊 **Multiple Outputs**: JSON, TXT, CSV formats

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Optional: CUDA-capable GPU for acceleration

### Setup

```bash
# Clone the repository
git clone https://github.com/Rinner400/image-video-analyzer.git
cd image-video-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### 1. Web Interface

```bash
python app.py
```

Access the application at `http://localhost:5000`

**Features:**
- Drag-and-drop file upload
- Real-time processing status
- Preview results in browser
- Download results as JSON/TXT/CSV
- Batch upload support

### 2. REST API

**Health Check:**
```bash
curl http://localhost:5000/api/health
```

**Analyze Image:**
```bash
curl -X POST -F "file=@image.jpg" http://localhost:5000/api/analyze/image
```

**Analyze Video:**
```bash
curl -X POST -F "file=@video.mp4" \
  -F "max_frames=10" \
  -F "fps=2" \
  http://localhost:5000/api/analyze/video
```

**Response Format:**
```json
{
  "status": "success",
  "file_name": "image.jpg",
  "file_type": "image",
  "analysis": {
    "caption": "A dog playing in the park",
    "objects": [
      {"label": "dog", "confidence": 0.95},
      {"label": "park", "confidence": 0.87}
    ],
    "prompt": "Generate an image of a dog playing in the park on a sunny day",
    "metadata": {...}
  },
  "processing_time": 2.34
}
```

### 3. Command-Line Interface

**Analyze Single Image:**
```bash
python cli.py analyze-image --path image.jpg
```

**Analyze Video:**
```bash
python cli.py analyze-video --path video.mp4 --frames 15 --fps 2
```

**Batch Process Directory:**
```bash
python cli.py batch-analyze --directory ./images --type image --output results.csv
```

**Available Options:**
```bash
python cli.py --help
```

## Configuration

Edit `config.py` to customize:

```python
# Model Selection
IMAGE_CAPTION_MODEL = "Salesforce/blip-image-captioning-large"
OBJECT_DETECTION_MODEL = "facebook/detr-resnet50"

# Processing
MAX_VIDEO_FRAMES = 30
VIDEO_SAMPLE_FPS = 2
CONFIDENCE_THRESHOLD = 0.5

# Hardware
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
USE_GPU = True

# Upload Limits
MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
```

## Project Structure

```
image-video-analyzer/
├── analyzer/
│   ├── __init__.py
│   ├── image_analyzer.py      # Image analysis logic
│   ├── video_analyzer.py      # Video analysis logic
│   └── utils.py               # Utility functions
├── templates/
│   ├── base.html              # Base template
│   ├── index.html             # Upload interface
│   └── results.html           # Results display
├── static/
│   ├── css/
│   │   └── style.css          # Styling
│   └── js/
│       └── script.js          # Frontend logic
├── app.py                     # Flask web application
├── cli.py                     # Command-line interface
├── config.py                  # Configuration
├── requirements.txt           # Python dependencies
├── .gitignore
└── README.md
```

## Models Used

### Image Captioning
- **Model**: Salesforce BLIP (Bootstrapping Language-Image Pre-training)
- **Capability**: Generates natural language descriptions of images
- **Link**: [Hugging Face](https://huggingface.co/Salesforce/blip-image-captioning-large)

### Object Detection
- **Model**: Facebook DETR (Detection Transformer)
- **Capability**: Detects and localizes objects in images
- **Link**: [Hugging Face](https://huggingface.co/facebook/detr-resnet50)

### Visual Similarity
- **Model**: OpenAI CLIP
- **Capability**: Matches images with text descriptions
- **Link**: [Hugging Face](https://huggingface.co/openai/clip-vit-base-patch32)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Web UI |
| GET | `/api/health` | Health check |
| POST | `/api/analyze/image` | Analyze image |
| POST | `/api/analyze/video` | Analyze video |
| GET | `/api/models` | List available models |
| POST | `/api/batch` | Batch analysis |

## Performance Tips

1. **GPU Acceleration**: Install CUDA for 5-10x faster processing
2. **Batch Processing**: Use batch API for multiple files
3. **Frame Sampling**: Reduce `max_frames` for faster video processing
4. **Model Optimization**: Use quantized models for lower memory usage

## Troubleshooting

**Out of Memory Error:**
- Reduce batch size in `config.py`
- Use CPU mode: Set `DEVICE = "cpu"`
- Reduce video frame count

**Slow Processing:**
- Enable GPU acceleration
- Reduce image resolution
- Decrease number of frames extracted

**Model Download Issues:**
- Check internet connection
- Set Hugging Face cache: `export HF_HOME=/path/to/cache`
- Download models manually

## Examples

### Python Script Integration

```python
from analyzer.image_analyzer import ImageAnalyzer
from config import Config

config = Config()
analyzer = ImageAnalyzer(config)

result = analyzer.analyze("path/to/image.jpg")
print(result["prompt"])
```

### Batch Video Analysis

```bash
for video in videos/*.mp4; do
  python cli.py analyze-video --path "$video" --frames 10
done
```

## Requirements

See `requirements.txt` for complete list:
- torch >= 2.0.0
- transformers >= 4.30.0
- pillow >= 9.0.0
- opencv-python >= 4.6.0
- flask >= 2.3.0
- click >= 8.1.0

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/Rinner400/image-video-analyzer/issues)
- Documentation: Check the wiki

## Roadmap

- [ ] Real-time webcam analysis
- [ ] Custom model fine-tuning
- [ ] Multi-language support
- [ ] Docker containerization
- [ ] Cloud deployment (AWS/GCP)
- [ ] Mobile app
- [ ] Advanced filtering options
- [ ] Result caching

---

**Made with ❤️ by Rinner400**
