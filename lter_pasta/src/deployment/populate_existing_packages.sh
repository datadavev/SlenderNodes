#!/usr/bin/env bash

./manage.py register_existing_packages | tee register_existing_packages.log
./manage.py process_population_queue | tee pasta_gmn_adapter.log
