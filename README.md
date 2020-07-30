# biigle_scripts
Utility scripts that use the BIIGLE API.

## Installation
This package requires Python >= 3.7.
It's recommended to work under a virtual environment, which could be set as follows:
```
virtualenv venv-biigle_scripts --python=python3.7
source venv-biigle_scripts/bin/activate
```

Installation procedure is the following:
```
git clone https://github.com/charleygros/biigle_scripts.git
cd biigle_scripts
pip install -e .
```

## How to run a script
Type the script's name of interest in your terminal followed by `-h` to get its usage. For instance:
```
convert_laser_circle_to_point -h
```
... gives:
```
usage: convert_laser_circle_to_point -e EMAIL -t TOKEN -s SURVEY_NAME [-h]

MANDATORY ARGUMENTS:
  -e EMAIL, --email EMAIL
                        Email address used for BIIGLE account.
  -t TOKEN, --token TOKEN
                        BIIGLE API token. To generate one:
                        https://biigle.de/settings/tokens
  -s SURVEY_NAME, --survey_name SURVEY_NAME
                        Survey name, eg NBP1402.

OPTIONAL ARGUMENTS:
  -h, --help            Shows function documentation.
```
