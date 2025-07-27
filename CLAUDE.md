# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QiQi Player is a PyQt6-based image slideshow application with background music support. It displays multiple images simultaneously with automatic transitions and allows users to pin specific images.

## Development Commands

### Running the Application
```bash
# ALWAYS use uv to run Python scripts
uv run python main.py
uv run python create_test_images.py
```

**Important**: Always use `uv run` when executing Python scripts in this project to ensure proper environment and dependency management.

### Installing Dependencies
```bash
# Using uv (preferred) - installs from pyproject.toml
uv sync

# Alternative: install in editable mode
uv pip install -e .
```

### Python Environment
- Requires Python >= 3.13
- Dependencies defined in pyproject.toml: PyQt6, Pygame, Pillow
- Uses uv for package management

## Architecture

### Core Components

1. **Entry Point** (`main.py`): Launches the configuration dialog, then creates the main window
2. **Main Window** (`src/main_window.py`): 
   - Manages the overall application state
   - Handles music playback via MusicPlayer
   - Controls pause/resume for both images and music (spacebar handling)
   - Provides menu bar with music selection history
   - Manages fullscreen mode (F11/ESC shortcuts)

3. **Image Viewer** (`src/image_viewer.py`):
   - `ImageViewer`: Manages multiple image slots with individual timers
   - `ImageSlot`: Handles smooth transitions between images with fade effects
   - `ImageLabel`: Custom QLabel that maintains aspect ratio
   - Click-to-pin functionality prevents specific images from changing
   - Each slot has independent timer (3-5 second intervals)

4. **Music Player** (`src/music_player.py`): Pygame-based audio playback with loop support

5. **Config Dialog** (`src/config_dialog.py`): 
   - Initial setup for image directory, music file, and image count (2-4 panes)
   - Maintains history of selected directories and music files
   - Validates image directory contains supported formats

6. **Utilities** (`utils/`):
   - `image_utils.py`: Image loading with EXIF orientation handling, format conversion
   - `animation_utils.py`: Animation helpers for transitions

### Key Features

- **Parallel Image Display**: Each slot operates independently with its own timer (3-5 second intervals)
- **Smooth Transitions**: Images fade in/out with optional rotation effects
- **Pin Functionality**: Click any image to pin it (prevents automatic changes)
- **Unified Pause**: Spacebar pauses both images and music together
- **Music History**: Quick access to recently played music files

### State Management

- Global pause state tracks whether display is paused
- Individual slot timers manage image rotation
- Music state tracked separately to handle pause/resume correctly
- Pinned state per image slot

## Important Guidelines

### UTF-8 and Character Encoding
- **Avoid using emojis in documentation files** (README.md, CLAUDE.md, etc.) as they can cause UTF-8 encoding issues
- Use ASCII characters only for better compatibility across different text editors
- If visual indicators are needed, use ASCII art or describe them in text
- When writing files, ensure they contain only valid UTF-8 characters

### Image Format Support
- Supported formats: .jpg, .jpeg, .png, .bmp, .gif, .webp, .tiff, .tif
- EXIF orientation is automatically handled for JPEG images
- Images are converted to appropriate Qt formats (RGBA/RGB)

### Audio Format Support
- Supported formats: .mp3, .wav, .ogg, .flac
- Music loops automatically when track ends

### Settings Persistence
- Uses QSettings to store configuration history
- Stores last 10 entries for both image directories and music files
- Settings stored under 'ImagePlayer' application name