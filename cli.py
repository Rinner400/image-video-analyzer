"""Command-Line Interface for Image & Video Analyzer"""

import click
import logging
import json
from pathlib import Path
from tabulate import tabulate
from config import Config
from analyzer.image_analyzer import ImageAnalyzer
from analyzer.video_analyzer import VideoAnalyzer
from analyzer.utils import save_results, format_analysis_result

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=Config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Initialize analyzers
config = Config()
image_analyzer = ImageAnalyzer(config)
video_analyzer = VideoAnalyzer(config)

@click.group()
def cli():
    """Image & Video Analyzer - CLI"""
    pass

@cli.command()
@click.option('--path', '-p', required=True, help='Path to image file')
@click.option('--format', '-f', type=click.Choice(['json', 'txt', 'csv']), 
              default='json', help='Output format')
@click.option('--save', '-s', is_flag=True, help='Save results to file')
def analyze_image(path, format, save):
    """Analyze a single image"""
    
    path_obj = Path(path)
    
    if not path_obj.exists():
        click.secho(f"✗ File not found: {path}", fg='red')
        return
    
    click.secho(f"\n📸 Analyzing image: {path_obj.name}", fg='blue', bold=True)
    
    with click.progressbar(length=100, label='Processing') as bar:
        try:
            result = image_analyzer.analyze(str(path_obj))
            bar.update(100)
            
            if result['status'] == 'success':
                _display_image_result(result)
                
                if save:
                    filepath = save_results(result, path_obj.name, format)
                    if filepath:
                        click.secho(f"✓ Results saved to {filepath}", fg='green')
            else:
                click.secho(f"✗ Error: {result.get('error', 'Unknown error')}", fg='red')
        
        except Exception as e:
            click.secho(f"✗ Analysis failed: {e}", fg='red')

@cli.command()
@click.option('--path', '-p', required=True, help='Path to video file')
@click.option('--frames', '-f', type=int, default=None, 
              help=f'Max frames to extract (default: {Config.MAX_VIDEO_FRAMES})')
@click.option('--fps', type=int, default=None,
              help=f'Sample frames per second (default: {Config.VIDEO_SAMPLE_FPS})')
@click.option('--format', type=click.Choice(['json', 'txt', 'csv']), 
              default='json', help='Output format')
@click.option('--save', is_flag=True, help='Save results to file')
@click.option('--summary-only', is_flag=True, help='Show summary only')
def analyze_video(path, frames, fps, format, save, summary_only):
    """Analyze a video"""
    
    path_obj = Path(path)
    
    if not path_obj.exists():
        click.secho(f"✗ File not found: {path}", fg='red')
        return
    
    click.secho(f"\n🎥 Analyzing video: {path_obj.name}", fg='blue', bold=True)
    
    try:
        result = video_analyzer.analyze(str(path_obj), frames, fps)
        
        if result['status'] == 'success':
            _display_video_result(result, summary_only)
            
            if save:
                filepath = save_results(result, path_obj.name, format)
                if filepath:
                    click.secho(f"✓ Results saved to {filepath}", fg='green')
        else:
            click.secho(f"✗ Error: {result.get('error', 'Unknown error')}", fg='red')
    
    except Exception as e:
        click.secho(f"✗ Analysis failed: {e}", fg='red')

@cli.command()
@click.option('--directory', '-d', required=True, help='Directory path')
@click.option('--type', '-t', type=click.Choice(['image', 'video']), 
              default='image', help='File type to process')
@click.option('--format', '-f', type=click.Choice(['json', 'txt', 'csv']), 
              default='json', help='Output format')
@click.option('--output', '-o', help='Output CSV file for results')
def batch_analyze(directory, type, format, output):
    """Batch analyze files in directory"""
    
    dir_path = Path(directory)
    
    if not dir_path.exists() or not dir_path.is_dir():
        click.secho(f"✗ Directory not found: {directory}", fg='red')
        return
    
    # Get files
    if type == 'image':
        extensions = Config.ALLOWED_IMAGE_EXTENSIONS
    else:
        extensions = Config.ALLOWED_VIDEO_EXTENSIONS
    
    files = []
    for ext in extensions:
        files.extend(dir_path.glob(f"*.{ext}"))
        files.extend(dir_path.glob(f"*.{ext.upper()}"))
    
    if not files:
        click.secho(f"✗ No {type} files found in {directory}", fg='red')
        return
    
    click.secho(f"\n📁 Processing {len(files)} {type} files...", fg='blue', bold=True)
    
    results = []
    
    with click.progressbar(files, label='Processing files') as bar:
        for filepath in bar:
            try:
                if type == 'image':
                    result = image_analyzer.analyze(str(filepath))
                else:
                    result = video_analyzer.analyze(str(filepath))
                
                results.append(result)
                
                if result['status'] == 'success':
                    save_results(result, filepath.name, format)
            
            except Exception as e:
                results.append({
                    "file": filepath.name,
                    "status": "error",
                    "error": str(e)
                })
    
    # Save results CSV
    if output:
        import csv
        with open(output, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['File', 'Status', 'Caption', 'Objects Count', 'Error'])
            for result in results:
                writer.writerow([
                    result.get('file_name') or result.get('video_path', 'Unknown'),
                    result.get('status', 'unknown'),
                    result.get('caption') or result.get('summary', {}).get('most_common_caption', 'N/A'),
                    len(result.get('objects', [])) if result.get('status') == 'success' else 'N/A',
                    result.get('error', '')
                ])
        click.secho(f"✓ Results saved to {output}", fg='green')
    
    # Summary
    successful = sum(1 for r in results if r.get('status') == 'success')
    click.secho(f"\n✓ Completed: {successful}/{len(files)} successful", fg='green')

