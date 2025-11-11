import zipfile
import os
import uuid
from lxml import etree as ET
from typing import Dict, List
from datetime import datetime

class VisioGenerator:
    """Generate .vsdx (Visio) files from detected shapes and connectors"""
    
    # Visio namespaces
    NAMESPACES = {
        'visio': 'http://schemas.microsoft.com/office/visio/2012/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'rel': 'http://schemas.openxmlformats.org/package/2006/relationships'
    }
    
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.shape_id_counter = 1
        self.connector_id_counter = 1000
        
    def create_visio_file(self, data: Dict) -> str:
        """Create a complete .vsdx file from processed image data"""
        temp_dir = f"/tmp/visio_{uuid.uuid4().hex}"
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Create directory structure
            self._create_directory_structure(temp_dir)
            
            # Create content files
            self._create_content_types(temp_dir)
            self._create_rels(temp_dir)
            self._create_app_xml(temp_dir)
            self._create_core_xml(temp_dir)
            self._create_document_xml(temp_dir, data)
            self._create_pages_xml(temp_dir, data)
            self._create_masters_xml(temp_dir)
            
            # Create zip file (vsdx is a zip)
            with zipfile.ZipFile(self.output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
            
            return self.output_path
        finally:
            # Cleanup temp directory
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def _create_directory_structure(self, base_dir: str):
        """Create the required directory structure for .vsdx"""
        dirs = [
            '_rels',
            'docProps',
            'visio',
            'visio/_rels',
            'visio/pages',
            'visio/pages/_rels',
            'visio/masters',
            'visio/masters/_rels'
        ]
        for d in dirs:
            os.makedirs(os.path.join(base_dir, d), exist_ok=True)
    
    def _create_content_types(self, base_dir: str):
        """Create [Content_Types].xml"""
        root = ET.Element('Types', xmlns='http://schemas.openxmlformats.org/package/2006/content-types')
        
        defaults = [
            ('rels', 'application/vnd.openxmlformats-package.relationships+xml'),
            ('xml', 'application/xml')
        ]
        
        for ext, content_type in defaults:
            ET.SubElement(root, 'Default', Extension=ext, ContentType=content_type)
        
        overrides = [
            ('/docProps/app.xml', 'application/vnd.openxmlformats-officedocument.extended-properties+xml'),
            ('/docProps/core.xml', 'application/vnd.openxmlformats-package.core-properties+xml'),
            ('/visio/document.xml', 'application/vnd.ms-visio.drawing.main+xml'),
            ('/visio/pages/pages.xml', 'application/vnd.ms-visio.pages+xml'),
            ('/visio/pages/page1.xml', 'application/vnd.ms-visio.page+xml'),
            ('/visio/masters/masters.xml', 'application/vnd.ms-visio.masters+xml')
        ]
        
        for part_name, content_type in overrides:
            ET.SubElement(root, 'Override', PartName=part_name, ContentType=content_type)
        
        self._write_xml(root, os.path.join(base_dir, '[Content_Types].xml'))
    
    def _create_rels(self, base_dir: str):
        """Create _rels/.rels"""
        root = ET.Element('Relationships', xmlns=self.NAMESPACES['rel'])
        
        relationships = [
            ('rId1', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties', 'docProps/app.xml'),
            ('rId2', 'http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties', 'docProps/core.xml'),
            ('rId3', 'http://schemas.microsoft.com/visio/2010/relationships/document', 'visio/document.xml')
        ]
        
        for rid, rel_type, target in relationships:
            ET.SubElement(root, 'Relationship', Id=rid, Type=rel_type, Target=target)
        
        self._write_xml(root, os.path.join(base_dir, '_rels', '.rels'))
    
    def _create_app_xml(self, base_dir: str):
        """Create docProps/app.xml"""
        root = ET.Element('Properties', xmlns='http://schemas.openxmlformats.org/officeDocument/2006/extended-properties')
        ET.SubElement(root, 'Application').text = 'Microsoft Visio'
        ET.SubElement(root, 'Template').text = 'Basic Diagram.vstx'
        
        self._write_xml(root, os.path.join(base_dir, 'docProps', 'app.xml'))
    
    def _create_core_xml(self, base_dir: str):
        """Create docProps/core.xml"""
        root = ET.Element('coreProperties', 
                         xmlns='http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
                         nsmap={'dc': 'http://purl.org/dc/elements/1.1/',
                               'dcterms': 'http://purl.org/dc/terms/',
                               'xsi': 'http://www.w3.org/2001/XMLSchema-instance'})
        
        ET.SubElement(root, '{http://purl.org/dc/elements/1.1/}creator').text = 'Image to Visio Converter'
        ET.SubElement(root, '{http://purl.org/dc/terms/}created', 
                     {'{http://www.w3.org/2001/XMLSchema-instance}type': 'dcterms:W3CDTF'}).text = datetime.utcnow().isoformat() + 'Z'
        
        self._write_xml(root, os.path.join(base_dir, 'docProps', 'core.xml'))
    
    def _create_document_xml(self, base_dir: str, data: Dict):
        """Create visio/document.xml"""
        root = ET.Element('VisioDocument', xmlns=self.NAMESPACES['visio'])
        
        doc_props = ET.SubElement(root, 'DocumentProperties')
        ET.SubElement(doc_props, 'Creator').text = 'Image to Visio Converter'
        
        # Add pages reference
        pages = ET.SubElement(root, 'Pages')
        ET.SubElement(pages, 'Page', ID='0', NameU='Page-1', Name='Page-1')
        
        self._write_xml(root, os.path.join(base_dir, 'visio', 'document.xml'))
        
        # Create document.xml.rels
        rels_root = ET.Element('Relationships', xmlns=self.NAMESPACES['rel'])
        ET.SubElement(rels_root, 'Relationship', 
                     Id='rId1', 
                     Type='http://schemas.microsoft.com/visio/2010/relationships/pages',
                     Target='pages/pages.xml')
        ET.SubElement(rels_root, 'Relationship',
                     Id='rId2',
                     Type='http://schemas.microsoft.com/visio/2010/relationships/masters',
                     Target='masters/masters.xml')
        
        self._write_xml(rels_root, os.path.join(base_dir, 'visio', '_rels', 'document.xml.rels'))
    
    def _create_pages_xml(self, base_dir: str, data: Dict):
        """Create visio/pages/pages.xml and page1.xml"""
        # pages.xml
        root = ET.Element('Pages', xmlns=self.NAMESPACES['visio'])
        ET.SubElement(root, 'Page', ID='0', NameU='Page-1', Name='Page-1')
        
        self._write_xml(root, os.path.join(base_dir, 'visio', 'pages', 'pages.xml'))
        
        # page1.xml with actual shapes
        self._create_page_content(base_dir, data)
        
        # pages.xml.rels
        rels_root = ET.Element('Relationships', xmlns=self.NAMESPACES['rel'])
        ET.SubElement(rels_root, 'Relationship',
                     Id='rId1',
                     Type='http://schemas.microsoft.com/visio/2010/relationships/page',
                     Target='page1.xml')
        
        self._write_xml(rels_root, os.path.join(base_dir, 'visio', 'pages', '_rels', 'pages.xml.rels'))
    
    def _create_page_content(self, base_dir: str, data: Dict):
        """Create the actual page content with shapes and connectors"""
        root = ET.Element('PageContents', xmlns=self.NAMESPACES['visio'])
        shapes_elem = ET.SubElement(root, 'Shapes')
        
        # Scale factor to convert pixel coordinates to Visio units (inches)
        scale_x = 8.5 / data.get('image_width', 800)  # 8.5 inches page width
        scale_y = 11.0 / data.get('image_height', 600)  # 11 inches page height
        
        # Add shapes
        for shape_data in data.get('shapes', []):
            self._add_shape(shapes_elem, shape_data, scale_x, scale_y)
        
        # Add connectors
        for connector_data in data.get('connectors', []):
            self._add_connector(shapes_elem, connector_data, scale_x, scale_y)
        
        self._write_xml(root, os.path.join(base_dir, 'visio', 'pages', 'page1.xml'))
    
    def _add_shape(self, parent: ET.Element, shape_data: Dict, scale_x: float, scale_y: float):
        """Add a shape to the page"""
        shape_id = self.shape_id_counter
        self.shape_id_counter += 1
        
        # Convert coordinates
        x = shape_data['x'] * scale_x
        y = (shape_data['y'] + shape_data['height']) * scale_y  # Visio Y is bottom-up
        width = shape_data['width'] * scale_x
        height = shape_data['height'] * scale_y
        
        shape = ET.SubElement(parent, 'Shape', 
                             ID=str(shape_id),
                             Type='Shape',
                             NameU=f"{shape_data['type']}_{shape_id}")
        
        # Add cells for position and size
        cells = [
            ('PinX', str(x + width/2)),
            ('PinY', str(y - height/2)),
            ('Width', str(width)),
            ('Height', str(height)),
            ('LocPinX', str(width/2)),
            ('LocPinY', str(height/2))
        ]
        
        for name, value in cells:
            cell = ET.SubElement(shape, 'Cell', N=name, V=value)
        
        # Add geometry based on shape type
        self._add_shape_geometry(shape, shape_data['type'], width, height)
        
        return shape
    
    def _add_shape_geometry(self, shape: ET.Element, shape_type: str, width: float, height: float):
        """Add geometry section for different shape types"""
        section = ET.SubElement(shape, 'Section', N='Geometry', IX='0')
        
        if shape_type in ['rectangle', 'square']:
            # Rectangle geometry
            ET.SubElement(section, 'Cell', N='NoFill', V='0')
            ET.SubElement(section, 'Cell', N='NoLine', V='0')
            
            row = ET.SubElement(section, 'Row', T='MoveTo', IX='1')
            ET.SubElement(row, 'Cell', N='X', V='0')
            ET.SubElement(row, 'Cell', N='Y', V='0')
            
            row = ET.SubElement(section, 'Row', T='LineTo', IX='2')
            ET.SubElement(row, 'Cell', N='X', V=str(width))
            ET.SubElement(row, 'Cell', N='Y', V='0')
            
            row = ET.SubElement(section, 'Row', T='LineTo', IX='3')
            ET.SubElement(row, 'Cell', N='X', V=str(width))
            ET.SubElement(row, 'Cell', N='Y', V=str(height))
            
            row = ET.SubElement(section, 'Row', T='LineTo', IX='4')
            ET.SubElement(row, 'Cell', N='X', V='0')
            ET.SubElement(row, 'Cell', N='Y', V=str(height))
            
            row = ET.SubElement(section, 'Row', T='LineTo', IX='5')
            ET.SubElement(row, 'Cell', N='X', V='0')
            ET.SubElement(row, 'Cell', N='Y', V='0')
        
        elif shape_type in ['circle', 'ellipse']:
            # Ellipse geometry
            ET.SubElement(section, 'Cell', N='NoFill', V='0')
            ET.SubElement(section, 'Cell', N='NoLine', V='0')
            
            row = ET.SubElement(section, 'Row', T='Ellipse', IX='1')
            ET.SubElement(row, 'Cell', N='X', V=str(width/2))
            ET.SubElement(row, 'Cell', N='Y', V=str(height/2))
            ET.SubElement(row, 'Cell', N='A', V=str(width/2))
            ET.SubElement(row, 'Cell', N='B', V='0')
            ET.SubElement(row, 'Cell', N='C', V=str(width/2))
            ET.SubElement(row, 'Cell', N='D', V=str(height))
    
    def _add_connector(self, parent: ET.Element, connector_data: Dict, scale_x: float, scale_y: float):
        """Add a connector line between shapes"""
        connector_id = self.connector_id_counter
        self.connector_id_counter += 1
        
        x1 = connector_data['start_x'] * scale_x
        y1 = connector_data['start_y'] * scale_y
        x2 = connector_data['end_x'] * scale_x
        y2 = connector_data['end_y'] * scale_y
        
        connector = ET.SubElement(parent, 'Shape',
                                 ID=str(connector_id),
                                 Type='Shape',
                                 NameU=f"Connector_{connector_id}")
        
        # Connector cells
        cells = [
            ('PinX', str((x1 + x2) / 2)),
            ('PinY', str((y1 + y2) / 2)),
            ('BeginX', str(x1)),
            ('BeginY', str(y1)),
            ('EndX', str(x2)),
            ('EndY', str(y2))
        ]
        
        for name, value in cells:
            ET.SubElement(connector, 'Cell', N=name, V=value)
    
    def _create_masters_xml(self, base_dir: str):
        """Create visio/masters/masters.xml"""
        root = ET.Element('Masters', xmlns=self.NAMESPACES['visio'])
        self._write_xml(root, os.path.join(base_dir, 'visio', 'masters', 'masters.xml'))
    
    def _write_xml(self, root: ET.Element, filepath: str):
        """Write XML element to file with proper formatting"""
        tree = ET.ElementTree(root)
        tree.write(filepath, 
                  xml_declaration=True, 
                  encoding='UTF-8', 
                  pretty_print=True)
