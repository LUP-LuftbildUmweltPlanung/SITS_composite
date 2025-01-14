###### execute force dynamically ##########
### requirements: .boto file (gsutil)
############################################
import subprocess
import time
import glob

from github_projects.SITS_composite2.utils.utils import parameter_file
from utils.utils import create_folder_structure, download_catalogues, queue_file, level1_csd, parameter_file, execute_prm_file, download_defined_catalogue
from utils.vrt_dem_download import download_dem

#General parameters
base_path = '/rvt_mount/composite_test_project'                 # Base Path where ./process/ folder structure should be created
local_dir = "/rvt_mount:/rvt_mount"                                     # Mount Point for local Drive
boto_dir = "/home/eouser/.boto:/home/docker/.boto"                      # Mount .goto file for gsutil
aois = "/rvt_mount/Force_L2A/DEM/bergamo/bergamo_4326.shp" #Area of interest

#L1C data parameters
#no_act = "-n"                          #If you are sure to download delete the -n inside the braquets
no_act = ""
date_range = "20200101,20200107"       #format YYYYMMDD,YYYYMMDD
cloud_cover = "0,50"
sensors = "S2A,S2B"                 #LT04,LT05,LE07,LC08


create_folder_structure(base_path)
download_catalogues(base_path, local_dir)
queue_file(base_path)
level1_csd(local_dir, base_path, boto_dir,aois, no_act, date_range, sensors, cloud_cover)


#L2A data parameters
download_dem(base_path,aois)
parameter_file(base_path, aois)

#Execute parameter file - the parameter file can be opened before to check the that the paths and infor is correct
# but it is not necessary.
execute_prm_file(base_path, boto_dir, local_dir)


