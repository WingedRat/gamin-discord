#!/usr/bin/env bash
source /home/wingedrat/.venv/gamin-discord/bin/activate
cd ~/PycharmProjects/gamin-discord
rm -rf etc/requirements.txt.old
mv etc/requirements.txt etc/requirements.txt.old
pip3 freeze > etc/requirements.txt
diff etc/requirements.txt.old etc/requirements.txt