@cli.command()
def config():
    """Show current configuration"""
    Config.print_config()
    
    config_data = [
        ['Setting', 'Value'],
        ['Device', Config.DEVICE],
        ['GPU Available', Config.USE_GPU],
        ['Image Caption Model', Config.IMAGE_CAPTION_MODEL],
        ['Object Detection Model', Config.OBJECT_DETECTION_MODEL],
        ['Max Video Frames', Config.MAX_VIDEO_FRAMES],
        ['Video Sample FPS', Config.VIDEO_SAMPLE_FPS],
        ['Max Image Size', f"{Config.MAX_IMAGE_SIZE / 1024 / 1024:.0f}MB"],
        ['Max Video Size', f"{Config.MAX_VIDEO_SIZE / 1024 / 1024:.0f}MB"],
        ['Upload Folder', str(Config.UPLOAD_FOLDER)],
        ['Results Folder', str(Config.RESULTS_FOLDER)],
    ]
    
    click.echo(tabulate(config_data, headers='firstrow', tablefmt='grid'))

def _display_image_result(result):
    """Display image analysis result"""
    
    click.secho("\n📊 Analysis Results:", fg='cyan', bold=True)
    
    # Caption
    click.echo(f"\n🔤 Caption:")
    click.echo(f"   {result['caption']}")
    
    # Objects
    if result.get('objects'):
        click.echo(f"\n🏷️  Detected Objects:")
        table = [['Object', 'Confidence']]
        for obj in result['objects']:
            table.append([obj['label'], f"{obj['confidence']:.1%}"])
        click.echo(tabulate(table, headers='firstrow', tablefmt='simple'))
    
    # Prompt
    click.echo(f"\n💬 Generated Prompt:")
    click.echo(f"   {result['prompt']}")
    
    # Metadata
    if result.get('metadata'):
        click.echo(f"\n📝 Metadata:")
        metadata = result['metadata']
        metadata_table = [
            ['Format', metadata.get('format', 'N/A')],
            ['Size', f"{metadata.get('size', {}).get('width', 0)}x{metadata.get('size', {}).get('height', 0)}"],
            ['File Size', f"{metadata.get('file_size_mb', 0)}MB"],
        ]
        click.echo(tabulate(metadata_table, tablefmt='simple'))

def _display_video_result(result, summary_only=False):
    """Display video analysis result"""
    
    click.secho("\n📊 Video Analysis Results:", fg='cyan', bold=True)
    
    # Summary
    if result.get('summary'):
        summary = result['summary']
        click.echo(f"\n📋 Summary:")
        click.echo(f"   Frames Analyzed: {summary.get('total_frames_analyzed', 0)}")
        click.echo(f"   Most Common Scene: {summary.get('most_common_caption', 'N/A')}")
    
    # Common Objects
    if result.get('summary', {}).get('common_objects'):
        click.echo(f"\n🏷️  Common Objects:")
        table = [['Object', 'Frequency', 'Avg Confidence']]
        for obj in result['summary']['common_objects'][:10]:
            table.append([
                obj['label'],
                obj['frequency'],
                f"{obj['avg_confidence']:.1%}"
            ])
        click.echo(tabulate(table, headers='firstrow', tablefmt='simple'))
    
    # Prompt
    click.echo(f"\n💬 Generated Prompt:")
    click.echo(f"   {result['prompt']}")
    
    # Metadata
    if result.get('metadata'):
        click.echo(f"\n📝 Video Metadata:")
        metadata = result['metadata']
        metadata_table = [
            ['Duration', f"{metadata.get('duration_seconds', 0):.2f}s"],
            ['Total Frames', metadata.get('total_frames', 0)],
            ['FPS', metadata.get('fps', 0)],
            ['Resolution', f"{metadata.get('resolution', {}).get('width', 0)}x{metadata.get('resolution', {}).get('height', 0)}"],
            ['File Size', f"{metadata.get('file_size_mb', 0)}MB"],
        ]
        click.echo(tabulate(metadata_table, tablefmt='simple'))
    
    # Frame details (if not summary only)
    if not summary_only and result.get('frame_analyses'):
        click.echo(f"\n📹 Frame-by-Frame Analysis:")
        table = [['Frame', 'Caption', 'Objects Count']]
        for analysis in result['frame_analyses'][:10]:
            table.append([
                analysis.get('frame_number', 'N/A'),
                analysis.get('caption', 'N/A')[:40] + '...' if len(analysis.get('caption', '')) > 40 else analysis.get('caption', 'N/A'),
                len(analysis.get('objects', []))
            ])
        click.echo(tabulate(table, headers='firstrow', tablefmt='simple'))

if __name__ == '__main__':
    cli()
