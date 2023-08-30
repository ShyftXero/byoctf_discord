#!/bin/bash
# ls -R *.py|  entr -r 
kill `pgrep -f byoctf_discord.py`
python ./byoctf_discord.py
