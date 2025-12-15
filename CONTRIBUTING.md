# Contributing to Timeline Generator MCP

Thank you for your interest in contributing to Timeline Generator! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to maintain a welcoming and inclusive community.

## How to Contribute

### Reporting Bugs

Before creating a bug report, please check existing issues to avoid duplicates. When creating a bug report, include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Sample configuration file if applicable
- Error messages or screenshots

### Suggesting Features

Feature suggestions are welcome! Please:

- Check existing issues/discussions first
- Describe the use case clearly
- Explain why this feature would be useful
- Consider how it fits with existing functionality

### Pull Requests

1. **Fork the repository** and create your branch from `main`:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Set up the development environment**:
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```

3. **Make your changes**:
   - Write clear, documented code
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Run tests and linting**:
   ```bash
   pytest
   ruff check .
   black --check .
   mypy timeline_generator/
   ```

5. **Commit your changes**:
   - Use clear, descriptive commit messages
   - Reference related issues when applicable

6. **Push and create a Pull Request**:
   - Provide a clear description of changes
   - Link related issues
   - Request review from maintainers

## Development Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use docstrings for public functions/classes

### Testing

- Write tests for new features
- Maintain or improve test coverage
- Run the full test suite before submitting

### Documentation

- Update README.md for user-facing changes
- Add docstrings for new functions/classes
- Include examples for new features

## Project Structure

```
timeline-generator/
├── timeline_generator/     # Main package
│   ├── cli.py             # CLI commands
│   ├── models.py          # Pydantic models
│   ├── parser.py          # Config parsing
│   ├── core/              # Core logic
│   ├── renderers/         # Timeline renderers
│   ├── themes/            # Visual themes
│   ├── animation/         # Animation support
│   ├── output/            # Export handlers
│   └── mcp_server.py      # MCP server
├── tests/                 # Test suite
├── examples/              # Example configs
└── output/                # Generated files
```

## Adding New Features

### New Timeline Style

1. Create renderer in `timeline_generator/renderers/`
2. Inherit from `BaseRenderer`
3. Implement required methods
4. Add to `TimelineStyle` enum
5. Register in renderer factory
6. Add tests and example

### New Theme

1. Create theme in `timeline_generator/themes/`
2. Inherit from `Theme`
3. Define color palette and fonts
4. Add to `ThemeName` enum
5. Register in themes `__init__.py`

### New Output Format

1. Update `OutputFormat` enum
2. Add exporter in `output/`
3. Update CLI handlers
4. Add tests

## Questions?

Feel free to open an issue for questions or join discussions.

Thank you for contributing!

