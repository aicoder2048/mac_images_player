import pygame
import os
import random
from typing import List, Optional
from src.logger import error


class MusicPlayer:
    def __init__(self):
        # Initialize pygame properly
        pygame.init()
        pygame.mixer.init()
        self.music_files: List[str] = []
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False  # Track pause state separately
        self.volume = 0.7  # Default volume
        self.music_ended = False
        
    def load_music_file(self, file_path: str) -> bool:
        """Load a single music file"""
        if not file_path or not os.path.exists(file_path):
            return False
            
        supported_formats = {'.mp3', '.wav', '.ogg', '.flac'}
        if any(file_path.lower().endswith(fmt) for fmt in supported_formats):
            self.music_files = [file_path]  # Single file in list
            self.current_index = 0
            return True
        return False
        
    def load_music_directory(self, directory: str) -> bool:
        """Load all music files from the given directory"""
        if not directory or not os.path.exists(directory):
            return False
            
        supported_formats = {'.mp3', '.wav', '.ogg', '.flac'}
        self.music_files = []
        
        for file in os.listdir(directory):
            if any(file.lower().endswith(fmt) for fmt in supported_formats):
                self.music_files.append(os.path.join(directory, file))
                
        if self.music_files:
            random.shuffle(self.music_files)
            return True
        return False
        
    def play(self):
        """Start playing music"""
        if not self.music_files:
            return
            
        if not self.is_playing:
            self._play_current_track()
            self.is_playing = True
            
    def _play_current_track(self):
        """Play the current track"""
        if self.current_index < len(self.music_files):
            try:
                pygame.mixer.music.load(self.music_files[self.current_index])
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play()
                self.music_ended = False
                self.is_paused = False
            except pygame.error as e:
                error(f"Error playing {self.music_files[self.current_index]}: {e}")
                self.next_track()
                
    def next_track(self):
        """Play the next track"""
        if len(self.music_files) > 1:
            self.current_index = (self.current_index + 1) % len(self.music_files)
        else:
            # For single file, restart from beginning
            self.current_index = 0
        if self.is_playing:
            self._play_current_track()
            
    def stop(self):
        """Stop playing music"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        
    def pause(self):
        """Pause the music"""
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            
    def unpause(self):
        """Resume the music"""
        if self.is_playing and self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)
        
    def check_music_end(self) -> bool:
        """Check if current track has ended and play next if needed"""
        if self.is_playing and not self.is_paused and not pygame.mixer.music.get_busy():
            if not self.music_ended:
                self.music_ended = True
                self.next_track()
                return True
        return False
        
    def get_current_track_name(self) -> Optional[str]:
        """Get the name of the currently playing track"""
        if self.current_index < len(self.music_files):
            return os.path.basename(self.music_files[self.current_index])
        return None