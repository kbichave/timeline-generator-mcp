"""Video/GIF export functionality."""

from pathlib import Path
from typing import Union, List
import tempfile
import os

from PIL import Image

from ..models import TimelineConfig, OutputFormat
from ..renderers.base import BaseRenderer


class VideoExporter:
    """Export timelines as animated GIFs or videos."""
    
    def __init__(self, renderer: BaseRenderer):
        """
        Initialize the video exporter.
        
        Args:
            renderer: The renderer to use for generating frames.
        """
        self.renderer = renderer
        self.config = renderer.config
    
    def generate_frames(
        self,
        num_frames: int = None,
        include_hold_frames: bool = True,
    ) -> List[Image.Image]:
        """
        Generate animation frames.
        
        Args:
            num_frames: Number of frames to generate. If None, calculated from config.
            include_hold_frames: Add extra frames at start and end for pause effect.
            
        Returns:
            List of PIL Images for each frame.
        """
        if num_frames is None:
            # Calculate based on config
            fps = self.config.output.fps
            duration = self.config.output.duration
            num_frames = int(fps * duration)
        
        frames = []
        
        # Hold frames at the start (show title only)
        hold_frames = 10 if include_hold_frames else 0
        
        # Generate animation frames
        total_animation_frames = num_frames - (hold_frames * 2)
        
        for i in range(num_frames):
            if i < hold_frames:
                # Initial hold - minimal content
                progress = 0.0
            elif i >= num_frames - hold_frames:
                # Final hold - full content
                progress = 1.0
            else:
                # Animation progress
                anim_frame = i - hold_frames
                progress = anim_frame / max(1, total_animation_frames - 1)
                # Apply easing
                progress = self._ease_out_cubic(progress)
            
            # Render frame
            surface = self.renderer.render_frame(progress)
            frame = self.renderer.surface_to_pil()
            frames.append(frame)
        
        return frames
    
    def _ease_out_cubic(self, t: float) -> float:
        """Cubic ease-out function for smooth animation."""
        return 1 - pow(1 - t, 3)
    
    def export_gif(
        self,
        output_path: Union[str, Path],
        fps: int = None,
        duration: float = None,
        loop: int = 0,
        optimize: bool = True,
    ) -> Path:
        """
        Export the timeline as an animated GIF.
        
        Args:
            output_path: Path to save the GIF file.
            fps: Frames per second. If None, uses config value.
            duration: Total duration in seconds. If None, uses config value.
            loop: Number of loops (0 = infinite).
            optimize: Whether to optimize the GIF.
            
        Returns:
            Path to the saved file.
        """
        path = Path(output_path)
        
        # Use config values if not provided
        if fps is None:
            fps = self.config.output.fps
        if duration is None:
            duration = self.config.output.duration
        
        num_frames = int(fps * duration)
        frame_duration = int(1000 / fps)  # ms per frame
        
        # Generate frames
        frames = self.generate_frames(num_frames)
        
        if not frames:
            raise ValueError("No frames generated")
        
        # Convert to palette mode for smaller GIF
        if optimize:
            frames = [self._optimize_frame(f) for f in frames]
        
        # Save as GIF
        frames[0].save(
            path,
            save_all=True,
            append_images=frames[1:],
            duration=frame_duration,
            loop=loop,
            optimize=optimize,
        )
        
        return path
    
    def _optimize_frame(self, frame: Image.Image) -> Image.Image:
        """Optimize a frame for GIF format."""
        # Convert to P mode with adaptive palette
        if frame.mode == "RGBA":
            # Create a white background
            background = Image.new("RGB", frame.size, (255, 255, 255))
            background.paste(frame, mask=frame.split()[3])
            frame = background
        
        # Quantize to reduce colors
        return frame.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    
    def export_mp4(
        self,
        output_path: Union[str, Path],
        fps: int = None,
        duration: float = None,
        codec: str = "libx264",
        bitrate: str = "5000k",
    ) -> Path:
        """
        Export the timeline as an MP4 video.
        
        Args:
            output_path: Path to save the MP4 file.
            fps: Frames per second. If None, uses config value.
            duration: Total duration in seconds. If None, uses config value.
            codec: Video codec to use.
            bitrate: Video bitrate.
            
        Returns:
            Path to the saved file.
        """
        path = Path(output_path)
        
        # Use config values if not provided
        if fps is None:
            fps = self.config.output.fps
        if duration is None:
            duration = self.config.output.duration
        
        num_frames = int(fps * duration)
        
        # Generate frames
        frames = self.generate_frames(num_frames, include_hold_frames=True)
        
        if not frames:
            raise ValueError("No frames generated")
        
        # Try to use moviepy for MP4 export
        try:
            from moviepy.editor import ImageSequenceClip
            
            # Convert PIL frames to numpy arrays
            import numpy as np
            frame_arrays = [np.array(f.convert("RGB")) for f in frames]
            
            # Create video clip
            clip = ImageSequenceClip(frame_arrays, fps=fps)
            
            # Write video
            clip.write_videofile(
                str(path),
                codec=codec,
                bitrate=bitrate,
                audio=False,
                verbose=False,
                logger=None,
            )
            
        except ImportError:
            # Fallback: save as GIF and inform user
            gif_path = path.with_suffix(".gif")
            self.export_gif(gif_path, fps, duration)
            raise RuntimeError(
                f"moviepy not available for MP4 export. "
                f"GIF saved to {gif_path} instead. "
                f"Install moviepy with: pip install moviepy"
            )
        
        return path
    
    def export(
        self,
        output_path: Union[str, Path],
        format: OutputFormat = None,
    ) -> Path:
        """
        Export the timeline to the specified video format.
        
        Args:
            output_path: Path to save the file.
            format: Output format. If None, inferred from path extension.
            
        Returns:
            Path to the saved file.
        """
        path = Path(output_path)
        
        # Infer format from extension if not provided
        if format is None:
            ext = path.suffix.lower()
            if ext == ".mp4":
                format = OutputFormat.MP4
            else:
                format = OutputFormat.GIF
        
        if format == OutputFormat.MP4:
            return self.export_mp4(path)
        else:
            return self.export_gif(path)

