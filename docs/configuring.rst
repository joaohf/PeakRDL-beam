Configuring PeakRDL-beam
========================

If using the `PeakRDL command line tool <https://peakrdl.readthedocs.io/>`_,
some aspects of the ``beam`` command can be configured  via the PeakRDL TOML
file. Any equivalent command-line options will always take precedence.

All BEAM specific options are defined under the ``[beam]`` TOML heading.

For example:

.. code-block:: toml

    [beam]
    flavor = "erlang"
    bitfields = "ltoh"



.. data:: flavor

    Select the BEAM languages (``erlang`` or ``elixir``) that generated output
    will conform to.


.. data:: bitfields

    Since the packing order of bit syntax is implementation defined, the
    packing order must be explicitly specified as ``ltoh`` or ``htol``.

