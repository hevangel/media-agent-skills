"""
Update EPUB series metadata by modifying the OPF file.
Adds or updates calibre:series and calibre:series_index meta tags.
"""

import zipfile
import shutil
from pathlib import Path
from lxml import etree
import tempfile
from typing import Union, Optional


def update_epub_series(
    epub_path: Union[str, Path],
    series_name: str,
    series_index: Union[int, float],
    create_backup: bool = True
) -> bool:
    """
    Update EPUB series metadata by adding/modifying calibre:series meta tags.
    
    Args:
        epub_path: Path to the EPUB file
        series_name: Name of the series
        series_index: Position in the series (e.g., 1, 2, 3.5)
        create_backup: Whether to create a backup of the original file
        
    Returns:
        True if successful, False otherwise
        
    Example:
        update_epub_series('dune.epub', 'Dune', 1)
    """
    epub_path = Path(epub_path)
    
    if not epub_path.exists():
        print(f"Error: File not found: {epub_path}")
        return False
    
    # Create a backup
    if create_backup:
        backup_path = Path(str(epub_path) + ".backup")
        shutil.copy2(epub_path, backup_path)
        print(f"Created backup: {backup_path}")
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        try:
            # Extract the EPUB
            with zipfile.ZipFile(epub_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir_path)
            
            # Find and read the OPF file
            container_path = temp_dir_path / 'META-INF' / 'container.xml'
            container_tree = etree.parse(str(container_path))
            container_root = container_tree.getroot()
            
            opf_relative_path = container_root.xpath(
                '//n:rootfile/@full-path',
                namespaces={'n': 'urn:oasis:names:tc:opendocument:xmlns:container'}
            )[0]
            
            opf_path = temp_dir_path / opf_relative_path
            
            # Parse the OPF file
            opf_tree = etree.parse(str(opf_path))
            opf_root = opf_tree.getroot()
            
            # Define namespaces
            opf_ns = 'http://www.idpf.org/2007/opf'
            
            # Find metadata section
            metadata = opf_root.find('.//{%s}metadata' % opf_ns)
            if metadata is None:
                print("Error: Could not find metadata section")
                return False
            
            # Remove existing series metadata if present
            for meta in metadata.findall('.//{%s}meta' % opf_ns):
                name_attr = meta.get('name')
                if name_attr in ['calibre:series', 'calibre:series_index']:
                    metadata.remove(meta)
            
            # Add new series metadata
            series_meta = etree.SubElement(metadata, f'{{{opf_ns}}}meta')
            series_meta.set('name', 'calibre:series')
            series_meta.set('content', str(series_name))
            
            series_index_meta = etree.SubElement(metadata, f'{{{opf_ns}}}meta')
            series_index_meta.set('name', 'calibre:series_index')
            series_index_meta.set('content', str(series_index))
            
            # Write the modified OPF back
            opf_tree.write(
                str(opf_path),
                encoding='utf-8',
                xml_declaration=True,
                pretty_print=True
            )
            
            # Create a new EPUB with the modified files
            with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as epub_zip:
                # First add mimetype (uncompressed, must be first)
                mimetype_path = temp_dir_path / 'mimetype'
                if mimetype_path.exists():
                    epub_zip.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)
                
                # Then add all other files
                for file_path in temp_dir_path.rglob('*'):
                    if file_path.is_file() and file_path.name != 'mimetype':
                        arcname = str(file_path.relative_to(temp_dir_path))
                        epub_zip.write(file_path, arcname)
            
            print(f"Successfully updated series metadata:")
            print(f"  Series: {series_name}")
            print(f"  Index: {series_index}")
            print(f"  File: {epub_path}")
            return True
            
        except Exception as e:
            print(f"Error updating series metadata: {str(e)}")
            return False


def get_epub_series(epub_path: Union[str, Path]) -> Optional[dict]:
    """
    Extract series metadata from an EPUB file.
    
    Args:
        epub_path: Path to the EPUB file
        
    Returns:
        Dictionary with 'series' and 'series_index' keys, or None if not found
    """
    epub_path = Path(epub_path)
    
    try:
        with zipfile.ZipFile(epub_path, 'r') as zip_file:
            # Find the OPF file
            container_path = 'META-INF/container.xml'
            container_content = zip_file.read(container_path)
            container_root = etree.fromstring(container_content)
            
            # Get OPF path
            opf_path = container_root.xpath(
                '//n:rootfile/@full-path',
                namespaces={'n': 'urn:oasis:names:tc:opendocument:xmlns:container'}
            )[0]
            
            # Read OPF content
            opf_content = zip_file.read(opf_path)
            opf_root = etree.fromstring(opf_content)
            
            # Find series metadata
            opf_ns = {'opf': 'http://www.idpf.org/2007/opf'}
            
            series_name = None
            series_index = None
            
            for meta in opf_root.xpath('//opf:meta[@name="calibre:series"]', namespaces=opf_ns):
                series_name = meta.get('content')
            
            for meta in opf_root.xpath('//opf:meta[@name="calibre:series_index"]', namespaces=opf_ns):
                series_index = meta.get('content')
            
            if series_name or series_index:
                return {
                    'series': series_name,
                    'series_index': series_index
                }
            
            return None
            
    except Exception as e:
        print(f"Error reading series metadata: {str(e)}")
        return None


def main():
    """Example: Update series metadata for EPUB files."""
    
    # Example 1: Update single book
    epub_path = Path(r"/path/to/calibre-library/Frank Herbert/Dune - Frank Herbert.epub")
    
    if epub_path.exists():
        print("="*80)
        print("Example 1: Adding series metadata to Dune")
        print("="*80)
        
        # Check current series metadata
        current = get_epub_series(epub_path)
        if current:
            print(f"Current series metadata: {current}")
        else:
            print("No series metadata found")
        
        # Update series metadata
        update_epub_series(epub_path, "Dune", 1)
        
        # Verify update
        updated = get_epub_series(epub_path)
        print(f"Updated series metadata: {updated}")
    else:
        print(f"File not found: {epub_path}")
    
    print("\n" + "="*80)
    print("Series metadata update complete!")
    print("="*80)


if __name__ == "__main__":
    main()
