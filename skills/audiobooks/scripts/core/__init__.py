"""Core modules for audiobook cover management."""

from .scanner import AudiobookScanner
from .embedder import CoverEmbedder
from .downloader import CoverDownloader

__all__ = ['AudiobookScanner', 'CoverEmbedder', 'CoverDownloader']
