#!/bin/bash

url='https://data.veridion.com/search/v1/companies'
api_key=''

data='{
  "filters": [
    {
      "attribute": "company_keywords",
      "relation": "match_expression",
      "value": {
        "match": {
          "operator": "or",
          "operands": [
            "veteran owned",
            "woman owned",
            "minority owned",
            "service disabled"
          ]
        }
      },
      "strictness": 3
    }
  ]
}'

curl -X POST "$url" \
     -H "x-api-key:$api_key" \
     -H "Content-Type: application/json" \
     -d "$data"
