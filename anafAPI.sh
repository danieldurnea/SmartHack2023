#!/bin/bash

# Get the CIF value by running the Python script
cif='16414068'

# Format the current date
current_date=$(date "+%Y-%m-%d")

# API URL
api_url='https://webservicesp.anaf.ro/PlatitorTvaRest/api/v6/ws/tva'

echo "[{\"cui\": ${cif}, \"data\": \"${current_date}\"}]"

# Make the curl request
curl POST "$api_url" \
     -H "Content-Type: application/json" \
     -d "[{\"cui\": ${cif}, \"data\": \"${current_date}\"}]"
