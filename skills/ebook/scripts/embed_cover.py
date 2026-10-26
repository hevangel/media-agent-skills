"""
Embed cover images into EPUB files.
Demonstrates proper cover embedding with EPUB2/EPUB3 compatibility.
"""

import zipfile
import shutil
import tempfile
from pathlib import Path
from lxml import etree
from typing import Union, Optional


def embed_cover_image(
    epub_path: Union[str, Path],
    cover_image_path: Union[str, Path],
    remove_existing_covers: bool = True
) -> bool:
    """
    Embed a cover image into an EPUB file.
    
    This function properly embeds a cover image by:
    1. Optionally removing all existing cover images
    2. Adding the new cover image to the EPUB
    3. Updating the OPF manifest with proper EPUB2/EPUB3 attributes
    4. Setting cover metadata reference
    
    Args:
        epub_path: Path to the EPUB file
        cover_image_path: Path to the cover image (JPG or PNG)
        remove_existing_covers: If True, removes all existing cover images first
        
    Returns:
        True if successful, False otherwise
        
    Example:
        embed_cover_image(
            'book.epub',
            'cover.jpg',
            remove_existing_covers=True
        )
    """
    epub_path = Path(epub_path)
    cover_image_path = Path(cover_image_path)
    
    if not epub_path.exists():
        print(f"Error: EPUB not found: {epub_path}")
        return False
    
    if not cover_image_path.exists():
        print(f"Error: Cover image not found: {cover_image_path}")
        return False
    
    # Determine media type
    ext = cover_image_path.suffix.lower()
    if ext in ['.jpg', '.jpeg']:
        media_type = 'image/jpeg'
        cover_filename = 'cover.jpg'
    elif ext == '.png':
        media_type = 'image/png'
        cover_filename = 'cover.png'
    else:
        print(f"Error: Unsupported image format: {ext}")
        return False
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Extract EPUB
        try:
            with zipfile.ZipFile(epub_path, 'r') as z:
                z.extractall(temp_dir_path)
        except zipfile.BadZipFile:
            print(f"Error: Invalid ZIP/EPUB file: {epub_path}")
            return False
        
        # Find OPF file via container.xml
        container_path = temp_dir_path / 'META-INF' / 'container.xml'
        if not container_path.exists():
            print("Error: No container.xml found - not a valid EPUB")
            return False
        
        container_tree = etree.parse(str(container_path))
        container_root = container_tree.getroot()
        
        opf_relative_path = container_root.xpath(
            '//n:rootfile/@full-path',
            namespaces={'n': 'urn:oasis:names:tc:opendocument:xmlns:container'}
        )[0]
        
        opf_path = temp_dir_path / opf_relative_path
        opf_dir = opf_path.parent
        
        # Remove existing cover images if requested
        if remove_existing_covers:
            removed = []
            for img_file in opf_dir.rglob('*'):
                if img_file.is_file():
                    name_lower = img_file.name.lower()
                    if 'cover' in name_lower and name_lower.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        removed.append(img_file.name)
                        img_file.unlink()
            if removed:
                print(f"Removed existing covers: {removed}")
        
        # Copy new cover image
        new_cover_path = opf_dir / cover_filename
        shutil.copy2(cover_image_path, new_cover_path)
        
        # Parse and update OPF
        opf_tree = etree.parse(str(opf_path))
        opf_root = opf_tree.getroot()
        
        opf_ns = 'http://www.idpf.org/2007/opf'
        
        metadata = opf_root.find('.//{%s}metadata' % opf_ns)
        manifest = opf_root.find('.//{%s}manifest' % opf_ns)
        
        if metadata is None or manifest is None:
            print("Error: Invalid OPF structure")
            return False
        
        # Remove old cover meta references
        for meta in list(metadata.findall(f'.//{{{opf_ns}}}meta')):
            if meta.get('name') == 'cover':
                metadata.remove(meta)
        
        # Remove old cover items from manifest
        for item in list(manifest.findall(f'{{{opf_ns}}}item')):
            item_id = item.get('id', '').lower()
            href = item.get('href', '').lower()
            if ('cover' in item_id or 'cover' in href) and href.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                manifest.remove(item)
        
        # Add new cover item to manifest with EPUB3 properties
        cover_item = etree.SubElement(manifest, f'{{{opf_ns}}}item')
        cover_item.set('id', 'cover-image')
        cover_item.set('href', cover_filename)
        cover_item.set('media-type', media_type)
        cover_item.set('properties', 'cover-image')  # EPUB3 standard
        
        # Add cover meta for EPUB2 compatibility
        cover_meta = etree.SubElement(metadata, f'{{{opf_ns}}}meta')
        cover_meta.set('name', 'cover')
        cover_meta.set('content', 'cover-image')
        
        # Write updated OPF
        opf_tree.write(str(opf_path), encoding='utf-8', xml_declaration=True, pretty_print=True)
        
        # Repack EPUB
        with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as z:
            # Mimetype first, uncompressed (EPUB spec requirement)
            mimetype_path = temp_dir_path / 'mimetype'
            if mimetype_path.exists():
                z.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)
            
            # All other files
            for file_path in temp_dir_path.rglob('*'):
                if file_path.is_file() and file_path.name != 'mimetype':
                    arcname = str(file_path.relative_to(temp_dir_path))
                    z.write(file_path, arcname)
        
        return True


def get_cover_info(epub_path: Union[str, Path]) -> Optional[dict]:
    """
    Get information about the cover image in an EPUB.
    
    Args:
        epub_path: Path to the EPUB file
        
    Returns:
        Dictionary with cover info or None if no cover found
        
    Example:
        info = get_cover_info('book.epub')
        # Returns: {'filename': 'cover.jpg', 'size': 53083, 'media_type': 'image/jpeg'}
    """
    epub_path = Path(epub_path)
    
    try:
        with zipfile.ZipFile(epub_path, 'r') as z:
            covers = []
            for name in z.namelist():
                name_lower = name.lower()
                if 'cover' in name_lower and name_lower.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    info = z.getinfo(name)
                    covers.append({
                        'filename': name,
                        'size': info.file_size,
                        'media_type': 'image/jpeg' if name_lower.endswith(('.jpg', '.jpeg')) else 'image/png'
                    })
            
            if covers:
                # Return the largest cover (likely the best quality)
                return max(covers, key=lambda x: x['size'])
    except Exception as e:
        print(f"Error reading EPUB: {e}")
    
    return None


def main():
    """Example: Embed a cover image into an EPUB file."""
    from pathlib import Path
    
    # Example usage
    epub_path = Path(r"/path/to/example.epub")
    cover_path = Path(r"/path/to/example_cover.jpg")
    
    if epub_path.exists() and cover_path.exists():
        print(f"Embedding cover into: {epub_path.name}")
        if embed_cover_image(epub_path, cover_path):
            print("✓ Cover embedded successfully")
            
            # Verify
            info = get_cover_info(epub_path)
            if info:
                print(f"  Cover: {info['filename']} ({info['size']} bytes)")
        else:
            print("✗ Failed to embed cover")
    else:
        print("Example files not found. Usage:")
        print("  from embed_cover import embed_cover_image")
        print("  embed_cover_image('book.epub', 'cover.jpg')")


if __name__ == "__main__":
    main()
