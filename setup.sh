#!/bin/bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "requirements.txt not found. Creating a default one."
    echo -e "flask\nflask_bcrypt" > requirements.txt
    pip install -r requirements.txt
fi
echo "Done."
