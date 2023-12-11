.. _caching:

Caching
=============


Purpose
-------

earthkit-data uses a dedicated **directory** to store the results of remote data access and some GRIB/BUFR indexing information. By default this directory is **unmanaged** (its size is not checked/limited) and **no caching** is provided for the files in it, i.e. repeated calls to :func:`from_source` for remote services and URLs will download the data again!

When **caching is enabled** this directory will also serve as a **cache**. It means if we run :func:`from_source` again with the same arguments it will load the data from the cache instead of downloading it again. Additionally, caching offers **monitoring and disk space management**. When the cache is full, cached data is deleted according to the settings (i.e. oldest data is deleted first). The cache is implemented by using a sqlite database running in a separate thread.

Please note that the earthkit-data cache configuration is managed through the :doc:`settings`.

.. warning::

  By default the caching is disabled, i.e. the :ref:`cache-policy <cache_policies>` is "off".

.. warning::

    The earthkit-data cache is intended to be used by a single user.
    Sharing cache with **multiple users is not recommended**.
    Downloading a local copy of data on a shared disk to have multiple
    users working is a different use case and should be supported
    through using mirrors.

.. _cache_location:
.. _cache_policies:

Cache policies
------------------------------

The primary key to control the cache in the settings is ``cache-policy``, which can take the following values:

  - :ref:`off <off_cache_policy>` (default)
  - :ref:`temporary <temporary_cache_policy>`
  - :ref:`user <user_cache_policy>`

The cache location can be read and modified with Python (see the details below).

.. tip::

   See the :ref:`/examples/cache.ipynb` notebook for examples.

.. note::

  It is recommended to restart your Jupyter kernels after changing
  the cache policy or location.

.. _off_cache_policy:

Off cache policy
++++++++++++++++++++++++

When the ``cache-policy`` is "off" no caching is available. This is the **default** value. In this case all files are downloaded into an **unmanaged** temporary directory created by ``tempfile.TemporaryDirectory``. Since caching is disabled, all repeated calls to :func:`from_source` for remote services and URLSs will download the data again! This temporary directory will be unique for each earthkit-data session. When the directory object goes out of scope (at the latest on exit) the directory will be **cleaned up**.

Due to the temporary nature of this directory path it cannot be queried via the :doc:`settings`, but we need to call the :meth:`~data.core.caching.Cache.directory` :ref:`cache method <cache_methods>`.

.. code-block:: python

  >>> from earthkit.data import cache, settings
  >>> settings.set("cache-policy", "off")
  >>> cache.directory()
  '/var/folders/ng/g0zkhc2s42xbslpsywwp_26m0000gn/T/tmp_5bf5kq8'

We can specify the parent directory for the the temporary directory by using the ``temporary-directory-root`` settings. By default it is set to None (no parent directory specified).

.. code-block:: python

  >>> from earthkit.data import cache, setting
  >>> s = {
  ...     "cache-policy": "off",
  ...     "temporary-directory-root": "~/my_demo_tmp",
  ... }
  >>> settings.set(s)
  >>> cache.directory()
  '~/my_demo_tmp/tmp0iiuvsz5'

.. _temporary_cache_policy:

Temporary cache policy
++++++++++++++++++++++++

When the ``cache-policy`` is "temporary" the **cache will be active and located in a managed** temporary directory created by ``tempfile.TemporaryDirectory``. This directory will be unique for each earthkit-data session. When the directory object goes out of scope (at the latest on exit) the cache is **cleaned up**.

Due to the temporary nature of this directory path it cannot be queried via the :doc:`settings`, but we need to call the :meth:`~data.core.caching.Cache.directory` :ref:`cache method <cache_methods>`.

.. code-block:: python

  >>> from earthkit.data import cache, settings
  >>> settings.set("cache-policy", "temporary")
  >>> cache.directory()
  '/var/folders/ng/g0zkhc2s42xbslpsywwp_26m0000gn/T/tmp_5bf5kq8'

We can specify the parent directory for the the temporary cache by using the ``temporary-cache-directory-root`` settings. By default it is set to None (no parent directory specified).

.. code-block:: python

  >>> from earthkit.data import cache, setting
  >>> s = {
  ...     "cache-policy": "temporary",
  ...     "temporary-cache-directory-root": "~/my_demo_cache",
  ... }
  >>> settings.set(s)
  >>> cache.directory()
  '~/my_demo_cache/tmp0iiuvsz5'

.. _user_cache_policy:

User cache policy
+++++++++++++++++++

When the ``cache-policy`` is "user" the **cache will be active** and created in a **managed directory** defined by the ``user-cache-directory`` settings.

The user cache directory is **not cleaned up on exit**. So next time you start earthkit-data it will be there again unless it is deleted manually or it is set in way that on each startup a different path is assigned to it. Also, when you run multiple sessions of earthkit-data under the same user they will share the same cache.

