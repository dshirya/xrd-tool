#!/bin/bash
# Change to the directory where main.py is located.
cd dirname 

# Start the Dash server in the background.
python3 main.py 

# Wait a few seconds to ensure the server has started.
sleep 3

# Open the default browser at the Dash app URL.
open http://127.0.0.1:8050

# Wait for the background process to finish.
wait