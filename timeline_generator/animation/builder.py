"""Animation frame builder."""

from typing import List, Optional, Callable
from dataclasses import dataclass, field

from PIL import Image

from ..models import TimelineConfig
from ..renderers.base import BaseRenderer
from .effects import TransitionEffect, FadeIn, EasingFunction, apply_easing


@dataclass
class AnimationConfig:
    """Configuration for animation generation."""
    
    fps: int = 30
    duration: float = 5.0
    hold_start: float = 0.5  # Seconds to hold at start
    hold_end: float = 1.0  # Seconds to hold at end
    milestone_stagger: float = 0.15  # Delay between milestones
    effect: TransitionEffect = field(default_factory=FadeIn)
    easing: EasingFunction = EasingFunction.EASE_OUT


class AnimationBuilder:
    """Build animation frames for timeline visualization."""
    
    def __init__(
        self,
        renderer: BaseRenderer,
        config: AnimationConfig = None,
    ):
        """
        Initialize the animation builder.
        
        Args:
            renderer: The renderer to use for generating frames.
            config: Animation configuration.
        """
        self.renderer = renderer
        self.timeline_config = renderer.config
        self.config = config or AnimationConfig(
            fps=renderer.config.output.fps,
            duration=renderer.config.output.duration,
        )
    
    @property
    def total_frames(self) -> int:
        """Get total number of frames."""
        return int(self.config.fps * self.config.duration)
    
    @property
    def hold_start_frames(self) -> int:
        """Get number of hold frames at start."""
        return int(self.config.fps * self.config.hold_start)
    
    @property
    def hold_end_frames(self) -> int:
        """Get number of hold frames at end."""
        return int(self.config.fps * self.config.hold_end)
    
    @property
    def animation_frames(self) -> int:
        """Get number of frames for the main animation."""
        return self.total_frames - self.hold_start_frames - self.hold_end_frames
    
    def calculate_progress(self, frame: int) -> float:
        """
        Calculate animation progress for a given frame.
        
        Args:
            frame: Frame number (0-indexed).
            
        Returns:
            Progress value from 0.0 to 1.0.
        """
        if frame < self.hold_start_frames:
            return 0.0
        
        if frame >= self.total_frames - self.hold_end_frames:
            return 1.0
        
        # Calculate progress within animation portion
        anim_frame = frame - self.hold_start_frames
        raw_progress = anim_frame / max(1, self.animation_frames - 1)
        
        # Apply easing
        return apply_easing(raw_progress, self.config.easing)
    
    def generate_frame(self, frame: int) -> Image.Image:
        """
        Generate a single animation frame.
        
        Args:
            frame: Frame number (0-indexed).
            
        Returns:
            PIL Image for the frame.
        """
        progress = self.calculate_progress(frame)
        
        # Render the frame
        self.renderer.render_frame(progress)
        
        return self.renderer.surface_to_pil()
    
    def generate_all_frames(
        self,
        callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Image.Image]:
        """
        Generate all animation frames.
        
        Args:
            callback: Optional callback(current_frame, total_frames) for progress.
            
        Returns:
            List of PIL Images.
        """
        frames = []
        
        for i in range(self.total_frames):
            frame = self.generate_frame(i)
            frames.append(frame)
            
            if callback:
                callback(i + 1, self.total_frames)
        
        return frames
    
    def build_gif(
        self,
        output_path: str,
        optimize: bool = True,
        loop: int = 0,
        callback: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """
        Build and save an animated GIF.
        
        Args:
            output_path: Path to save the GIF.
            optimize: Whether to optimize the GIF.
            loop: Number of loops (0 = infinite).
            callback: Optional progress callback.
            
        Returns:
            Path to the saved GIF.
        """
        frames = self.generate_all_frames(callback)
        
        if not frames:
            raise ValueError("No frames generated")
        
        # Calculate frame duration in milliseconds
        frame_duration = int(1000 / self.config.fps)
        
        # Optimize frames for GIF
        if optimize:
            optimized_frames = []
            for frame in frames:
                if frame.mode == "RGBA":
                    # Create white background
                    bg = Image.new("RGB", frame.size, (255, 255, 255))
                    bg.paste(frame, mask=frame.split()[3])
                    frame = bg
                optimized_frames.append(
                    frame.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
                )
            frames = optimized_frames
        
        # Save GIF
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=frame_duration,
            loop=loop,
            optimize=optimize,
        )
        
        return output_path
    
    def build_frames_for_video(
        self,
        callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Image.Image]:
        """
        Build frames suitable for video encoding.
        
        Args:
            callback: Optional progress callback.
            
        Returns:
            List of RGB PIL Images.
        """
        frames = self.generate_all_frames(callback)
        
        # Ensure all frames are RGB
        rgb_frames = []
        for frame in frames:
            if frame.mode != "RGB":
                if frame.mode == "RGBA":
                    bg = Image.new("RGB", frame.size, (255, 255, 255))
                    bg.paste(frame, mask=frame.split()[3])
                    frame = bg
                else:
                    frame = frame.convert("RGB")
            rgb_frames.append(frame)
        
        return rgb_frames


def create_animation_builder(
    renderer: BaseRenderer,
    fps: int = None,
    duration: float = None,
    stagger: float = 0.15,
) -> AnimationBuilder:
    """
    Create an animation builder with the specified settings.
    
    Args:
        renderer: The renderer to use.
        fps: Frames per second (default from config).
        duration: Animation duration (default from config).
        stagger: Delay between milestones.
        
    Returns:
        Configured AnimationBuilder.
    """
    config = AnimationConfig(
        fps=fps or renderer.config.output.fps,
        duration=duration or renderer.config.output.duration,
        milestone_stagger=stagger,
    )
    
    return AnimationBuilder(renderer, config)

