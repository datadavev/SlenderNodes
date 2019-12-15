#!/usr/bin/env bash

./workers-stop.sh
./manage.py runworker --settings settings scan
