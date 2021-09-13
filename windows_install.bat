ECHO OFF
ECHO Checking Python version
python3.8 --version

ECHO If this command returns an error, please download Python3.8 from the Microsoft Software Store.
PAUSE

ECHO Installing Python virtualenv

python3.8 -m pip -qqq install --upgrade pip virtualenv

PAUSE

ECHO Creating virtual environment

python3.8 -m virtualenv venv/

PAUSE

ECHO Installing bantool in venv

.\venv\Scripts\python.exe -m pip install -qqq .

.\venv\Scripts\python.exe -m bantool --init

PAUSE

ECHO Installation success! The "windows_run_bantool" program can now be launched.

PAUSE

EXIT
