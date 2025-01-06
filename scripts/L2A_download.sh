#!/bin/bash

# Load environment variables
source $(dirname $0)/../config/paths.env

# Set permissions for parameter file
sudo chmod 777 "${FORCE_L2A}/param/l2ps_brg.prm"

# Run Python script to generate VRT file
python "${FORCE_L2A}/DEM/vrt_dem_download.py"

# Run FORCE Level 2 processing
sudo docker run -t -v "${BASE_MOUNT}:${BASE_MOUNT}" davidfrantz/force \
  force-level2 "${FORCE_L2A}/param/l2ps_brg.prm"
