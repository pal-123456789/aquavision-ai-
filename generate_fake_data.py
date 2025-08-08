# generate_fake_data.py

import numpy as np
import rasterio
from rasterio.transform import from_origin

def generate_fake_data():
    """Generates a fake GeoTIFF satellite image for demonstration."""
    width, height = 512, 512
    # Define coordinate system and location (dummy values for Surat, India)
    transform = from_origin(72.83, 21.17, 0.001, 0.001)
    crs = 'EPSG:4326'  # WGS84 Coordinate System

    # Create 3 bands: Red, Green, Blue
    # We will simulate an algal bloom by making a few areas intensely green.
    red = np.random.rand(height, width).astype(np.float32) * 50
    green = np.random.rand(height, width).astype(np.float32) * 60
    blue = np.random.rand(height, width).astype(np.float32) * 80

    # Add a few "algae" patches to the green band
    green[100:150, 100:150] = np.random.rand(50, 50) * 180 + 50
    green[400:450, 350:400] = np.random.rand(50, 50) * 200 + 55
    green[250:280, 200:230] = np.random.rand(30, 30) * 150 + 40
    
    print("Generating fake satellite data file: fake_satellite_image.tif")
    
    with rasterio.open(
        'fake_satellite_image.tif',
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=3, # Number of bands
        dtype=np.float32,
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(red, 1)   # Write red band to band 1
        dst.write(green, 2) # Write green band to band 2
        dst.write(blue, 3)  # Write blue band to band 3

    print("Fake data generated successfully!")

if __name__ == '__main__':
    generate_fake_data()