from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

app = FastAPI(
    title="Lake Encroachment Monitoring API",
    description="Satellite-based lake monitoring prototype",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/monitor")
def monitor_lake(
    lake_name: str,
    latitude: float,
    longitude: float
):
    return {
        "lake_name": lake_name,
        "latitude": latitude,
        "longitude": longitude,
        "satellite": "Sentinel-2",
        "method": "NDWI",
        "status": "Monitoring request received",
        "note": "Prototype - satellite processing will be connected next"
    }


@app.get("/monitor-real")
def monitor_real(
    lake_name: str,
    latitude: float,
    longitude: float
):
    import pystac_client
    import planetary_computer
    import rasterio
    from rasterio.windows import Window
    import numpy as np

    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1"
    )

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=[
            longitude - 0.02,
            latitude - 0.02,
            longitude + 0.02,
            latitude + 0.02
        ],
        datetime="2026-01-01/2026-09-09",
        query={"eo:cloud_cover": {"lt": 30}},
        max_items=1
    )

    items = list(search.items())

    if not items:
        return {
            "lake_name": lake_name,
            "latitude": latitude,
            "longitude": longitude,
            "status": "No suitable Sentinel-2 image found"
        }

    item = items[0]
    signed_item = planetary_computer.sign(item)

    green_url = signed_item.assets["B03"].href
    nir_url = signed_item.assets["B08"].href

    with rasterio.open(green_url) as src:
        cx = src.width // 2
        cy = src.height // 2
        window = Window(cx - 128, cy - 128, 256, 256)
        green = src.read(1, window=window).astype(np.float32)

    with rasterio.open(nir_url) as src:
        cx = src.width // 2
        cy = src.height // 2
        window = Window(cx - 128, cy - 128, 256, 256)
        nir = src.read(1, window=window).astype(np.float32)

    green = green / 10000.0
    nir = nir / 10000.0

    ndwi = (green - nir) / (green + nir + 1e-8)
    water_mask = ndwi > 0

    water_pixels = int(water_mask.sum())
    total_pixels = int(water_mask.size)

    return {
        "lake_name": lake_name,
        "latitude": latitude,
        "longitude": longitude,
        "satellite": "Sentinel-2",
        "image_date": str(item.datetime.date()),
        "method": "NDWI",
        "water_pixels": water_pixels,
        "total_pixels": total_pixels,
        "detected_water_percentage": round(
            (water_pixels / total_pixels) * 100, 2
        ),
        "status": "Real satellite prototype result"
    }


@app.get("/water-mask")
def water_mask():
    image_path = os.path.join(BASE_DIR, "water_mask.png")

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
    image_path = os.path.join(BASE_DIR, "satellite_visual.png")

    if not os.path.exists(image_path):
        return {
            "error": "Satellite image not found"
        }

    return FileResponse(
        image_path,
        media_type="image/png"
    )
        

   
    
    
