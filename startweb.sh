#!/bin/bash
# #ls -R *.py|  entr -r /root/byoctf_discord/.venv/bin/python ./challenge_validator_webapp.py &
# #ls -R *.py|  entr -r /root/byoctf_discord/.venv/bin/python ./scoreboard.py &

# killall gunicorn
# # ls -R *.py|  entr -r 
# /root/byoctf_discord/.venv/bin/python -m gunicorn --bind 127.0.0.1:5000 challenge_validator_webapp:app &
# # ls -R *.py|  entr -r 
# /root/byoctf_discord/.venv/bin/python -m gunicorn --bind 127.0.0.1:4000 scoreboard:app &
python -m gunicorn --bind 127.0.0.1:4000 scoreboard:app

# #!/bin/bash

# # Define the directory where the app and logs will reside
# APP_DIR="/root/byoctf_discord"
# LOG_DIR="$APP_DIR/logs"

# # Ensure the application and log directories exist
# [ -d "$APP_DIR" ] || mkdir -p "$APP_DIR"
# [ -d "$LOG_DIR" ] || mkdir -p "$LOG_DIR"

# # Check if supervisord is installed and install it if it's not
# if ! command -v supervisord &> /dev/null; then
#     echo "supervisord could not be found, installing now..."
#     apt-get update && apt-get install -y supervisor
# else
#     echo "supervisord is already installed."
# fi


# # Supervisord configuration content (replace with your actual configuration)
# SUPERVISORD_CONF="[unix_http_server]
# file=/tmp/supervisor.sock   ; (the path to the socket file)
# chmod=0765

# [supervisord]
# logfile=$LOG_DIR/supervisord.log ; (main log file path)
# logfile_maxbytes=50MB        ; (max log file size)
# logfile_backups=10           ; (number of log backups)
# loglevel=info                ; (logging level)
# pidfile=/tmp/supervisord.pid ; (pidfile path)
# nodaemon=false               ; (start in foreground?)

# [rpcinterface:supervisor]
# supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

# [supervisorctl]
# serverurl=unix:///tmp/supervisor.sock ; use a unix:// URL for a unix socket


# [program:scoreboard]
# command=/root/byoctf_discord/.venv/bin/python -m gunicorn --bind 127.0.0.1:4000 scoreboard:app
# directory=$APP_DIR
# autostart=true
# autorestart=true
# stderr_logfile=$LOG_DIR/scoreboard.err.log
# stdout_logfile=$LOG_DIR/scoreboard.out.log

# [group:appgroup]
# programs=scoreboard"

# # Check if the configuration file already exists and matches the desired state
# CONF_FILE="/etc/supervisor/conf.d/byoctf_discord.conf"
# rm "$CONF_FILE"
# if [ -f "$CONF_FILE" ]; then
#     # Check if the existing file content matches the desired configuration
#     if ! echo "$SUPERVISORD_CONF" | diff - "$CONF_FILE" > /dev/null; then
#         # If it doesn't match, update the configuration
#         echo "$SUPERVISORD_CONF" > "$CONF_FILE"
#         echo "Updated the existing supervisord configuration."
#     else
#         echo "The supervisord configuration is already up-to-date."
#     fi
# else
#     # If the configuration file doesn't exist, create it
#     echo "$SUPERVISORD_CONF" > "$CONF_FILE"
#     echo "Created a new supervisord configuration."
# fi

# # Reload supervisord configuration and update the programs
# # This is generally safe to run multiple times and is necessary if the configuration has changed
# supervisorctl reread
# supervisorctl update

# supervisorctl stop all

# # Start all programs (only start those that are not already running)
# supervisorctl start all
# supervisorctl status