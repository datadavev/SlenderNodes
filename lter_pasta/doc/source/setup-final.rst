Final configuration and startup
===============================

Security
~~~~~~~~

The Adapter does not limit access to its pasta and admin endpoints. It is
assumed that access to the Adapter is controlled at the firewall level. By
default, the Adapter runs on port 80. Only PASTA should have access to the
http://fqdn/pasta/new_package endpoint and only the PASTA-GMN administrator
should have access to http://fqdn/admin/\*. All other systems must be blocked
with firewall rules.


Secret key
~~~~~~~~~~

Django requires a unique, secret key to be set up for each application.

  Set a random secret key in ``settings.py``::

    $ cd /var/local/dataone/pasta_gmn_adapter
    $ sed -i 's/^SECRET_KEY.*/SECRET_KEY = '\'`openssl rand -hex 32`\''/' settings.py


Initialize the database
~~~~~~~~~~~~~~~~~~~~~~~

::

  $ cd /var/local/dataone/pasta_gmn_adapter
  $ psql --dbname pasta_gmn_adapter --file deployment/pasta_gmn_adapter.sql

The above procedure can also be used for clearing the database.


Filesystem permissions
~~~~~~~~~~~~~~~~~~~~~~

Set all the files to be owned by the gmn account, and to be writable by www-data::

  $ cd /var/local/dataone/
  $ sudo chown -R gmn:www-data .
  $ sudo chmod -R g+w .

Set the private keys to be readable only by the gmn user::

    $ cd /var/local/dataone/certs
    $ sudo chmod 400 `find /var/local/dataone/certs -name '*_key*'


Firewall
~~~~~~~~

Make sure that HTTP is allowed through the firewall::

  $ sudo ufw allow 80


Misc settings
~~~~~~~~~~~~~

Update any settings in ``settings.py`` that need to be changed. Each setting is
described in that file.


Starting PASTA-GMN Adapter
~~~~~~~~~~~~~~~~~~~~~~~~~~

PASTA-GMN Adapter should now be ready to start. Simply restart Apache::

  $ sudo service apache2 restart
