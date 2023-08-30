#!/bin/bash
#ls -R *.py|  entr -r python ./challenge_validator_webapp.py &
#ls -R *.py|  entr -r python ./scoreboard.py &

killall gunicorn
# ls -R *.py|  entr -r 
gunicorn --bind 127.0.0.1:5000 challenge_validator_webapp:app &
# ls -R *.py|  entr -r 
gunicorn --bind 127.0.0.1:4000 scoreboard:app &

