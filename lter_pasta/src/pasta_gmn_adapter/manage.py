#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import d1_common.util

sys.path.append(d1_common.util.abs_path('./api_types/generated'))

if __name__ == "__main__":
  os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pasta_gmn_adapter.settings")

  from django.core.management import execute_from_command_line

  execute_from_command_line(sys.argv)
