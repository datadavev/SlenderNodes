#!/usr/bin/env bash

while true
do
  manage.py runworker add-log
  sleep 1
done
