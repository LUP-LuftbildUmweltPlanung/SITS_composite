#!/bin/bash

# Load environment variables
source $(dirname $0)/../config/paths.env

# Create the l1_pool.txt file if it doesn't already exist
if [ ! -f "${FORCE_L2A}/l1_pool.txt" ]; then
  echo "Creating l1_pool.txt..."
  mkdir -p "${FORCE_L2A}" # Ensure the directory exists
  touch "${FORCE_L2A}/l1_pool.txt"
  echo "l1_pool.txt created at ${FORCE_L2A}/l1_pool.txt"
fi

# Grant permissions to the base mount directory
sudo chmod -R 777 "${BASE_MOUNT}"
chmod 777 "${FORCE_L2A}/l1_pool.txt"

# Check if HMAC keys are set
if [ -z "$HMAC_ACCESS_KEY" ] || [ -z "$HMAC_SECRET_KEY" ]; then
  echo "Error: HMAC keys are not set. Please set HMAC_ACCESS_KEY and HMAC_SECRET_KEY as environment variables."
  exit 1
fi

# Authenticate with gcloud using HMAC keys
gcloud auth activate-service-account --key-file <(echo -e "{
  \"type\": \"service_account\",
  \"access_key\": \"$HMAC_ACCESS_KEY\",
  \"secret_key\": \"$HMAC_SECRET_KEY\"
}")

# Authenticate Google Cloud and configure HMAC key
echo "Running 'gcloud auth login'..."
gcloud auth login
gsutil config

# Adjust boto permissions
chmod 644 "${BOTO_FILE}"
