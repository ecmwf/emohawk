.. _bufr:


BUFR
---------

BUFR (Binary Universal Form for Representation of meteorological data) is a binary data format maintained by WMO. The earthkit-data interface supports both BUFR `edition 3 <https://community.wmo.int/en/activity-areas/wmo-codes/manual-codes/bufr-edition-3-and-crex-edition-1>`_ and `edition 4 <https://library.wmo.int/index.php?lvl=notice_display&id=10684>`_.

BUFRList
+++++++++++

We can read/retrieve BUFR data with :func:`from_source <data-sources>`. The resulting object will be a :obj:`BUFRList <data.readers.bufr.bufr.BUFRList>` representing a list of :obj:`BUFRMessage <data.readers.bufr.bufr.BUFRMessage>`\ s.

The structure of a BUFR message is typically hierarchical and can be rather complex, so the recommended way to deal with BUFR data is to extract the required data with :meth:`to_pandas() <data.readers.bufr.bufr.BUFRList.to_pandas>`
into a pandas DataFrame, which is much easier to work with.

The following table gives us an overview of the :obj:`BUFRList API<data.readers.bufr.bufr.BUFRList>`:

.. list-table:: Highlights of the BUFRList API
   :header-rows: 1

   * - Methods/Operators
     - API
   * - :ref:`conversion`
     - :meth:`to_pandas() <data.readers.bufr.bufr.BUFRList.to_pandas>`
   * - :ref:`concat`
     -
   * - :ref:`iter`
     -
   * - :ref:`slice`
     -
   * - :ref:`sel`
     - :meth:`sel() <data.readers.bufr.bufr.BUFRList.sel>`
   * - :ref:`order_by`
     - :meth:`order_by() <data.readers.bufr.bufr.BUFRList.order_by>`
   * - :ref:`metadata`
     - :meth:`metadata() <data.readers.bufr.bufr.BUFRList.metadata>`
   * - :ref:`inspection`
     - :meth:`ls() <data.readers.bufr.bufr.BUFRList.ls>`, :meth:`head() <data.readers.bufr.bufr.BUFRList.head>`, :meth:`tail() <data.readers.bufr.bufr.BUFRList.tail>`

BUFRMessage
++++++++++++++

A :obj:`BUFRMessage <data.readers.bufr.bufr.BUFRMessage>` represent a single BUFR message. It primarily offers methods to:

 - extract message data/metadata with :meth:`metadata() <data.readers.bufr.bufr.BUFRMessage.metadata>`
 - show the message structure with :meth:`dump() <data.readers.bufr.bufr.BUFRMessage.dump>`

Examples:

    - :ref:`/examples/bufr_temp.ipynb`
    - :ref:`/examples/bufr_synop.ipynb`
