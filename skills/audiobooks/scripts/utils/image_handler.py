"""
Image Handler
Handles image format conversions and manipulations.
"""

from pathlib import Path
from typing import Optional

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ImageHandler:
    """Handles image format conversions and manipulations."""

    @staticmethod
    def is_available() -> bool:
        """Check if PIL/Pillow is available."""
        return PIL_AVAILABLE

    @staticmethod
    def detect_format(image_path: str) -> Optional[str]:
        """
        Detect image format (PNG, JPEG, etc.).

        Args:
            image_path: Path to the image file

        Returns:
            Format string (e.g., 'PNG', 'JPEG') or None if detection fails
        """
        if not PIL_AVAILABLE:
            # Fallback to file extension
            ext = Path(image_path).suffix.lower()
            if ext in ['.jpg', '.jpeg']:
                return 'JPEG'
            elif ext == '.png':
                return 'PNG'
            return None

        try:
            with Image.open(image_path) as img:
                return img.format
        except Exception:
            return None

    @staticmethod
    def convert_png_to_jpg(png_path: str, jpg_path: Optional[str] = None, quality: int = 95) -> bool:
        """
        Convert a PNG image to JPEG format.

        Args:
            png_path: Path to the PNG file
            jpg_path: Path for the output JPEG file (optional, defaults to same name with .jpg)
            quality: JPEG quality (1-95, default: 95)

        Returns:
            True if conversion was successful, False otherwise
        """
        if not PIL_AVAILABLE:
            print("  Warning: PIL/Pillow not available. Cannot convert image.")
            return False

        try:
            if jpg_path is None:
                jpg_path = str(Path(png_path).with_suffix('.jpg'))

            with Image.open(png_path) as img:
                # Convert to RGB if necessary (PNG might have alpha channel)
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    # Paste with alpha mask if available
                    if img.mode in ('RGBA', 'LA'):
                        rgb_img.paste(img, mask=img.split()[-1])
                    else:
                        rgb_img.paste(img)
                    rgb_img.save(jpg_path, 'JPEG', quality=quality)
                else:
                    img.save(jpg_path, 'JPEG', quality=quality)

            return True

        except Exception as e:
            print(f"  Error converting PNG to JPEG: {e}")
            return False

    @staticmethod
    def ensure_jpg_format(image_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Ensure an image is in JPEG format, converting if necessary.

        Args:
            image_path: Path to the image file
            output_path: Path for the output file (optional)

        Returns:
            Path to the JPEG file, or None if conversion failed
        """
        format_type = ImageHandler.detect_format(image_path)

        if format_type == 'JPEG':
            return image_path

        if format_type == 'PNG':
            if output_path is None:
                output_path = str(Path(image_path).with_suffix('.jpg'))
            if ImageHandler.convert_png_to_jpg(image_path, output_path):
                return output_path

        return None

    @staticmethod
    def get_image_size(image_path: str) -> Optional[tuple]:
        """
        Get image dimensions.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (width, height) or None if detection fails
        """
        if not PIL_AVAILABLE:
            return None

        try:
            with Image.open(image_path) as img:
                return img.size
        except Exception:
            return None
