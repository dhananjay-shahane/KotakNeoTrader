#!/bin/bash

# Set up environment variables
export SESSION_SECRET="275726958984846c2f4c8c2cef08959663c7202cc4ca7e045431dac2d01c69ec"

# Set up library paths for pandas dependencies
export LD_LIBRARY_PATH="/nix/store/$(ls /nix/store | grep zlib | head -1)/lib:/nix/store/$(ls /nix/store | grep gcc-unwrapped | head -1)/lib:$LD_LIBRARY_PATH"

echo "Starting Kotak Neo Trading Application..."
echo "Library path: $LD_LIBRARY_PATH"

# Start the application
exec gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app