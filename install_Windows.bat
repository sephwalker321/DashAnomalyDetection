@ECHO OFF
Rem Script to install virtual environment and all dependencies.
Rem For Windows


Rem Set up virtual environment
if exist %~dp0\venv\ (
echo "venv/ exists on your filesystem."
CALL %~dp0\venv\Scripts\activate
) else (
echo "venv/ doens't exist"
pip install virtualenv
python -m venv venv
CALL %~dp0\venv\Scripts\activate
pip install -r requirements.txt --no-cache-dir
)

Rem End and generate test files
echo "Succesfull installation termination"
python DemoDat.py
