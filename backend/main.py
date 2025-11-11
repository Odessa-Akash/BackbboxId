from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import shutil
from pathlib import Path
from image_processor import ShapeDetector
from visio_generator import VisioGenerator

app = FastAPI(title="Image to Visio Converter API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
UPLOAD_DIR = Path("/tmp/uploads")
OUTPUT_DIR = Path("/tmp/outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Image to Visio Converter API", "status": "running"}

@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image file"""
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate unique filename
    file_id = uuid.uuid4().hex
    file_extension = os.path.splitext(file.filename)[1]
    upload_path = UPLOAD_DIR / f"{file_id}{file_extension}"
    
    # Save uploaded file
    try:
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    return {
        "file_id": file_id,
        "filename": file.filename,
        "message": "File uploaded successfully"
    }

@app.post("/api/convert/{file_id}")
async def convert_to_visio(file_id: str):
    """Convert uploaded image to Visio file"""
    # Find the uploaded file
    uploaded_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
    if not uploaded_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    image_path = str(uploaded_files[0])
    
    try:
        # Process image
        detector = ShapeDetector(image_path)
        processed_data = detector.process()
        
        # Generate Visio file
        output_path = OUTPUT_DIR / f"{file_id}.vsdx"
        generator = VisioGenerator(str(output_path))
        visio_file = generator.create_visio_file(processed_data)
        
        return {
            "file_id": file_id,
            "visio_file": f"{file_id}.vsdx",
            "shapes_detected": len(processed_data['shapes']),
            "connectors_detected": len(processed_data['connectors']),
            "text_elements": len(processed_data['text_elements']),
            "message": "Conversion successful"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

@app.get("/api/download/{file_id}")
async def download_visio(file_id: str):
    """Download the generated Visio file"""
    visio_path = OUTPUT_DIR / f"{file_id}.vsdx"
    
    if not visio_path.exists():
        raise HTTPException(status_code=404, detail="Visio file not found")
    
    return FileResponse(
        path=str(visio_path),
        filename=f"diagram_{file_id}.vsdx",
        media_type="application/vnd.ms-visio.drawing"
    )

@app.get("/api/analyze/{file_id}")
async def analyze_image(file_id: str):
    """Analyze image and return detected elements without generating Visio file"""
    uploaded_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
    if not uploaded_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    image_path = str(uploaded_files[0])
    
    try:
        detector = ShapeDetector(image_path)
        processed_data = detector.process()
        
        return {
            "file_id": file_id,
            "analysis": processed_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.delete("/api/cleanup/{file_id}")
async def cleanup_files(file_id: str):
    """Clean up uploaded and generated files"""
    deleted = []
    
    # Delete uploaded file
    for file in UPLOAD_DIR.glob(f"{file_id}.*"):
        file.unlink()
        deleted.append(str(file))
    
    # Delete generated Visio file
    visio_file = OUTPUT_DIR / f"{file_id}.vsdx"
    if visio_file.exists():
        visio_file.unlink()
        deleted.append(str(visio_file))
    
    return {
        "message": "Cleanup successful",
        "deleted_files": deleted
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
