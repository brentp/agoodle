Agoodle: GDAL + numpy
=====================

Access raster datasets through `GDAL`_ as `numpy`_ arrays.

:Author: Brent Pedersen (brentp), Josh Livni (jlivni)
:Email: bpederse@gmail.com
:License: MIT

.. contents ::


Summary
=======

::

    >>> from agoodle import AGoodle
    >>> g = AGoodle('agoodle/tests/data/z.tif')
    >>> g.raster_info.extent
    (-13249847.854555907, 4515032.8277741019, -13181883.342945984, 4598109.0017419849)



Installation
============

Requirements
------------

  1) `GDAL`_ configure with --with-python to enable python bindings.
  2) `numpy`_
  3) `matplotlib`_

Agoodle
-------
get agoodle, run tests, install::

    git clone http://github.com/brentp/agoodle/
    cd agoodle
    python setup.py install

Usage
=====


Development
===========

please fork, patch, document, contribute.


.. _`GDAL`: http://gdal.osgeo.org
.. _`numpy`: http://numpy.scipy.org
.. _`matplotlib`: http://matplotlib.sourceforge.net
