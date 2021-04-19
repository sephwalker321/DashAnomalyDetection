#!/bin/bash
# Script to install virtual environment and all dependancies. Currently only working on Linux.

# Activate virtual environment
ActEnv() { 
	source venv/bin/activate
}
DeActEnv() { 
	deactivate 
}

#Set up virtual environment
if [ -d "venv/" ]
then
	echo "venv/ exists on your filesystem."
	ActEnv
else
	echo "venv/ doens't exist"
	python3 -m venv venv
	ActEnv
	pip install -r requirements.txt	--no-cache-dir
fi

echo "Succesfull installation termination"
echo " "
python DemoDat.py
exit
