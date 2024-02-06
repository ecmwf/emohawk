.. _settings:

Settings
========

*earthkit-data* is maintaining a set of global settings which control
its behaviour.

The settings are automatically saved in ``~/.earthkit-data/settings.yaml`` and they can
be accessed and modified from Python.

.. tip::

    See the :ref:`/examples/settings.ipynb` notebook for examples.

.. _settings_get:

Accessing settings
------------------

earthkit-data settings can be accessed using the python API:

.. literalinclude:: include/settings-get.py


.. _settings_set:

Changing settings
------------------

.. note::

    It is recommended to restart your Jupyter kernels after changing
    or resetting settings.

earthkit-data settings can be modified using the python API:

.. literalinclude:: include/settings-set.py

.. _settings_temporary:

Temporary settings
------------------

We can create a temporary settings (as a context manager) as a copy of the original settings. We will still refer to it as “settings”, but it is completely independent from the original object and changes are not saved into the yaml file (even when ``settings.auto_save_settings`` is True).

.. literalinclude:: include/settings-temporary.py

Output::

    8
    12
    11


.. _settings_reset:

Resetting settings
------------------

.. note::

    It is recommended to restart your Jupyter kernels after changing
    or resetting settings.

earthkit-data settings can be reset using the python API:

.. literalinclude:: include/settings-reset.py


.. _settings_table:

Settings parameters
-------------------

This is the list of all the settings parameters:

.. module-output:: generate_settings_rst
