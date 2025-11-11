import cv2
import numpy as np
from PIL import Image
from typing import List, Dict, Tuple

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

class ShapeDetector:
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.image = cv2.imread(image_path)
        self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.shapes = []
        self.connectors = []
        self.text_elements = []
        
    def preprocess_image(self):
        """Preprocess image for better shape detection"""
        blurred = cv2.GaussianBlur(self.gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return thresh
    
    def detect_shapes(self) -> List[Dict]:
        """Detect shapes in the image"""
        thresh = self.preprocess_image()
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        shapes = []
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area < 500:  # Filter out noise
                continue
            
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
            x, y, w, h = cv2.boundingRect(contour)
            
            shape_type = self._classify_shape(approx, area, w, h)
            
            shapes.append({
                'id': f'shape_{i}',
                'type': shape_type,
                'x': int(x),
                'y': int(y),
                'width': int(w),
                'height': int(h),
                'center_x': int(x + w/2),
                'center_y': int(y + h/2),
                'vertices': len(approx)
            })
        
        self.shapes = shapes
        return shapes
    
    def _classify_shape(self, approx, area, width, height) -> str:
        """Classify shape based on vertices and aspect ratio"""
        vertices = len(approx)
        aspect_ratio = float(width) / height if height > 0 else 0
        
        if vertices == 3:
            return 'triangle'
        elif vertices == 4:
            if 0.95 <= aspect_ratio <= 1.05:
                return 'square'
            else:
                return 'rectangle'
        elif vertices == 5:
            return 'pentagon'
        elif vertices == 6:
            return 'hexagon'
        elif vertices > 6:
            circularity = 4 * np.pi * area / (cv2.arcLength(approx, True) ** 2)
            if circularity > 0.8:
                return 'circle'
            else:
                return 'ellipse'
        else:
            return 'polygon'
    
    def detect_connectors(self) -> List[Dict]:
        """Detect lines/connectors between shapes"""
        edges = cv2.Canny(self.gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=50, maxLineGap=10)
        
        connectors = []
        if lines is not None:
            for i, line in enumerate(lines):
                x1, y1, x2, y2 = line[0]
                
                # Check if line connects two shapes
                start_shape = self._find_nearest_shape(x1, y1)
                end_shape = self._find_nearest_shape(x2, y2)
                
                if start_shape and end_shape and start_shape != end_shape:
                    connectors.append({
                        'id': f'connector_{i}',
                        'from_shape': start_shape,
                        'to_shape': end_shape,
                        'start_x': int(x1),
                        'start_y': int(y1),
                        'end_x': int(x2),
                        'end_y': int(y2)
                    })
        
        self.connectors = connectors
        return connectors
    
    def _find_nearest_shape(self, x: int, y: int, threshold: int = 30) -> str:
        """Find the nearest shape to a point"""
        min_distance = float('inf')
        nearest_shape = None
        
        for shape in self.shapes:
            cx, cy = shape['center_x'], shape['center_y']
            distance = np.sqrt((x - cx)**2 + (y - cy)**2)
            
            if distance < min_distance and distance < threshold:
                min_distance = distance
                nearest_shape = shape['id']
        
        return nearest_shape
    
    def extract_text(self) -> List[Dict]:
        """Extract text from image using OCR"""
        if not TESSERACT_AVAILABLE:
            print("Tesseract OCR not available, skipping text extraction")
            return []
        
        try:
            # Use pytesseract to extract text with bounding boxes
            data = pytesseract.image_to_data(self.image, output_type=pytesseract.Output.DICT)
            
            text_elements = []
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 60:  # Confidence threshold
                    text = data['text'][i].strip()
                    if text:
                        text_elements.append({
                            'id': f'text_{i}',
                            'text': text,
                            'x': int(data['left'][i]),
                            'y': int(data['top'][i]),
                            'width': int(data['width'][i]),
                            'height': int(data['height'][i]),
                            'confidence': int(data['conf'][i])
                        })
            
            self.text_elements = text_elements
            return text_elements
        except Exception as e:
            print(f"OCR Error: {e}")
            return []
    
    def process(self) -> Dict:
        """Process image and return all detected elements"""
        shapes = self.detect_shapes()
        connectors = self.detect_connectors()
        text_elements = self.extract_text()
        
        return {
            'shapes': shapes,
            'connectors': connectors,
            'text_elements': text_elements,
            'image_width': self.image.shape[1],
            'image_height': self.image.shape[0]
        }
