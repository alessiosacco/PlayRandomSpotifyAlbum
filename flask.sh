#!/usr/bin/env bash
export FLASK_APP=main.py
export FLASK_ENV=debug
export CLIENT_ID="PLACEHOLDER"
export CLIENT_SECRET="PLACEHOLDER"

python3 -m flask run