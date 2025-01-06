#!/bin/bash

# Load environment variables
source $(dirname $0)/../config/paths.env

# Create necessary directories
mkdir -p "${METADATA_DIR}"
mkdir -p "${L1_DIR}"

# Run FORCE Level 1 processing - define your own requirements
sudo docker run -v "${BASE_MOUNT}:${BASE_MOUNT}" -v "${BOTO_FILE}:/home/docker/.boto" davidfrantz/force \
  force-level1-csd -n -d 20190101,20190330 -s S2A,S2B -c 0,50 -k "${METADATA_DIR}" \
  "${L1_DIR}" "${FORCE_L2A}/l1_pool.txt" "${SHAPEFILE_PATH}"
