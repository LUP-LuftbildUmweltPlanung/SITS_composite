# FORCE Processing Workflow

This project automates Level 1 and Level 2 FORCE processing using Docker. It supports custom user setups through a configuration file.

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/your-repository.git
   cd your-repository


### Generating HMAC Keys
1. Go to [Google Cloud Console](https://console.cloud.google.com/storage/settings).
2. Under "Interoperability," generate a new HMAC key.
3. Save the access key and secret key securely.
4. Export the keys as environment variables:
   ```bash
   export HMAC_ACCESS_KEY="your-access-key"
   export HMAC_SECRET_KEY="your-secret-key"
