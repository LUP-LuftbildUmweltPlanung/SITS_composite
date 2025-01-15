###### execute force dynamically ##########
### requirements: .boto file (gsutil)
############################################
import subprocess
import time
import glob

from utils.utils import create_folder_structure, download_catalogues, queue_file, level1_csd, parameter_file, execute_prm_file
from utils.vrt_dem_download import download_dem

#General parameters
base_path = '/rvt_mount/composite_test_project'                 # Directory path where ./process/ folder structure should be created
local_dir = "/rvt_mount:/rvt_mount"                             # Mount Point for local Drive
boto_dir = "/home/eouser/.boto:/home/docker/.boto"              # Mount .boto file for gsutil - check the Readme file for more info
aois = "/rvt_mount/Force_L2A/DEM/bergamo/bergamo_4326.shp"      # Area of interest - shapefile

#L1C data parameters
no_act = ""                            # Continue the download process without checking the size of it
no_act = "-n"                          # Dry run parameter that only returns number of images and total data volume
date_range = "20200101,20200107"       # Format YYYYMMDD,YYYYMMDD
cloud_cover = "0,50"                   # Cloud cover, format minimum,maximum percentage
sensors = "S2A,S2B"                    # Sensors that will be used. Landsat options (LT04,LT05,LE07,LC08)


create_folder_structure(base_path)                              # Creates the folder structure for the project
download_catalogues(base_path, local_dir)                       # Download the FORCE catalogues
queue_file(base_path)                                           # Creates the queue file
level1_csd(local_dir, base_path, boto_dir,aois, no_act, date_range, sensors, cloud_cover) # Download the L1C data


#L2A data parameters
download_dem(base_path,aois)                                    # Download the NASA DEM necessary for corrections
parameter_file(base_path, aois)                                 # Creates your own parameter file with some info filled

#Execute parameter file - the parameter file can be opened before to check the that the paths and infor is correct
# but it is not necessary.
execute_prm_file(base_path, boto_dir, local_dir)                #Executes the parameter file and download L2A data


