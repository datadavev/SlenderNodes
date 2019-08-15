Install the PASTA-GMN Adapter
=============================

The Adapter is a web app implemented in :term:`Python` based on the
:term:`Django` framework. Django is :term:`WSGI` compliant. The PASTA-GMN
Adapter is served by :term:`Apache` via :term:`mod_wsgi`.

.. graphviz::

  digraph G {
    dpi=72;

    "DataONE Client" -> "DataONE Common" -> "PASTA-GMN Adapter";
    Apache -> mod_wsgi -> Django -> "PASTA-GMN Adapter";

    {
      rank=same
      PASTA
      "PASTA-GMN Adapter" [shape=box, color=blue]
      "DataONE Generic Member Node (GMN)"
      PASTA -> "PASTA-GMN Adapter" -> "DataONE Generic Member Node (GMN)"
    }
  }


GMN software stack
~~~~~~~~~~~~~~~~~~

This setup documentation describes how to set the adapter up to run in the same
Python virtual environment as GMN and sharing GMN's dependencies. Thus, the
first step in setting up the adapter is setting up GMN. GMN is distributed via
PyPI. Install GMN as described in the documentation hosted on PyPI, at
https://dataone-python.readthedocs.io/en/latest/gmn/index.html.


PASTA-GMN Adapter software stack
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PASTA-GMN Adapter is distributed via git.

