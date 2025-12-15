"""Parser for YAML, JSON, and TOON timeline configuration files.

TOON (Token-Oriented Object Notation) is a compact format designed for LLMs
that reduces token usage by 30-60% compared to JSON while maintaining
full data model compatibility.

TOON Format Reference:
- Key-value pairs: `key: value` (no quotes needed for simple values)
- Arrays: `key[N]:` followed by N lines of values
- Tabular arrays: `key[N]: field1 field2` header, then N rows of values
- Nested objects: indentation-based (like YAML)

Example TOON for timeline:
```
title: Project Timeline
style: horizontal
theme: corporate
milestones[3]: date title description highlight
2024-01-15 "Project Start" "Kickoff meeting" true
2024-06-01 Launch "Go live" false
2024-12-01 "Year End" null false
```
"""

import json
import re
from pathlib import Path
from typing import Union

import yaml
from pydantic import ValidationError

from .models import TimelineConfig, QuickMilestone, Milestone


class ParserError(Exception):
    """Custom exception for parsing errors."""
    
    def __init__(self, message: str, details: list[str] | None = None):
        super().__init__(message)
        self.details = details or []


def parse_file(file_path: Union[str, Path]) -> TimelineConfig:
    """
    Parse a YAML or JSON file into a TimelineConfig.
    
    Args:
        file_path: Path to the configuration file.
        
    Returns:
        Validated TimelineConfig object.
        
    Raises:
        ParserError: If the file cannot be read or parsed.
    """
    path = Path(file_path)
    
    if not path.exists():
        raise ParserError(f"File not found: {path}")
    
    if not path.is_file():
        raise ParserError(f"Not a file: {path}")
    
    suffix = path.suffix.lower()
    
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        raise ParserError(f"Failed to read file: {e}")
    
    if suffix in (".yaml", ".yml"):
        return parse_yaml(content)
    elif suffix == ".json":
        return parse_json(content)
    elif suffix == ".toon":
        return parse_toon(content)
    else:
        # Try YAML first (it's a superset of JSON)
        try:
            return parse_yaml(content)
        except ParserError:
            try:
                return parse_json(content)
            except ParserError:
                return parse_toon(content)


def parse_yaml(content: str) -> TimelineConfig:
    """
    Parse YAML content into a TimelineConfig.
    
    Args:
        content: YAML string content.
        
    Returns:
        Validated TimelineConfig object.
        
    Raises:
        ParserError: If the YAML is invalid or doesn't match schema.
    """
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ParserError(f"Invalid YAML: {e}")
    
    if data is None:
        raise ParserError("Empty YAML file")
    
    if not isinstance(data, dict):
        raise ParserError("YAML must contain a mapping/dictionary at the root level")
    
    return _validate_config(data)


