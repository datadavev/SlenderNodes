#!/usr/bin/env bash

/home/gmn/.pyenv/versions/django_channels_test/bin/daphne \
-v2 -b 127.0.0.1 -p 8443 \
d1_schema_scan.asgi:application
