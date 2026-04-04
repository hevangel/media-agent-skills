"""
Audiobookbay data models.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AudiobookResult:
    """Represents a search result from Audiobookbay."""
    title: str
    link: str
    cover: Optional[str] = None
    language: str = "N/A"
    post_date: str = "N/A"
    format: str = "N/A"
    bitrate: str = "N/A"
    file_size: str = "N/A"
    info_hash: Optional[str] = None
    magnet_link: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "link": self.link,
            "cover": self.cover,
            "language": self.language,
            "post_date": self.post_date,
            "format": self.format,
            "bitrate": self.bitrate,
            "file_size": self.file_size,
            "info_hash": self.info_hash,
            "magnet_link": self.magnet_link,
        }

    def __str__(self) -> str:
        """String representation."""
        lines = [
            f"Title: {self.title}",
            f"Link: {self.link}",
            f"Language: {self.language}",
            f"Format: {self.format}",
            f"Bitrate: {self.bitrate}",
            f"File Size: {self.file_size}",
        ]
        if self.info_hash:
            lines.append(f"Info Hash: {self.info_hash}")
        if self.magnet_link:
            lines.append(f"Magnet Link: {self.magnet_link}")
        return "\n".join(lines)
