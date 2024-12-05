#!/bin/sh
# Start the Flask server in the background
flask run --host=0.0.0.0 --port=5000 --debug --cert=/run/secrets/gatcha_cert --key=/run/secrets/gatcha_key &

# Capture the PID of the Flask server
FLASK_PID=$!


sleep 3


python bootstrap.py

# Wait for the Flask server to finish
wait $FLASK_PID