The default value of the user cache directory depends on your system:

  - ``/tmp/earthkit-data-$USER`` for Linux,
  - ``C:\\Users\\$USER\\AppData\\Local\\Temp\\earthkit-data-$USER`` for Windows
  - ``/tmp/.../earthkit-data-$USER`` for MacOS


We can query the directory path via the :doc:`settings` and also by calling the :meth:`~data.core.caching.Cache.directory` :ref:`cache method <cache_methods>`.

.. code-block:: python

  >>> from earthkit.data import cache, settings
  >>> settings.set("cache-policy", "user")
  >>> settings.get("user-cache-directory")
  /tmp/earthkit-data-myusername
  >>> cache.directory()
  /tmp/earthkit-data-myusername


The following code shows how to change the ``user-cache-directory`` settings:

.. code:: python

  >>> from earthkit.data import settings
  >>> settings.get("user-cache-directory")  # Find the current cache directory
  /tmp/earthkit-data-myusername
  >>> # Change the value of the setting
  >>> settings.set("cache-user-directory", "/big-disk/earthkit-data-cache")

  # Python kernel restarted

  >>> from earthkit.data import settings
  >>> settings.get("user-cache-directory")  # Cache directory has been modified
  /big-disk/earthkit-data-cache

More generally, the earthkit-data settings can be read, modified, reset
to their default values from Python,
see the :doc:`Settings documentation <settings>`.

.. _cache_object:
.. _cache_methods:

Cache methods
-------------------------

The cache is controlled by a global object, which we can access as ``earthkit.data.cache``.

.. code:: python

  >>> from earthkit.data import cache
  >>> cache
  <earthkit.data.core.caching.Cache object at 0x117be7040>


When ``cache-policy`` is :ref:`user <user_cache_policy>` or :ref:`temporary <temporary_cache_policy>`
there are a set of methods available on this object to manage and interact with the cache.

.. list-table:: Methods/properties of the cache object
   :header-rows: 1

   * - Methods
     - Description

   * - :attr:`~data.core.caching.Cache.policy`
     - Get the current cache policy object.
   * - :meth:`~data.core.caching.Cache.directory`
     - Return the path to the current cache directory
   * - :meth:`~data.core.caching.Cache.size`
     - Return the total number of bytes stored in the cache
   * - :meth:`~data.core.caching.Cache.check_size`
     - Check the cache size and trim it down when needed.
   * - :meth:`~data.core.caching.Cache.entries`
     - Dump the entries stored in the cache
   * - :meth:`~data.core.caching.Cache.summary_dump_database`
     - Return the number of items and total size of the cache
   * - :meth:`~data.core.caching.Cache.purge`
     - Delete entries from the cache

.. warning::

    :meth:`~data.core.caching.Cache.check_size` automatically runs when a new
    entry is added to the cache or any of the :ref:`cache_settings` changes.

Examples:

.. code:: python

      >>> from earthkit.data import cache
      >>> cache.policy.name
      'user'
      >>> cache.directory()
      '/var/folders/ng/g0zkhc2s42xbslpsywwp_26m0000gn/T/earthkit-data-cgr'
      >>> cache.size()
      846785699
      >>> cache.summary_dump_database()
      (40, 846785699)
      >>> d = cache.entries()
      >>> len(d)
      40
      >>> d[0].get("creation_date")
      '2023-10-30 14:48:31.320322'


Cache limits
------------

.. warning::

  These settings does not work when ``cache-policy`` is :ref:`off <off_cache_policy>` .


Maximum-cache-size
  The ``maximum-cache-size`` setting ensures that earthkit-data does not
  use to much disk space.  Its value sets
  the maximum disk space used by earthkit-data cache.  When earthkit-data cache disk
  usage goes above this limit, earthkit-data triggers its cache cleaning mechanism  before
  downloading additional data.  The value of cache-maximum-size is
  absolute (such as "10G", "10M", "1K"). To disable it use None.

Maximum-cache-disk-usage
  The ``maximum-cache-disk-usage`` setting ensures that earthkit-data
  leaves does not fill your disk.
  Its values sets the maximum disk usage as % of the filesystem containing the cache
  directory. When the disk space goes below this limit, earthkit-data triggers
  its cache cleaning mechanism before downloading additional data.
  The value of maximum-cache-disk-usage is relative (such as "90%" or "100%").
  To disable it use None.

.. warning::
    If your disk is filled by another application, earthkit-data will happily
    delete its cached data to make room for the other application as soon
    as it has a chance.

.. .. note::
..     When tweaking the cache settings, it is recommended to set the
..     ``maximum-cache-size`` to a value below the user disk quota (if applicable)
..     and ``maximum-cache-disk-usage`` to ``None``.


.. _cache_settings:

Cache settings parameters
-------------------------------

.. module-output:: generate_settings_rst .*-cache-.* cache-.* .*-cache

Other earthkit-data settings can be found :ref:`here <settings_table>`.
