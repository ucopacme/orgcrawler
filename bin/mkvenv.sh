#!/bin/bash
#probably better to use ansible for this for cross OS support
mkdir ~/python/venv
virtualenv ~/python/venv/ucopacme-organizer
source ~/python/venv/ucopacme-organizer/bin/activate
pip install -r requirements.txt
pip install -e .
