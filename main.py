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


@app.get("/")
def root():
    return {
        "message": "Lake Encroachment Monitoring API",
        "status": "online"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/monitoring")
def monitoring():
    return {
        "status": "Monitoring API is working"
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


@app.get("/monitor-change")
def monitor_change(
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
        datetime="2024-01-01/2026-09-09",
        query={"eo:cloud_cover": {"lt": 30}},
        max_items=2
    )

    items = list(search.items())

    if len(items) < 2:
        return {
            "lake_name": lake_name,
            "latitude": latitude,
            "longitude": longitude,
            "status": "Not enough satellite images for comparison"
        }

    items = sorted(items, key=lambda x: x.datetime)

    before_item = items[0]
    after_item = items[-1]

    def calculate_water(item):
        signed = planetary_computer.sign(item)

        green_url = signed.assets["B03"].href
        nir_url = signed.assets["B08"].href

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
        mask = ndwi > 0

        return int(mask.sum()), int(mask.size)

    before_pixels, total_pixels = calculate_water(before_item)
    after_pixels, _ = calculate_water(after_item)

    before_percent = (before_pixels / total_pixels) * 100
    after_percent = (after_pixels / total_pixels) * 100

    change_pixels = after_pixels - before_pixels
    change_percent = after_percent - before_percent

    if change_percent > 1:
        change_status = "Water increased"
    elif change_percent < -1:
        change_status = "Water decreased"
    else:
        change_status = "No significant change"

    return {
        "lake_name": lake_name,
        "latitude": latitude,
        "longitude": longitude,
        "satellite": "Sentinel-2",
        "before_date": str(before_item.datetime.date()),
        "after_date": str(after_item.datetime.date()),
        "before_water_pixels": before_pixels,
        "after_water_pixels": after_pixels,
        "total_pixels": total_pixels,
        "before_water_percentage": round(before_percent, 2),
        "after_water_percentage": round(after_percent, 2),
        "change_pixels": change_pixels,
        "change_percentage": round(change_percent, 2),
        "change_status": change_status,
        "method": "NDWI change detection",
        "status": "Real satellite before/after prototype"
    }


@app.get("/water-mask")
def water_mask():
    file_path = "/content/drive/MyDrive/Lake_Encroachment_Project/outputs/maps/hussain_sagar_water_mask.png"

    if os.path.exists(file_path):
        return FileResponse(file_path)

    return {
        "status": "Water mask file not found"
    }


@app.get("/satellite-image")
def satellite_image():
    file_path = "/content/drive/MyDrive/Lake_Encroachment_Project/outputs/maps/hussain_sagar_satellite_visual.png"

    if os.path.exists(file_path):
        return FileResponse(file_path)

    return {
        "status": "Satellite image not found"
    }
    
           

   

   
    
    
