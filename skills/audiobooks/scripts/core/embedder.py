"""
Cover Embedder
Embeds cover art into audio files.
"""

import base64
from pathlib import Path
from typing import Optional

try:
    from mutagen import File as MutagenFile
    from mutagen.mp4 import MP4, MP4Cover
    from mutagen.mp3 import MP3
    from mutagen.id3 import APIC
    from mutagen.flac import FLAC, Picture
    from mutagen.oggvorbis import OggVorbis
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


class CoverEmbedder:
    """Embeds cover art into audio files."""

    def __init__(self):
        if not MUTAGEN_AVAILABLE:
            print("Warning: mutagen library not available. Install with: uv add mutagen")
            print("Cover embedding will not work without mutagen.")

    @staticmethod
    def is_available() -> bool:
        """Check if mutagen is available."""
        return MUTAGEN_AVAILABLE

    def embed_cover_in_file(self, audio_file_path: str, cover_image_path: str) -> bool:
        """
        Embed cover art into a single audio file.

        Args:
            audio_file_path: Path to the audio file
            cover_image_path: Path to the cover image

        Returns:
            True if embedding was successful, False otherwise
        """
        if not MUTAGEN_AVAILABLE:
            return False

        try:
            # Read cover image data
            with open(cover_image_path, 'rb') as f:
                cover_data = f.read()

            # Load audio file
            audio = MutagenFile(audio_file_path)
            if audio is None:
                return False

            # Detect image format
            if cover_data[:8] == b'\x89PNG\r\n\x1a\n':
                mime_type = 'image/png'
                mp4_format = MP4Cover.FORMAT_PNG
            else:
                mime_type = 'image/jpeg'
                mp4_format = MP4Cover.FORMAT_JPEG

            # Embed based on audio file type
            if isinstance(audio, MP4):
                audio.tags['covr'] = [MP4Cover(cover_data, imageformat=mp4_format)]
                audio.save()
                return True

            elif isinstance(audio, MP3):
                if audio.tags is None:
                    audio.add_tags()
                audio.tags.delall('APIC')
                audio.tags.add(APIC(
                    encoding=3,
                    mime=mime_type,
                    type=3,  # Cover (front)
                    desc='Cover',
                    data=cover_data
                ))
                audio.save()
                return True

            elif isinstance(audio, FLAC):
                audio.clear_pictures()
                picture = Picture()
                picture.data = cover_data
                picture.type = 3  # Cover (front)
                picture.mime = mime_type
                picture.desc = 'Cover'
                audio.add_picture(picture)
                audio.save()
                return True

            elif isinstance(audio, OggVorbis):
                picture = Picture()
                picture.data = cover_data
                picture.type = 3  # Cover (front)
                picture.mime = mime_type
                picture.desc = 'Cover'
                picture_data = base64.b64encode(picture.write()).decode('ascii')
                audio.pop('metadata_block_picture', None)
                audio['metadata_block_picture'] = [picture_data]
                audio.save()
                return True

            else:
                return False

        except Exception as e:
            print(f"    Error embedding in {Path(audio_file_path).name}: {str(e)[:80]}")
            return False

    def embed_cover_in_audiobook(self, audiobook_path: str, cover_image_path: str, max_files: int = 5) -> int:
        """
        Embed cover art into multiple audio files in an audiobook directory.

        Args:
            audiobook_path: Path to the audiobook directory
            cover_image_path: Path to the cover image
            max_files: Maximum number of files to embed cover in (default: 5)

        Returns:
            Number of files successfully embedded
        """
        if not MUTAGEN_AVAILABLE:
            print("  ⚠ Mutagen not available - skipping embedding")
            return 0

        audio_extensions = ['.m4a', '.m4b', '.mp3', '.flac', '.ogg']
        audio_files = []

        # Find all audio files
        audiobook_dir = Path(audiobook_path)
        for file_path in audiobook_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                audio_files.append(file_path)

        audio_files.sort()

        # Embed cover in first N files
        embedded_count = 0
        for audio_file in audio_files[:max_files]:
            if self.embed_cover_in_file(str(audio_file), cover_image_path):
                embedded_count += 1
                print(f"    ✓ Embedded in: {audio_file.name}")
            else:
                print(f"    ✗ Failed: {audio_file.name}")

        if len(audio_files) > max_files:
            print(f"    (Skipped {len(audio_files) - max_files} remaining files)")

        return embedded_count

    def embed_cover_from_data(self, audio_file_path: str, cover_data: bytes) -> bool:
        """
        Embed cover art from binary data into an audio file.

        Args:
            audio_file_path: Path to the audio file
            cover_data: Binary cover image data

        Returns:
            True if embedding was successful, False otherwise
        """
        if not MUTAGEN_AVAILABLE:
            return False

        try:
            audio = MutagenFile(audio_file_path)
            if audio is None:
                return False

            # Detect image format
            if cover_data[:8] == b'\x89PNG\r\n\x1a\n':
                mime_type = 'image/png'
                mp4_format = MP4Cover.FORMAT_PNG
            else:
                mime_type = 'image/jpeg'
                mp4_format = MP4Cover.FORMAT_JPEG

            # Embed based on audio file type
            if isinstance(audio, MP4):
                audio.tags['covr'] = [MP4Cover(cover_data, imageformat=mp4_format)]
                audio.save()
                return True

            elif isinstance(audio, MP3):
                if audio.tags is None:
                    audio.add_tags()
                audio.tags.delall('APIC')
                audio.tags.add(APIC(
                    encoding=3,
                    mime=mime_type,
                    type=3,
                    desc='Cover',
                    data=cover_data
                ))
                audio.save()
                return True

            elif isinstance(audio, FLAC):
                audio.clear_pictures()
                picture = Picture()
                picture.data = cover_data
                picture.type = 3
                picture.mime = mime_type
                audio.add_picture(picture)
                audio.save()
                return True

            elif isinstance(audio, OggVorbis):
                picture = Picture()
                picture.data = cover_data
                picture.type = 3
                picture.mime = mime_type
                picture_data = base64.b64encode(picture.write()).decode('ascii')
                audio.pop('metadata_block_picture', None)
                audio['metadata_block_picture'] = [picture_data]
                audio.save()
                return True

            else:
                return False

        except Exception:
            return False
