import geopandas as gpd
import subprocess
import math
import os

#DEM_NODATA = -32768
def reproject_to_wgs84(shapefile_path):
    """
    Reproject the shapefile to WGS84.
    """
    gdf = gpd.read_file(shapefile_path)
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
    tif_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.tif')]

    # Step 1: Create the .txt file with the paths of the DEM files
    with open(txt_file_path, "w") as txt_file:
        for tif in tif_files:
            txt_file.write(f"{tif}\n")

    # Step 2: Create the .vrt file using gdalbuildvrt
    gdal_command = f"gdalbuildvrt -input_file_list {txt_file_path} {vrt_file_path}"
    subprocess.run(gdal_command, shell=True)


def main():
    shapefile_path = input("Enter the path to your shapefile: ")
    output_dir = input("Enter the output directory for downloaded DEMs: ")

    # Step 1: Reproject the shapefile to WGS84
    print("Reprojecting shapefile to WGS84...")
    gdf_wgs84 = reproject_to_wgs84(shapefile_path)

    # Step 2: Extract extent and format as tiles
    print("Extracting extent and formatting to tile names...")
    tiles = extract_extent_to_tiles(gdf_wgs84)
    print(f"Identified tiles: {tiles}")

    # Step 3: Generate AWS S3 command
    print("Generating AWS S3 command...")
    aws_command = generate_aws_command(tiles, output_dir)
    print(f"Generated AWS command:\n{aws_command}")

    # Optional: Execute the AWS command
    execute = input("Do you want to execute the AWS command now? (y/n): ")
    if execute.lower() == 'y':
        subprocess.run(aws_command, shell=True)

    # Step 4: Create the .txt and .vrt files
    txt_file_path = os.path.join(output_dir, "nasa.txt")
    vrt_file_path = os.path.join(output_dir, "nasa.vrt")
    print(f"Creating {txt_file_path} and {vrt_file_path}...")
    create_txt_and_vrt(output_dir, txt_file_path, vrt_file_path)

    # Step 5: Output the VRT file path for the .prm file
    print(f"VRT file created at: {vrt_file_path}")


if __name__ == "__main__":
    main()
