import pygame
import os
import random
from typing import List, Optional


class MusicPlayer:
    def __init__(self):
        # Initialize pygame properly
        pygame.init()
        pygame.mixer.init()
        self.music_files: List[str] = []
        self.current_index = 0
        self.is_playing = False
        self.volume = 0.7  # Default volume
        self.music_ended = False
        
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
            except pygame.error as e:
                print(f"Error playing {self.music_files[self.current_index]}: {e}")
                self.next_track()
                
    def next_track(self):
        """Play the next track"""
        self.current_index = (self.current_index + 1) % len(self.music_files)
        if self.is_playing:
            self._play_current_track()
            
    def stop(self):
        """Stop playing music"""
        pygame.mixer.music.stop()
        self.is_playing = False
        
    def pause(self):
        """Pause the music"""
        if self.is_playing:
            pygame.mixer.music.pause()
            
    def unpause(self):
        """Resume the music"""
        if self.is_playing:
            pygame.mixer.music.unpause()
            
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)
        
    def check_music_end(self) -> bool:
        """Check if current track has ended and play next if needed"""
        if self.is_playing and not pygame.mixer.music.get_busy():
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