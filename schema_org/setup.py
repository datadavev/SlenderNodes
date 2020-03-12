#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This work was created by participants in the DataONE project, and is
# jointly copyrighted by participating institutions in DataONE. For
# more information on DataONE, see our web site at http://dataone.org.
#
#   Copyright 2013-2019 DataONE
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""DataONE Schema.org package
"""
from setuptools import setup

kwargs = {
    'name': 'schema_org',
    'version': '4.1.5',
    'description': 'Interact with a schema.org resource provider',
    'author': 'DataONE Project',
    'author_email': 'developers@dataone.org',
    'url': 'https://github.com/DataONEorg/d1_python',
    'license': 'Apache License, Version 2.0',
    'packages': ['schema_org', 'schema_org.data', 'schema_org.sotools'],
    'package_data': {'schema_org': ['data/*.ttl']},
    'classifiers': [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    'keywords': (
        'DataONE schema.org'
    ),
    'entry_points': {
        'console_scripts': [
            'd1-validate=schema_org.commandline:validate',
            'd1-check-site=schema_org.commandline:d1_check_site',
            'harvest-abds-ipt=schema_org.commandline:abds_ipt',
            'harvest-arm=schema_org.commandline:arm',
            'harvest-bcodmo=schema_org.commandline:bcodmo',
            'harvest-cuahsi=schema_org.commandline:cuahsi',
            'harvest-ieda=schema_org.commandline:ieda',
            'harvest-nkn=schema_org.commandline:nkn',
        ],
    }
}
setup(**kwargs)
