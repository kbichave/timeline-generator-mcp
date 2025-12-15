"""Command-line interface for Timeline Generator."""

from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel

from . import __version__
from .models import TimelineStyle, ThemeName, TimeScale, OutputFormat, TimelineConfig
from .parser import parse_file, parse_quick_milestones, create_config_from_quick, ParserError
from .themes import THEMES
from .renderers import (
    HorizontalRenderer,
    VerticalRenderer,
    GanttRenderer,
    RoadmapRenderer,
    InfographicRenderer,
)
from .output.image import ImageExporter
from .output.video import VideoExporter

app = typer.Typer(
    name="timeline-gen",
    help="Generate beautiful timeline visualizations from milestone data.",
    add_completion=False,
)

console = Console()


def get_renderer(config: TimelineConfig, theme):
    """Get the appropriate renderer for the timeline style."""
    style = config.style
    
    renderers = {
        TimelineStyle.HORIZONTAL: HorizontalRenderer,
        TimelineStyle.VERTICAL: VerticalRenderer,
        TimelineStyle.GANTT: GanttRenderer,
        TimelineStyle.ROADMAP: RoadmapRenderer,
        TimelineStyle.INFOGRAPHIC: InfographicRenderer,
    }
    
    renderer_class = renderers.get(style, HorizontalRenderer)
    return renderer_class(config, theme)


def get_theme(name: str):
    """Get a theme instance by name."""
    theme_class = THEMES.get(name, THEMES["minimal"])
    return theme_class()


