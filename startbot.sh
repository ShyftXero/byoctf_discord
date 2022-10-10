#!/bin/bash
ls -R *.py|  entr -r python ./byoctf_discord.py
