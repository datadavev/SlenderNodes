#!/usr/bin/env bash

./workers-stop.sh

for i in {1..10}
do
   ./manage.py runworker --settings settings_deploy scan &
done
