# Image to Visio Converter

A powerful web-based tool that converts images of diagrams and flowcharts into fully editable Microsoft Visio (.vsdx) files. The tool uses computer vision and image processing to detect shapes, connectors, and text, then generates a professional Visio file with editable elements.

## Features

- 🎯 **Automatic Shape Detection**: Detects rectangles, circles, ellipses, triangles, and other geometric shapes
- 🔗 **Smart Connector Recognition**: Identifies and recreates connector lines between shapes
- 📝 **Text Extraction**: Uses OCR to extract and preserve text from diagrams
- ✏️ **Fully Editable Output**: Generated Visio files have movable shapes and reconnectable connectors
- 🎨 **Modern UI**: Beautiful, responsive interface built with React and Tailwind CSS
- 🚀 **Fast Processing**: Efficient backend powered by Python FastAPI and OpenCV

## Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **OpenCV**: Computer vision library for image processing
- **NumPy**: Numerical computing for image analysis
- **Pillow**: Image manipulation
- **pytesseract**: OCR for text extraction
- **lxml**: XML processing for Visio file generation

### Frontend
- **React**: Modern JavaScript library for UI
- **Tailwind CSS**: Utility-first CSS framework
- **Responsive Design**: Works on desktop and mobile devices

## Installation

### Prerequisites
- Python 3.8 or higher
- Node.js 14 or higher
- Tesseract OCR (for text extraction)

### Backend Setup

1. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Install Tesseract OCR (required for text extraction):

**Amazon Linux / CentOS / RHEL:**
```bash
sudo dnf install tesseract -y
```

**Ubuntu / Debian:**
```bash
sudo apt-get install tesseract-ocr -y
```

**macOS:**
```bash
brew install tesseract
```

### Frontend Setup

1. Install Node.js dependencies:
```bash
cd frontend
npm install
```

## Running the Application

### Start Backend Server

```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`

### Start Frontend Development Server

```bash
cd frontend
npm start
```

The web interface will open at `http://localhost:3000`

## Usage

1. **Upload Image**: Drag and drop or browse to select an image containing a diagram or flowchart
2. **Convert**: Click the "Convert to Visio" button to process the image
3. **Download**: Download the generated .vsdx file
4. **Edit**: Open the file in Microsoft Visio and edit shapes, connectors, and text

## Supported Image Formats

- PNG
- JPG/JPEG
- BMP

## API Endpoints

### `POST /api/upload`
Upload an image file for processing.

**Request**: Multipart form data with image file

**Response**:
```json
{
  "file_id": "abc123",
  "filename": "diagram.png",
  "message": "File uploaded successfully"
}
```

### `POST /api/convert/{file_id}`
Convert uploaded image to Visio format.

**Response**:
```json
{
  "file_id": "abc123",
  "visio_file": "abc123.vsdx",
  "shapes_detected": 5,
  "connectors_detected": 4,
  "text_elements": 3,
  "message": "Conversion successful"
}
```

### `GET /api/download/{file_id}`
Download the generated Visio file.

**Response**: Binary .vsdx file

### `GET /api/analyze/{file_id}`
Analyze image without generating Visio file (for debugging).

**Response**: JSON with detected shapes, connectors, and text

### `DELETE /api/cleanup/{file_id}`
Clean up temporary files.

## How It Works

1. **Image Preprocessing**: The image is converted to grayscale and processed to enhance edges and shapes
2. **Shape Detection**: Uses contour detection to identify closed shapes
3. **Shape Classification**: Analyzes vertices and aspect ratios to classify shapes (rectangle, circle, etc.)
4. **Connector Detection**: Uses Hough Line Transform to detect straight lines connecting shapes
5. **Text Extraction**: OCR extracts text and its position
6. **Visio Generation**: Creates a .vsdx file (which is a ZIP containing XML files) with proper structure
7. **XML Construction**: Generates shape and connector XML with coordinates, geometry, and properties

## Project Structure

```
/vercel/sandbox/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── image_processor.py      # Image processing and shape detection
│   ├── visio_generator.py      # Visio file generation
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.js             # Main application component
│   │   ├── components/
│   │   │   ├── ImageUploader.js      # File upload component
│   │   │   ├── ProcessingStatus.js   # Processing indicator
│   │   │   └── ResultPanel.js        # Results display
│   │   ├── index.css          # Tailwind CSS imports
│   │   └── index.js           # React entry point
│   ├── package.json           # Node.js dependencies
│   └── tailwind.config.js     # Tailwind configuration
└── README.md                  # This file
```

## Limitations

- Works best with clear, high-contrast diagrams
- Complex curved connectors may be simplified to straight lines
- Text recognition accuracy depends on image quality
- Very small shapes (< 500 pixels area) are filtered as noise

## Future Enhancements

- Support for curved connectors
- Better text positioning within shapes
- Shape style preservation (colors, line styles)
- Support for more complex diagram types
- Batch processing of multiple images
- Export to other formats (SVG, PDF)

## Troubleshooting

### "Tesseract not found" error
Install Tesseract OCR using the commands in the Installation section.

### CORS errors
Make sure both backend (port 8000) and frontend (port 3000) are running.

### Poor shape detection
Try preprocessing the image to increase contrast or use a higher resolution image.

## License

MIT License - Feel free to use and modify for your projects.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
