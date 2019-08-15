#!/usr/bin/env bash

find . -path './api_types/generated' -prune -o -name '*.py' -print -exec isort -y {} \; -exec yapf -i {} \;

#isort -y
#yapf -ir .

