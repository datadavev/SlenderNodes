#!/usr/bin/env bash

# This is the systemd entry point for the service workers.
# Referenced at: /etc/systemd/system/dataone_schema_org_scanner@.service

set -x
set -e

venv_bin_path=/home/scan/.pyenv/versions/3.7.5/bin
py_bin_path=${venv_bin_path}/python

# Set current directory to the location of this script, which should be the project root.
cd "$(dirname "$0")"

${py_bin_path} ./manage.py runworker --settings settings_deploy scan &

