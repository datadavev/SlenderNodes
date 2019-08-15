#!/usr/bin/env bash

# systemd service.

venv_bin_path=/var/local/dataone/gmn_venv_py3/bin
py_bin_path=${venv_bin_path}/python
daphne_bin_path=${venv_bin_path}/daphne

# Set current directory to where this bash script is.
# Should be the project root directory (where settings.py also is).
cd "$(dirname "$0")"

# Redirect all output from this script and children to log.
exec >> "$(basename "$0").log"
exec 2>&1

pkill -ef runworker
pkill -ef daphne

for i in {1..10}
do
   ${py_bin_path} ./manage.py runworker --settings settings_deploy scan &
done

${daphne_bin_path} -v2 -b 127.0.0.1 -p 8443 d1_schema_scan.asgi:application

# WSS
#/var/local/dataone/gmn_venv_py3/bin/daphne -e ssl:8443:\
#privateKey=/etc/letsencrypt/live/gmn.test.dataone.org/privkey.pem:\
#certKey=/etc/letsencrypt/live/gmn.test.dataone.org/fullchain.pem \
#d1_schema_scan.asgi:application -p 8444 -b 127.0.0.1 -v2
