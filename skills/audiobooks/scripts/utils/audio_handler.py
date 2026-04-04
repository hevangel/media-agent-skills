"""
Audio Handler
Handles audio file detection and operations.
"""

from pathlib import Path
from typing import List, Optional


class AudioHandler:
    """Handles audio file detection and operations."""

    # Supported audio file extensions
    AUDIO_EXTENSIONS = ['.m4a', '.m4b', '.mp3', '.flac', '.ogg']

    @staticmethod
    def is_audio_file(file_path: str) -> bool:
        """
        Check if a file is an audio file based on extension.

        Args:
            file_path: Path to the file

        Returns:
            True if the file is an audio file, False otherwise
        """
        return Path(file_path).suffix.lower() in AudioHandler.AUDIO_EXTENSIONS

    @staticmethod
    def find_audio_files(directory: str, recursive: bool = False) -> List[Path]:
        """
        Find all audio files in a directory.

        Args:
            directory: Path to the directory to search
            recursive: Whether to search recursively (default: False)

        Returns:
            List of Path objects for audio files
        """
        dir_path = Path(directory)
        audio_files = []

        if recursive:
            for ext in AudioHandler.AUDIO_EXTENSIONS:
                audio_files.extend(dir_path.rglob(f'*{ext}'))
        else:
            for ext in AudioHandler.AUDIO_EXTENSIONS:
                audio_files.extend(dir_path.glob(f'*{ext}'))

        return sorted(audio_files)

    @staticmethod
    def get_audio_format(file_path: str) -> Optional[str]:
        """
        Get the audio format based on file extension.

        Args:
            file_path: Path to the audio file

        Returns:
            Format string ('MP4', 'MP3', 'FLAC', 'OGG') or None if not recognized
        """
        ext = Path(file_path).suffix.lower()

        format_map = {
            '.m4a': 'MP4',
            '.m4b': 'MP4',
            '.mp3': 'MP3',
            '.flac': 'FLAC',
            '.ogg': 'OGG'
        }

        return format_map.get(ext)

    @staticmethod
    def count_audio_files(directory: str) -> int:
        """
        Count audio files in a directory (non-recursive).

        Args:
            directory: Path to the directory

        Returns:
            Number of audio files found
        """
        return len(AudioHandler.find_audio_files(directory, recursive=False))

    @staticmethod
    def get_first_audio_file(directory: str) -> Optional[Path]:
        """
        Get the first audio file in a directory (alphabetically).

        Args:
            directory: Path to the directory

        Returns:
            Path to the first audio file, or None if no audio files found
        """
        audio_files = AudioHandler.find_audio_files(directory, recursive=False)
        return audio_files[0] if audio_files else None