def parse_json(content: str) -> TimelineConfig:
    """
    Parse JSON content into a TimelineConfig.
    
    Args:
        content: JSON string content.
        
    Returns:
        Validated TimelineConfig object.
        
    Raises:
        ParserError: If the JSON is invalid or doesn't match schema.
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ParserError(f"Invalid JSON: {e}")
    
    if not isinstance(data, dict):
        raise ParserError("JSON must contain an object at the root level")
    
    return _validate_config(data)


def parse_toon(content: str) -> TimelineConfig:
    """
    Parse TOON (Token-Oriented Object Notation) content into a TimelineConfig.
    
    TOON is optimized for LLMs with 30-60% token savings vs JSON.
    
    Format:
        - Simple values: `key: value`
        - Tabular arrays: `key[N]: field1 field2` followed by N data rows
        - Quoted strings for values with spaces: `"multi word value"`
        - null for empty values
    
    Args:
        content: TOON string content.
        
    Returns:
        Validated TimelineConfig object.
        
    Raises:
        ParserError: If the TOON is invalid or doesn't match schema.
    """
    try:
        data = _toon_to_dict(content)
    except Exception as e:
        raise ParserError(f"Invalid TOON format: {e}")
    
    if not data:
        raise ParserError("Empty TOON content")
    
    return _validate_config(data)


def _toon_to_dict(content: str) -> dict:
    """
    Convert TOON format to Python dictionary.
    
    Handles:
    - Simple key: value pairs
    - Tabular arrays with field headers
    - Quoted strings
    - Nested objects via indentation
    """
    result = {}
    lines = content.strip().split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            i += 1
            continue
        
        # Check for tabular array: key[N]: field1 field2 ...
        array_match = re.match(r'^(\w+)\[(\d+)\]:\s*(.+)$', line)
        if array_match:
            key = array_match.group(1)
            count = int(array_match.group(2))
            fields = _parse_toon_fields(array_match.group(3))
            
            # Read N rows of data
            rows = []
            for j in range(count):
                i += 1
                if i < len(lines):
                    row_values = _parse_toon_row(lines[i].strip(), len(fields))
                    row_dict = {}
                    for k, field in enumerate(fields):
                        if k < len(row_values):
                            row_dict[field] = row_values[k]
                    rows.append(row_dict)
            
            result[key] = rows
            i += 1
            continue
        
        # Check for simple array: key[N]: (values on next lines)
        simple_array_match = re.match(r'^(\w+)\[(\d+)\]:?\s*$', line)
        if simple_array_match:
            key = simple_array_match.group(1)
            count = int(simple_array_match.group(2))
            
            values = []
            for j in range(count):
                i += 1
                if i < len(lines):
                    values.append(_parse_toon_value(lines[i].strip()))
            
            result[key] = values
            i += 1
            continue
        
        # Simple key: value pair
        kv_match = re.match(r'^(\w+):\s*(.*)$', line)
        if kv_match:
            key = kv_match.group(1)
            value_str = kv_match.group(2).strip()
            
            # Check if value is a nested object (next lines indented)
            if not value_str and i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line and (next_line.startswith('  ') or next_line.startswith('\t')):
                    # Collect nested content
                    nested_lines = []
                    i += 1
                    while i < len(lines) and (lines[i].startswith('  ') or lines[i].startswith('\t') or not lines[i].strip()):
                        if lines[i].strip():
                            # Remove one level of indentation
                            nested_lines.append(re.sub(r'^  |\t', '', lines[i]))
                        i += 1
                    result[key] = _toon_to_dict('\n'.join(nested_lines))
                    continue
            
            result[key] = _parse_toon_value(value_str)
            i += 1
            continue
        
        i += 1
    
    return result


def _parse_toon_fields(field_str: str) -> list[str]:
    """Parse space-separated field names."""
    return field_str.split()


def _parse_toon_row(row_str: str, expected_count: int) -> list:
    """Parse a TOON data row, handling quoted strings."""
    values = []
    current = ""
    in_quotes = False
    
    for char in row_str + " ":
        if char == '"' and not in_quotes:
            in_quotes = True
        elif char == '"' and in_quotes:
            in_quotes = False
            values.append(current)
            current = ""
        elif char == ' ' and not in_quotes:
            if current:
                values.append(_parse_toon_value(current))
                current = ""
        else:
            current += char
    
    return values


def _parse_toon_value(value_str: str):
    """Parse a single TOON value to appropriate Python type."""
    if not value_str:
        return None
    
    # Remove quotes if present
    if value_str.startswith('"') and value_str.endswith('"'):
        return value_str[1:-1]
    
    # Handle special values
    if value_str.lower() == 'null' or value_str.lower() == 'none':
        return None
    if value_str.lower() == 'true':
        return True
    if value_str.lower() == 'false':
        return False
    
    # Try numeric conversion
    try:
        if '.' in value_str:
            return float(value_str)
        return int(value_str)
    except ValueError:
        pass
    
    return value_str


def _validate_config(data: dict) -> TimelineConfig:
    """
    Validate a dictionary against the TimelineConfig schema.
    
    Args:
        data: Dictionary containing timeline configuration.
        
    Returns:
        Validated TimelineConfig object.
        
    Raises:
        ParserError: If validation fails.
    """
    try:
        return TimelineConfig(**data)
    except ValidationError as e:
        errors = []
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"  {loc}: {msg}")
        raise ParserError("Validation failed:", errors)


def parse_quick_milestones(milestone_strings: list[str]) -> list[Milestone]:
    """
    Parse quick inline milestone strings.
    
    Args:
        milestone_strings: List of strings in format 'DATE:TITLE'.
        
    Returns:
        List of Milestone objects.
        
    Raises:
        ParserError: If any milestone string is invalid.
    """
    milestones = []
    errors = []
    
    for i, s in enumerate(milestone_strings):
        try:
            quick = QuickMilestone.from_string(s)
            milestones.append(quick.to_milestone())
        except ValueError as e:
            errors.append(f"  Milestone {i + 1}: {e}")
        except Exception as e:
            errors.append(f"  Milestone {i + 1}: Failed to parse - {e}")
    
    if errors:
        raise ParserError("Failed to parse milestones:", errors)
    
    return milestones


def create_config_from_quick(
    milestones: list[Milestone],
    title: str = "Timeline",
    style: str = "horizontal",
    scale: str = "monthly",
    theme: str = "minimal",
    output_format: str = "png",
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    duration: float = 5.0,
    transparent: bool = False,
) -> TimelineConfig:
    """
    Create a TimelineConfig from quick milestone inputs.
    
    Args:
        milestones: List of parsed milestones.
        title: Timeline title.
        style: Timeline style name.
        scale: Time scale name.
        theme: Theme name.
        output_format: Output format.
        width: Output width.
        height: Output height.
        fps: Frames per second for animations.
        duration: Animation duration in seconds.
        transparent: Use transparent background.
        
    Returns:
        TimelineConfig object.
    """
    return TimelineConfig(
        title=title,
        style=style,
        scale=scale,
        theme=theme,
        milestones=milestones,
        output={
            "format": output_format,
            "width": width,
            "height": height,
            "fps": fps,
            "duration": duration,
            "transparent": transparent,
        },
    )

