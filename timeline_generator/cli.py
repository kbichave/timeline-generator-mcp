"""Command-line interface for Timeline Generator."""

from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel

from . import __version__
from .models import TimelineStyle, ThemeName, TimeScale, OutputFormat, TimelineConfig, ExportPreset, PRESET_DIMENSIONS
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
    text_wrap: Optional[bool] = typer.Option(
        None,
        "--text-wrap/--no-text-wrap",
        help="Enable or disable text wrapping for long titles/descriptions.",
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
        
        # Apply text wrap override
        if text_wrap is not None:
            config.text_wrap = text_wrap
        
        # Determine output path
        if output is None:
            ext = config.output.format.value
            output = input_file.with_suffix(f".{ext}")
        
        # Get theme and renderer
        theme_instance = get_theme(config.theme.value)
        
        # Apply custom overrides from config
        if config.colors:
            theme_instance.apply_color_overrides(config.colors)
        if config.fonts:
            theme_instance.apply_font_overrides(config.fonts)

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
    text_wrap: bool = typer.Option(
        True,
        "--text-wrap/--no-text-wrap",
        help="Enable or disable text wrapping for long titles/descriptions.",
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
            text_wrap=text_wrap,
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
        "neon": ("Vibrant glowing neon on dark", "Cyan & Magenta"),
        "pastel": ("Soft friendly pastel colors", "Rose & Sky"),
        "ocean": ("Deep aquatic blue-green tones", "Blues & Teals"),
        "sunset": ("Warm golden hour gradient", "Orange & Gold"),
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
    template = '''# Timeline Generator Configuration
# Documentation: https://github.com/kbichave/timeline-generator-mcp

title: "My Project Timeline"
subtitle: "Key milestones and deliverables"
scale: monthly          # hourly, daily, weekly, monthly, quarterly, yearly
style: horizontal       # horizontal, vertical, gantt, roadmap, infographic
theme: corporate        # minimal, corporate, creative, dark, neon, pastel, ocean, sunset

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

text_wrap: true

# Optional: custom font family (overrides theme default)
# fonts:
#   family: "Georgia"
#   title: 16
#   description: 12

# Optional: watermark/branding
# watermark:
#   text: "Made with TimelineGen"
#   position: bottom-right
#   opacity: 0.3

output:
  format: png           # png, svg, gif, mp4
  # preset: ig-post     # ig-story, ig-post, linkedin, twitter, yt-thumbnail, presentation
  width: 1920
  height: 1080
  fps: 30              # For gif/mp4 only
  duration: 5          # Seconds, for gif/mp4 only
  # animation_effect: fade  # fade, slide-up, slide-left, pop, scale
'''
    
    output.write_text(template)
    console.print(f"[bold green]✓[/] Template created: [cyan]{output}[/]")
    console.print("\nEdit the file and run:")
    console.print(f"  [cyan]timeline-gen generate {output}[/]")


@app.command()
def presets():
    """List all available export size presets."""
    table = Table(title="Export Size Presets")
    table.add_column("Preset", style="cyan")
    table.add_column("Size", style="bold")
    table.add_column("Use Case")

    preset_info = {
        "hd-16:9": "Standard HD video/presentation",
        "ig-story": "Instagram Story / TikTok",
        "ig-post": "Instagram square post",
        "linkedin": "LinkedIn feed post",
        "twitter": "Twitter/X post",
        "presentation": "16:9 slide deck",
        "a4-landscape": "Print-quality A4 landscape",
        "yt-thumbnail": "YouTube thumbnail",
    }

    for name, (w, h) in PRESET_DIMENSIONS.items():
        table.add_row(name, f"{w}x{h}", preset_info.get(name, ""))

    console.print(table)


@app.command()
def demo(
    output_dir: Path = typer.Option(
        Path("demo_output"),
        "-o", "--output-dir",
        help="Directory to save demo outputs.",
    ),
):
    """Generate a showcase of all styles and themes."""
    from datetime import datetime as dt
    from .models import Milestone, OutputConfig

    output_dir.mkdir(parents=True, exist_ok=True)

    demo_milestones = [
        Milestone(date=dt(2024, 1, 15), title="Project Kickoff", description="Team assembled", highlight=True),
        Milestone(date=dt(2024, 3, 1), title="Design Complete", description="UI/UX finalized"),
        Milestone(date=dt(2024, 5, 15), title="Beta Launch", description="First users onboarded", highlight=True),
        Milestone(date=dt(2024, 8, 1), title="Scale Phase", description="Performance optimization"),
        Milestone(date=dt(2024, 11, 1), title="v1.0 Release", description="Production ready", color="#4CAF50"),
    ]

    generated = []
    theme_list = [t.value for t in ThemeName]
    style_list = ["horizontal", "vertical", "infographic"]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        total = len(theme_list) * len(style_list)
        task = progress.add_task("Generating demo showcase...", total=total)

        for theme_name in theme_list:
            for style_name in style_list:
                try:
                    config = TimelineConfig(
                        title=f"{style_name.title()} — {theme_name.title()}",
                        subtitle="Timeline Generator Demo",
                        scale=TimeScale.MONTHLY,
                        style=TimelineStyle(style_name),
                        theme=ThemeName(theme_name),
                        milestones=demo_milestones,
                        output=OutputConfig(width=1280, height=720),
                    )

                    theme_instance = get_theme(config.theme.value)
                    renderer = get_renderer(config, theme_instance)
                    exporter = ImageExporter(renderer)

                    filename = f"{style_name}_{theme_name}.png"
                    exporter.export_png(output_dir / filename)
                    generated.append(filename)
                except Exception as e:
                    console.print(f"  [yellow]Skipped {style_name}/{theme_name}: {e}[/]")

                progress.update(task, advance=1)

    console.print(f"\n[bold green]✓[/] Generated {len(generated)} demo images in [cyan]{output_dir}/[/]")
    console.print(f"  Styles: {', '.join(style_list)}")
    console.print(f"  Themes: {', '.join(theme_list)}")


if __name__ == "__main__":
    app()

