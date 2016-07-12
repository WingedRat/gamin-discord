#!/usr/bin/env bash
source $HOME/.venv/gamin-discord/bin/activate
cd ~/PycharmProjects/gamin-discord
rm -rf etc/requirements.txt.old
mv requirements.txt etc/requirements.txt.old
pip3 freeze > requirements.txt
diff etc/requirements.txt.old requirements.txt
