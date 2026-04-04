"""
Update EPUB metadata by modifying the OPF file directly.
Demonstrates editing EPUB metadata using lxml and zipfile.
"""

import zipfile
import shutil
from pathlib import Path
from lxml import etree
import tempfile
from typing import Dict, Any, Union


def update_epub_metadata(epub_path: Union[str, Path], new_metadata: Dict[str, Any], create_backup: bool = True) -> bool:
    """
    Update EPUB metadata by modifying the OPF file.
    
    Args:
        epub_path: Path to the EPUB file
        new_metadata: Dictionary of metadata fields to update (e.g., {'creator': 'Author Name', 'publisher': 'Publisher'})
        create_backup: Whether to create a backup of the original file
        
    Returns:
        True if successful, False otherwise
        
    Example:
        update_epub_metadata(
            'book.epub',
            {
                'creator': 'Author Name',
                'publisher': 'Publisher Name',
                'title': 'New Title'
            }
        )
    """
    epub_path = Path(epub_path)
    
    # Create a backup
    if create_backup:
        backup_path = Path(str(epub_path) + ".backup")
        shutil.copy2(epub_path, backup_path)
        print(f"Created backup: {backup_path}")
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
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
        dc_ns = 'http://purl.org/dc/elements/1.1/'
        opf_ns = 'http://www.idpf.org/2007/opf'
        
        # Find metadata section
        metadata = opf_root.find('.//{%s}metadata' % opf_ns)
        if metadata is None:
            print("Error: Could not find metadata section")
            return False
        
        # Update or add metadata fields
        for field, value in new_metadata.items():
            if value is None:
                continue
                
            dc_element_name = f'{{{dc_ns}}}{field}'
            
            # Remove existing elements of this type
            for elem in metadata.findall(dc_element_name):
                metadata.remove(elem)
            
            # Add new element(s)
            if isinstance(value, list):
                for v in value:
                    new_elem = etree.SubElement(metadata, dc_element_name)
                    new_elem.text = str(v)
            else:
                new_elem = etree.SubElement(metadata, dc_element_name)
                new_elem.text = str(value)
        
        # Write the modified OPF back
        opf_tree.write(str(opf_path), encoding='utf-8', xml_declaration=True, pretty_print=True)
        
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
        
        print(f"Successfully updated metadata in: {epub_path}")
        return True


def extract_opf_metadata(epub_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Extract metadata directly from the OPF file in an EPUB.
    
    Args:
        epub_path: Path to the EPUB file
        
    Returns:
        Dictionary containing metadata fields
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
            
            # Extract metadata
            dc_ns = {'dc': 'http://purl.org/dc/elements/1.1/'}
            
            metadata = {}
            metadata['title'] = opf_root.xpath('//dc:title/text()', namespaces=dc_ns)
            metadata['creator'] = opf_root.xpath('//dc:creator/text()', namespaces=dc_ns)
            metadata['publisher'] = opf_root.xpath('//dc:publisher/text()', namespaces=dc_ns)
            metadata['date'] = opf_root.xpath('//dc:date/text()', namespaces=dc_ns)
            metadata['language'] = opf_root.xpath('//dc:language/text()', namespaces=dc_ns)
            metadata['identifier'] = opf_root.xpath('//dc:identifier/text()', namespaces=dc_ns)
            metadata['subject'] = opf_root.xpath('//dc:subject/text()', namespaces=dc_ns)
            metadata['description'] = opf_root.xpath('//dc:description/text()', namespaces=dc_ns)
            
            return metadata
            
    except Exception as e:
        return {"error": str(e)}


def main():
    """Example: Update metadata for specific EPUB files."""
    # Example 1: Update single author
    epub1_path = Path(r"E:\ebook\Calibre Library\libgen.li\The end of indexing (318)\The end of indexing - libgen.li.epub")
    
    if epub1_path.exists():
        print("="*80)
        print(f"Updating: {epub1_path.name}")
        print("="*80)
        
        metadata1 = {
            'creator': 'Niels Joachim Gormsen',
            'publisher': 'Columbia University Press'
        }
        update_epub_metadata(epub1_path, metadata1)
    
    # Example 2: Update multiple authors
    epub2_path = Path(r"E:\ebook\Calibre Library\Gene Kim\The DevOps Handbook_ How to Create (262)\The DevOps Handbook_ How to Cre - Gene Kim.epub")
    
    if epub2_path.exists():
        print("\n" + "="*80)
        print(f"Updating: {epub2_path.name}")
        print("="*80)
        
        metadata2 = {
            'title': 'The DevOps Handbook: How to Create World-Class Agility, Reliability, and Security in Technology Organizations',
            'creator': ['Gene Kim', 'Jez Humble', 'Patrick Debois', 'John Willis'],
            'publisher': 'IT Revolution Press'
        }
        update_epub_metadata(epub2_path, metadata2)
    
    print("\n" + "="*80)
    print("Metadata updates complete!")
    print("="*80)


if __name__ == "__main__":
    main()
