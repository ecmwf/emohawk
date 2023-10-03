.. _caching:

Caching
=============

.. warning::

     This part of eartkit-data is still a work in progress. Documentation
     and code behaviour will change.

Purpose
-------

earthkit-data caches most of the remote data access on a local cache. Running again
:func:`from_source` will use the cached data instead of
downloading it again. When the cache is full, cached data is deleted according it cache policy
(i.e. oldest data is deleted first).
earthkit-data cache configuration is managed through the :doc:`settings`.

.. warning::

    The earthkit-data cache is intended to be used by a single user.
    Sharing cache with **multiple users is not recommended**.
    Downloading a local copy of data on a shared disk to have multiple
    users working is a different use case and should be supported
    through using mirrors.

.. _cache_location:
.. _cache_policies:

Cache policies and locations
------------------------------

The primary key to control the cache in the settings is ``cache‑policy``, which can take the following values:

  - "user" (default)
  - "temporary"
  - "off"

The cache location can be read and modified with Python (see the details below).

.. tip::

   See the :ref:`/examples/cache.ipynb` notebook for examples.

.. note::

  It is recommended to restart your Jupyter kernels after changing
  the cache location.

User cache policy
+++++++++++++++++++

When the ``cache‑policy`` is "user" the cache is created in the directory defined by the ``user-cache-directory`` settings. The user cache directory is not cleaned up on exit. So next time you start earthkit-data it will (probably) be there again. Also, when you run multiple sessions of earthkit-data under the same user they will share the same cache.

The default value of the cache directory depends on your system:

  - ``/tmp/earthkit-data-$USER`` for Linux,
  - ``C:\\Users\\$USER\\AppData\\Local\\Temp\\earthkit-data-$USER`` for Windows
  - ``/tmp/.../earthkit-data-$USER`` for MacOS


The following code shows how to change the ``user-cache-directory`` settings:

.. code:: python

  >>> from earthkit.data import settings
  >>> settings.get("user-cache-directory")  # Find the current cache directory
  /tmp/earthkit-data-$USER
  >>> # Change the value of the setting
  >>> settings.set("cache-directory", "/big-disk/earthkit-data-cache")

  # Python kernel restarted

  >>> from earthkit.data import settings
  >>> settings.get("user-cache-directory")  # Cache directory has been modified
  /big-disk/earthkit-data-cache

More generally, the earthkit-data settings can be read, modified, reset
to their default values from Python,
see the :doc:`Settings documentation <settings>`.


Temporary cache policy
++++++++++++++++++++++++

When the ``cache‑policy`` is "temporary" the cache will be located in a temporary directory created by ``tempfile.TemporaryDirectory``. This directory will be unique for each earthkit-data session. When the directory object goes out of scope (at the latest on exit) the cache is cleaned up. Due to the temporary nature of this directory path it cannot be queried via the :doc:`settings`, but we need to use :meth:`cache_directory` on the ``cache`` object.

.. code-block:: python

  >>> from earthkit.data import cache, settings
  >>> settings.set("cache-policy", "temporary")
  >>> cache.cache_directory()
  '/var/folders/ng/g0zkhc2s42xbslpsywwp_26m0000gn/T/tmp_5bf5kq8'

We can specify the parent directory for the the temporary cache by using the ``temporary-cache-directory-root`` settings. By default it is set to None (no parent directory specified).

.. code-block:: python

  >>> from earthkit.data import cache, setting
  >>> s = {
  ...     "cache-policy": "temporary",
  ...     "temporary-cache-directory-root": "~/my_demo_cache",
  ... }
  >>> settings.set(s)
  >>> cache.cache_directory()
  '~/my_demo_cache/tmp0iiuvsz5'

Off cache policy
++++++++++++++++++++++++

It is also possible to turn caching off completely by setting the ``cache-policy`` to “off”.

.. warning::

  At the moment, when the cache is disabled none of the sources downloading data  (e.g. :ref:`data-sources-mars`) will work. On top of that the  :ref:`data-sources-file` source will not be able to handle archive input (e.g. tar, zip).

Cache limits
------------

Maximum-cache-size
  The ``maximum-cache-size`` setting ensures that earthkit-data does not
  use to much disk space.  Its value sets the maximum disk space used
  by earthkit-data cache.  When earthkit-data cache disk usage goes above
  this limit, earthkit-data triggers its cache cleaning mechanism  before
  downloading additional data.  The value of cache-maximum-size is
  absolute (such as "10G", "10M", "1K").

Maximum-cache-disk-usage
  The ``maximum-cache-disk-usage`` setting ensures that earthkit-data
  leaves does not fill your disk.
  Its values sets the maximum disk usage as % of the filesystem containing the cache
  directory. When the disk space goes below this limit, earthkit-data triggers
  its cache cleaning mechanism before downloading additional data.
  The value of maximum-cache-disk-usage is relative (such as "90%" or "100%").

.. warning::
    If your disk is filled by another application, earthkit-data will happily
    delete its cached data to make room for the other application as soon
    as it has a chance.

.. note::
    When tweaking the cache settings, it is recommended to set the
    ``maximum-cache-size`` to a value below the user disk quota (if applicable)
    and ``maximum-cache-disk-usage`` to ``None``.


Caching settings parameters
-------------------------------

.. module-output:: generate_settings_rst .*-cache-.* cache-.* .*-cache

Other earthkit-data settings can be found :ref:`here <settings_table>`.
