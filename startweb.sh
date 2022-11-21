#!/bin/bash
ls -R *.py|  entr -r python ./challenge_validator_webapp.py &
ls -R *.py|  entr -r python ./scoreboard.py &

