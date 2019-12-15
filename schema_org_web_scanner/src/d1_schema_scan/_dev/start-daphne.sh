#!/usr/bin/env bash

/home/scan/.pyenv/versions/3.7.5/bin/daphne \
-v2 -b 127.0.0.1 -p 8443 \
d1_schema_scan.asgi:application
