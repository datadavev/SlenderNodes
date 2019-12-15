#!/usr/bin/env bash

# This is the systemd entry point for the main service.
# Referenced at: /etc/systemd/system/dataone_schema_org_scanner.service

set -x
set -e

venv_bin_path=/home/scan/.pyenv/versions/3.7.5/bin
py_bin_path=${venv_bin_path}/python
daphne_bin_path=${venv_bin_path}/daphne

# Set current directory to the location of this script, which should be the project root.
cd "$(dirname "$0")"

${daphne_bin_path} -v2 -b 127.0.0.1 -p 8443 d1_schema_scan.asgi:application


# WSS                                                                                                                                                                                                                                                          
#/var/local/dataone/gmn_venv_py3/bin/daphne -e ssl:8443:\
#privateKey=/etc/letsencrypt/live/gmn.test.dataone.org/privkey.pem:\
#certKey=/etc/letsencrypt/live/gmn.test.dataone.org/fullchain.pem \
#d1_schema_scan.asgi:application -p 8444 -b 127.0.0.1 -v2
