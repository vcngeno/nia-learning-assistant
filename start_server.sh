#!/bin/bash
# Load environment variables from .env
export $(grep -v '^#' .env | xargs)
# Start the server
uvicorn enhanced_api:app --reload --port 8000