@app.command()
def generate(
    input_file: Path = typer.Argument(
        ...,
        help="Path to YAML or JSON configuration file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "-o", "--output",
        help="Output file path. If not specified, uses input filename with appropriate extension.",
    ),
    format: Optional[str] = typer.Option(
        None,
        "-f", "--format",
        help="Output format: png, svg, gif, mp4. Overrides config file setting.",
    ),
    style: Optional[str] = typer.Option(
        None,
        "-s", "--style",
        help="Timeline style. Overrides config file setting.",
    ),
    theme: Optional[str] = typer.Option(
        None,
        "-t", "--theme",
        help="Theme name. Overrides config file setting.",
    ),
    width: Optional[int] = typer.Option(
        None,
        "-w", "--width",
        help="Output width in pixels. Overrides config file setting.",
    ),
    height: Optional[int] = typer.Option(
        None,
        "-h", "--height",
        help="Output height in pixels. Overrides config file setting.",
    ),
    fps: Optional[int] = typer.Option(
        None,
        "--fps",
        help="Frames per second for GIF/MP4. Higher = smoother but larger file. (default: 30)",
    ),
    duration: Optional[float] = typer.Option(
        None,
        "-d", "--duration",
        help="Animation duration in seconds for GIF/MP4. (default: 5.0)",
    ),
    transparent: bool = typer.Option(
        False,
        "--transparent",
        help="Use transparent background (PNG/GIF only).",
    ),
    accent_color: Optional[str] = typer.Option(
        None,
        "--accent-color",
        help="Custom accent color in hex format (e.g., #FF5733).",
    ),
):
    """Generate a timeline from a configuration file."""
    try:
        # Parse input file
        with console.status("[bold blue]Parsing configuration..."):
            config = parse_file(input_file)
        
        # Apply command-line overrides
        if format:
            config.output.format = OutputFormat(format.lower())
        if style:
            config.style = TimelineStyle(style.lower())
        if theme:
            config.theme = ThemeName(theme.lower())
        if width:
            config.output.width = width
        if height:
            config.output.height = height
        if fps:
            config.output.fps = fps
        if duration:
            config.output.duration = duration
        if transparent:
            config.output.transparent = True
        
        # Apply accent color override
        if accent_color:
            from .models import ColorConfig
            if config.colors is None:
                config.colors = ColorConfig()
            config.colors.accent = accent_color
        
        # Determine output path
        if output is None:
            ext = config.output.format.value
            output = input_file.with_suffix(f".{ext}")
        
        # Get theme and renderer
        theme_instance = get_theme(config.theme.value)
        
        # Apply custom color overrides from config
        if config.colors:
            theme_instance.apply_color_overrides(config.colors)
        
        renderer = get_renderer(config, theme_instance)
        
        # Generate output
        output_format = config.output.format
        
        if output_format in (OutputFormat.PNG, OutputFormat.SVG):
            with console.status(f"[bold green]Generating {output_format.value.upper()}..."):
                exporter = ImageExporter(renderer)
                exporter.export(output, output_format)
        else:
            # Animated output (GIF or MP4)
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Generating {output_format.value.upper()}...",
                    total=100,
                )
                
                def update_progress(current, total):
                    progress.update(task, completed=int(current / total * 100))
                
                exporter = VideoExporter(renderer)
                if output_format == OutputFormat.GIF:
                    exporter.export_gif(output)
                else:
                    exporter.export_mp4(output)
        
        console.print(f"\n[bold green]✓[/] Timeline saved to: [cyan]{output}[/]")
        
        # Print summary
        table = Table(title="Generation Summary", show_header=False, box=None)
        table.add_row("Style", config.style.value.title())
        table.add_row("Theme", config.theme.value.title())
        table.add_row("Milestones", str(len(config.milestones)))
        table.add_row("Format", output_format.value.upper())
        table.add_row("Size", f"{config.output.width}x{config.output.height}")
        console.print(table)
        
    except ParserError as e:
        console.print(f"[bold red]Error:[/] {e}")
        if e.details:
            for detail in e.details:
                console.print(f"  [red]{detail}[/]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@app.command()
def quick(
    milestones: List[str] = typer.Argument(
        ...,
        help="Milestones in 'DATE:TITLE' format (e.g., '2024-01-01:Project Start').",
    ),
    output: Path = typer.Option(
        Path("timeline.png"),
        "-o", "--output",
        help="Output file path.",
    ),
    title: str = typer.Option(
        "Timeline",
        "--title",
        help="Timeline title.",
    ),
    style: str = typer.Option(
        "horizontal",
        "-s", "--style",
        help="Timeline style: horizontal, vertical, gantt, roadmap, infographic.",
    ),
    scale: str = typer.Option(
        "monthly",
        "--scale",
        help="Time scale: hourly, daily, weekly, monthly, quarterly, yearly.",
    ),
    theme: str = typer.Option(
        "minimal",
        "-t", "--theme",
        help="Theme: minimal, corporate, creative, dark.",
    ),
    format: str = typer.Option(
        "png",
        "-f", "--format",
        help="Output format: png, svg, gif, mp4.",
    ),
    width: int = typer.Option(
        1920,
        "-w", "--width",
        help="Output width in pixels.",
    ),
    height: int = typer.Option(
        1080,
        "-h", "--height",
        help="Output height in pixels.",
    ),
    fps: int = typer.Option(
        30,
        "--fps",
        help="Frames per second for GIF/MP4 animations.",
    ),
    duration: float = typer.Option(
        5.0,
        "-d", "--duration",
        help="Animation duration in seconds for GIF/MP4.",
    ),
    transparent: bool = typer.Option(
        False,
        "--transparent",
        help="Use transparent background (PNG/GIF only).",
    ),
    accent_color: Optional[str] = typer.Option(
        None,
        "--accent-color",
        help="Custom accent color in hex format (e.g., #FF5733).",
    ),
):
    """
    Quickly generate a timeline from inline milestones.
    
    Example:
        timeline-gen quick "2024-01-01:Start" "2024-06-01:Launch" "2024-12-01:Scale"
    """
    try:
        # Parse milestones
        with console.status("[bold blue]Parsing milestones..."):
            parsed_milestones = parse_quick_milestones(milestones)
        
        # Create config
        config = create_config_from_quick(
            milestones=parsed_milestones,
            title=title,
            style=style,
            scale=scale,
            theme=theme,
            output_format=format,
            width=width,
            height=height,
            fps=fps,
            duration=duration,
            transparent=transparent,
        )
        
        # Apply accent color override
        if accent_color:
            from .models import ColorConfig
            config.colors = ColorConfig(accent=accent_color)
        
        # Get theme and renderer
        theme_instance = get_theme(config.theme.value)
        
        # Apply custom color overrides
        if config.colors:
            theme_instance.apply_color_overrides(config.colors)
        
        renderer = get_renderer(config, theme_instance)
        
        # Generate output
        output_format = config.output.format
        
        if output_format in (OutputFormat.PNG, OutputFormat.SVG):
            with console.status(f"[bold green]Generating {output_format.value.upper()}..."):
                exporter = ImageExporter(renderer)
                exporter.export(output, output_format)
        else:
            with console.status(f"[bold green]Generating {output_format.value.upper()}..."):
                exporter = VideoExporter(renderer)
                exporter.export(output, output_format)
        
        console.print(f"\n[bold green]✓[/] Timeline saved to: [cyan]{output}[/]")
        
    except ParserError as e:
        console.print(f"[bold red]Error:[/] {e}")
        if e.details:
            for detail in e.details:
                console.print(f"  [red]{detail}[/]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@app.command()
def styles():
    """List all available timeline styles."""
    table = Table(title="Available Timeline Styles")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    
    style_info = {
        "horizontal": "Classic left-to-right timeline with milestones above and below the line",
        "vertical": "Top-to-bottom timeline, ideal for longer histories",
        "gantt": "Project management style with duration bars and optional progress",
        "roadmap": "Product roadmap with swimlanes and categories",
        "infographic": "Creative layout with large icons and flowing design",
    }
    
    for style in TimelineStyle:
        table.add_row(style.value, style_info.get(style.value, ""))
    
    console.print(table)


@app.command()
def themes():
    """List all available themes."""
    table = Table(title="Available Themes")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Colors", style="dim")
    
    theme_info = {
        "minimal": ("Clean and simple with subtle colors", "Grayscale"),
        "corporate": ("Professional business style", "Navy & Blue"),
        "creative": ("Bold and playful design", "Coral & Turquoise"),
        "dark": ("Modern dark mode aesthetic", "Dark with neon accents"),
    }
    
    for name in ThemeName:
        info = theme_info.get(name.value, ("", ""))
        table.add_row(name.value, info[0], info[1])
    
    console.print(table)


@app.command()
def preview(
    input_file: Path = typer.Argument(
        ...,
        help="Path to YAML or JSON configuration file.",
        exists=True,
    ),
):
    """Preview timeline configuration (ASCII art representation)."""
    try:
        config = parse_file(input_file)
        
        # Create ASCII timeline preview
        console.print(Panel(
            f"[bold]{config.title}[/]" +
            (f"\n[dim]{config.subtitle}[/]" if config.subtitle else ""),
            title="Timeline Preview",
            subtitle=f"Style: {config.style.value} | Theme: {config.theme.value}",
        ))
        
        # Show milestones
        console.print("\n[bold]Milestones:[/]")
        
        for i, m in enumerate(config.milestones):
            date_str = m.date.strftime("%Y-%m-%d")
            marker = "◆" if m.highlight else "●"
            color = "yellow" if m.highlight else "cyan"
            
            console.print(f"  [{color}]{marker}[/] [bold]{date_str}[/] - {m.title}")
            if m.description:
                console.print(f"      [dim]{m.description}[/]")
        
        # Show output settings
        console.print(f"\n[bold]Output:[/]")
        console.print(f"  Format: {config.output.format.value.upper()}")
        console.print(f"  Size: {config.output.width}x{config.output.height}")
        if config.output.format in (OutputFormat.GIF, OutputFormat.MP4):
            console.print(f"  Duration: {config.output.duration}s @ {config.output.fps}fps")
        
    except ParserError as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    console.print(f"[bold]timeline-gen[/] version {__version__}")


@app.command()
def init(
    output: Path = typer.Option(
        Path("timeline.yaml"),
        "-o", "--output",
        help="Output file path for the template.",
    ),
):
    """Create a sample timeline configuration file."""
    template = '''# Timeline Generator MCP Configuration
# Documentation: https://github.com/kbichave/timeline-generator-mcp

title: "My Project Timeline"
subtitle: "Key milestones and deliverables"
scale: monthly          # hourly, daily, weekly, monthly, quarterly, yearly
style: horizontal       # horizontal, vertical, gantt, roadmap, infographic
theme: corporate        # minimal, corporate, creative, dark

milestones:
  - date: "2024-01-15"
    title: "Project Kickoff"
    description: "Initial planning and team assembly"
    highlight: true
    
  - date: "2024-02-01"
    title: "Requirements Complete"
    description: "Finalized project requirements and specifications"
    
  - date: "2024-03-15"
    title: "Design Phase"
    description: "UI/UX design and architecture planning"
    category: "design"
    
  - date: "2024-05-01"
    title: "Development Start"
    description: "Begin implementation phase"
    category: "development"
    
  - date: "2024-07-15"
    title: "Beta Release"
    description: "Internal testing and feedback"
    highlight: true
    
  - date: "2024-09-01"
    title: "Public Launch"
    description: "Official release to production"
    highlight: true
    color: "#4CAF50"

output:
  format: png           # png, svg, gif, mp4
  width: 1920
  height: 1080
  fps: 30              # For gif/mp4 only
  duration: 5          # Seconds, for gif/mp4 only
'''
    
    output.write_text(template)
    console.print(f"[bold green]✓[/] Template created: [cyan]{output}[/]")
    console.print("\nEdit the file and run:")
    console.print(f"  [cyan]timeline-gen generate {output}[/]")


if __name__ == "__main__":
    app()

