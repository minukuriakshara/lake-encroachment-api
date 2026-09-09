
from fastapi import FastAPI
from fastapi.responses import FileResponse
import os

app = FastAPI(
    title="Lake Encroachment Monitoring API",
    description="Satellite-based lake monitoring prototype",
    version="1.0"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/")
def home():
    return {
        "message": "Lake Monitoring API is running",
        "status": "success"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

@app.get("/monitoring")
def monitoring():
    return {
        "location": "Hussain Sagar Lake, Hyderabad",
        "latitude": 17.4239,
        "longitude": 78.4738,
        "satellite": "Sentinel-2",
        "image_date": "2026-09-06",
        "detected_water_percentage": 62.5,
        "water_pixels": 40959,
        "total_pixels": 65536,
        "method": "NDWI",
        "status": "Prototype monitoring result"
    }

@app.get("/water-mask")
def water_mask():
    image_path = os.path.join(
        BASE_DIR,
        "water_mask.png"
    )

    if not os.path.exists(image_path):
        return {
            "error": "Water mask image not found"
        }

    return FileResponse(
        image_path,
        media_type="image/png"
    )

@app.get("/satellite-image")
def satellite_image():
    image_path = os.path.join(
        BASE_DIR,
        "satellite_visual.png"
    )

    if not os.path.exists(image_path):
        return {
            "error": "Satellite image not found"
        }

    return FileResponse(
        image_path,
        media_type="image/png"
    )
