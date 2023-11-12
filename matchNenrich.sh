#!/bin/bash

curl 'https://data.veridion.com/match/v4/companies' \
  -H "x-api-key: "\
  -H "Content-type: application/json" \
  -d '{
    "commercial_names": [""],
    "address_txt": "Romania"
  }'
