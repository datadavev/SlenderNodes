PASTA-GMN Adapter setup overview
================================

Setting up the PASTA-GMN Adapter.

This procedure has been verified on Ubuntu 18.04 LTS Server.

The setup process for the PASTA-GMN Adapter closely resembles the one for GMN.
The PASTA-GMN Adapter is designed to be installed side by side with GMN, on a
server on which GMN has already been installed. The Adapter also works much like
GMN, in that it is a Django web application with Django management commands and
asynronous processing. Because of this, background information has been kept to
a minimum in this documentation. The procedures described here should be
familiar after installing GMN, and the GMN documentation contains more
background information.

The instructions describe how to set the PASTA-GMN Adapter up to run in a
separate Apache Virtual Host on a server on which GMN (with its dependencies)
has already been installed.

The PASTA-GMN Adapter software stack is installed into the same Python virtual
environment in which GMN has been installed. This enables the adapter to use the
same dependencies as GMN. It also avoids potential conflicts with other Python
software on the server.

.. toctree::
  :maxdepth: 1

  setup-adapter
  setup-authn-client
  setup-apache
  setup-postgresql
  setup-async
  setup-final
