"""Image export functionality (PNG, SVG)."""

from pathlib import Path
from typing import Union
import io

import cairo
from PIL import Image

from ..models import TimelineConfig, OutputFormat
from ..renderers.base import BaseRenderer


class ImageExporter:
    """Export timelines as static images."""
    
    def __init__(self, renderer: BaseRenderer):
        """
        Initialize the image exporter.
        
        Args:
            renderer: The renderer to use for generating images.
        """
        self.renderer = renderer
        self.config = renderer.config
    
    def export_png(
        self,
        output_path: Union[str, Path],
        quality: int = 95,
        transparent: bool = False,
    ) -> Path:
        """
        Export the timeline as a PNG image.
        
        Args:
            output_path: Path to save the PNG file.
            quality: Image quality (1-100).
            transparent: Whether to use transparent background.
            
        Returns:
            Path to the saved file.
        """
        path = Path(output_path)
        
        # Render the timeline
        surface = self.renderer.render()
        
        # Convert to PIL Image
        img = self.renderer.surface_to_pil()
        
        # Handle transparency
        if not transparent:
            # Ensure RGB mode for non-transparent
            if img.mode == "RGBA":
                # Create white background
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # Use alpha as mask
                img = background
        
        # Save with quality
        if transparent and img.mode == "RGBA":
            img.save(path, "PNG", optimize=True)
        else:
            img.save(path, "PNG", quality=quality, optimize=True)
        
        return path
    
    def export_svg(self, output_path: Union[str, Path]) -> Path:
        """
        Export the timeline as an SVG file.
        
        Args:
            output_path: Path to save the SVG file.
            
        Returns:
            Path to the saved file.
        """
        path = Path(output_path)
        
        # Create SVG surface
        width = self.config.output.width
        height = self.config.output.height
        
        svg_surface = cairo.SVGSurface(str(path), width, height)
        
        # Create new context with SVG surface
        old_surface = self.renderer._surface
        old_ctx = self.renderer._ctx
        
        self.renderer._surface = svg_surface
        self.renderer._ctx = cairo.Context(svg_surface)
        
        # Render to SVG
        self.renderer.render()
        
        # Finish and close
        svg_surface.finish()
        
        # Restore original surface
        self.renderer._surface = old_surface
        self.renderer._ctx = old_ctx
        
        return path
    
    def export_bytes(self, format: OutputFormat = OutputFormat.PNG) -> bytes:
        """
        Export the timeline as bytes.
        
        Args:
            format: Output format (PNG or SVG).
            
        Returns:
            Image data as bytes.
        """
        if format == OutputFormat.SVG:
            # SVG to bytes
            buffer = io.BytesIO()
            width = self.config.output.width
            height = self.config.output.height
            
            svg_surface = cairo.SVGSurface(buffer, width, height)
            
            old_surface = self.renderer._surface
            old_ctx = self.renderer._ctx
            
            self.renderer._surface = svg_surface
            self.renderer._ctx = cairo.Context(svg_surface)
            
            self.renderer.render()
            svg_surface.finish()
            
            self.renderer._surface = old_surface
            self.renderer._ctx = old_ctx
            
            return buffer.getvalue()
        else:
            # PNG to bytes
            self.renderer.render()
            return self.renderer.surface_to_bytes("png")
    
    def export(
        self,
        output_path: Union[str, Path],
        format: OutputFormat = None,
    ) -> Path:
        """
        Export the timeline to the specified format.
        
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
            if ext == ".svg":
                format = OutputFormat.SVG
            else:
                format = OutputFormat.PNG
        
        if format == OutputFormat.SVG:
            return self.export_svg(path)
        else:
            return self.export_png(
                path,
                quality=self.config.output.quality,
                transparent=self.config.output.transparent,
            )

