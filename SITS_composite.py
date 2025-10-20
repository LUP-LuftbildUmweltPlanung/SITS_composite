###### execute force dynamically ##########
### requirements: .boto file (gsutil)
############################################
import subprocess
import time
import glob

from utils.utils import (
    create_folder_structure,
    download_catalogues,
    queue_file,
    level1_csd,
    parameter_file,
    execute_prm_file,
    cleanup_level1_data,
    flatten_level2_output,
)
from utils.vrt_dem_download import download_dem

#General parameters
base_path = '/rvt_mount/force/FORCE/C1/L2'  # Directory path where ./process/ folder structure should be created /force/FORCE/C1_/L2/ard/
local_dir = "/rvt_mount:/rvt_mount"                             # Mount Point for local Drive
boto_dir = "/home/eouser/.boto:/home/docker/.boto"              # Mount .boto file for gsutil - check the Readme file for more info
aois = "/rvt_mount/3DTests/data/harm_data/ilmenau.shp"      # Area of interest - shapefile

#L1C vitalitat_3cities_data parameters
no_act = ""                            # Continue the download process without checking the size of it
#no_act = "-n"                          # Dry run parameter that only returns number of images and total vitalitat_3cities_data volume
date_range = "20160101,20180630"       # Format YYYYMMDD,YYYYMMDD
cloud_cover = "0,30"                   # Cloud cover, format minimum,maximum percentage
sensors = "S2A,S2B"                    # Sensors that will be used. Landsat options (LT04,LT05,LE07,LC08)

create_folder_structure(base_path)                              # Creates the folder structure for the project
download_catalogues(base_path, local_dir)                       # Download the FORCE catalogues
queue_file(base_path)                                           # Creates the queue file
level1_csd(local_dir, base_path, boto_dir,aois, no_act, date_range, sensors, cloud_cover) # Download the L1C vitalitat_3cities_data


#L2A vitalitat_3cities_data parameters
download_dem(base_path,aois)                                    # Download the NASA DEM necessary for corrections
parameter_file(base_path, aois)                                 # Creates your own parameter file with some info filled

#Execute parameter file - the parameter file can be opened before to check the that the paths and infor is correct
# but it is not necessary.
execution_success = execute_prm_file(base_path, boto_dir, local_dir)  # Executes the parameter file and download L2A vitalitat_3cities_data

if execution_success:
    flatten_level2_output(base_path)
    cleanup_level1_data(base_path)
else:
    print("Skipping L1C cleanup because Level2 execution failed.")
