import geopandas as gpd
import subprocess
import math
import os
from typing import List


# DEM_NODATA = -32768
def reproject_to_wgs84(aois):
    """
    Reproject the shapefile to WGS84.
    """
    gdf = gpd.read_file(aois)
    gdf_wgs84 = gdf.to_crs("EPSG:4326")
    return gdf_wgs84


def extract_extent_to_tiles(gdf):
    """
    Extract the extent and convert it into formatted strings like 'n123e012'.
    """
    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    min_lon, min_lat, max_lon, max_lat = bounds

    # Generate the formatted extent for each degree tile
    tiles = []
    for lat in range(math.floor(min_lat), math.ceil(max_lat)):
        for lon in range(math.floor(min_lon), math.ceil(max_lon)):
            n = f"n{abs(lat):02d}" if lat >= 0 else f"s{abs(lat):02d}"
            e = f"e{abs(lon):03d}" if lon >= 0 else f"w{abs(lon):03d}"
            tiles.append(f"{n}{e}")
    return tiles

def generate_aws_command(tiles, output_dir):
    """
    Generate the AWS S3 command for downloading DEM files based on tile names.
    """
    include_patterns = " ".join([f"--include 'NASADEM_HGT_{tile}*'" for tile in tiles])
    aws_command = (
        f"aws s3 cp s3://raster/NASADEM/NASADEM_be/ {output_dir} "
        f"--recursive --exclude '*' {include_patterns} "
        f"--endpoint-url https://opentopography.s3.sdsc.edu --no-sign-request"
    )
    return aws_command


def create_txt_and_vrt(output_dir, txt_file_path, vrt_file_path):
    """
    Create a .txt file with the paths of the downloaded DEM files and a .vrt file.
    """
    # Get the paths of all .tif files in the output directory
    tif_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".tif")]

    # Step 1: Create the .txt file with the paths of the DEM files
    with open(txt_file_path, "w") as txt_file:
        for tif in tif_files:
            txt_file.write(f"{tif}\n")

    # Step 2: Create the .vrt file using gdalbuildvrt
    gdal_command = f"gdalbuildvrt -input_file_list {txt_file_path} {vrt_file_path}"
    subprocess.run(gdal_command, shell=True, check=True)


def download_dem(
    base_path: str,
    aois: str,
    auto_execute: bool = True,
    skip_if_present: bool = True,
    tiles_override: List[str] = None,
) -> None:
    """
    Download DEM files for the specified AOI and save them to the predefined DEM folder.

    Parameters:
        base_path (str): The base path where the folder structure has been created.
        aois (str): Path to the AOIs shapefile.
        auto_execute (bool): If True, executes the AWS download command automatically.
        skip_if_present (bool): Skip downloading when DEM tiles already exist locally.
        tiles_override (List[str]): Optional list of tile IDs to download instead of deriving from the AOI.
    """
    # Define the output directory for DEMs
    output_dem_dir = os.path.join(base_path, "process/temp/dem")

    # Ensure the AOI shapefile exists
    if not os.path.exists(aois):
        raise FileNotFoundError(f"The shapefile '{aois}' does not exist.")

    # Ensure the DEM output directory exists
    if not os.path.exists(output_dem_dir):
        os.makedirs(output_dem_dir)
        print(f"Created DEM directory: {output_dem_dir}")

    # Step 1: Reproject the shapefile to WGS84
    print("Reprojecting shapefile to WGS84...")
    gdf_wgs84 = reproject_to_wgs84(aois)

    # Step 2: Extract extent and format as tiles
    print("Extracting extent and formatting to tile names...")
    tiles = tiles_override if tiles_override is not None else extract_extent_to_tiles(gdf_wgs84)
    print(f"Identified tiles: {tiles}")

    existing_tiles = [f for f in os.listdir(output_dem_dir) if f.endswith(".tif")]
    if skip_if_present and existing_tiles:
        print(f"DEM tiles already present in {output_dem_dir}; skipping download.")
        tiles_downloaded = existing_tiles
    else:
        # Step 3: Generate AWS S3 command
        print("Generating AWS S3 command...")
        aws_command = generate_aws_command(tiles, output_dem_dir)
        print(f"Generated AWS command:\n{aws_command}")

        if auto_execute:
            print("Executing AWS command automatically. Use --dem-prompt to enable confirmation.")
            subprocess.run(aws_command, shell=True, check=True)
        else:
            execute = input("Do you want to execute the AWS command now? (y/n): ")
            if execute.lower().startswith("y"):
                subprocess.run(aws_command, shell=True, check=True)
            else:
                print("Skipping AWS download on user request. DEM files might be incomplete.")
        tiles_downloaded = [f for f in os.listdir(output_dem_dir) if f.endswith(".tif")]

    if not tiles_downloaded:
        raise RuntimeError(
            f"No DEM GeoTIFFs found in {output_dem_dir}. Ensure the download command completed successfully."
        )

    # Step 4: Create the .txt and .vrt files
    txt_file_path = os.path.join(output_dem_dir, "nasa.txt")
    vrt_file_path = os.path.join(output_dem_dir, "nasa.vrt")
    print(f"Creating {txt_file_path} and {vrt_file_path}...")
    create_txt_and_vrt(output_dem_dir, txt_file_path, vrt_file_path)

    # Step 5: Output the VRT file path for the .prm file
    print(f"VRT file created at: {vrt_file_path}")


if __name__ == "__main__":
    raise SystemExit("This module is intended to be used via SITS_composite.py.")
