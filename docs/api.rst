.. _python_api:

Python API
==========
If you want to embed this tool into your own script, you can do so with the
following API.


Example
-------

The following example shows how to compile a SystemRDL file and then generate
the Erlang modules and header using the Python API.

.. code-block:: python

    from systemrdl import RDLCompiler
    from peakrdl_beam.exporter import ErlangExporter

    # compile the SystemRDL
    rdlc = RDLCompiler()
    rdlc.compile_file('example.rdl')
    top = rdlc.elaborate()

    # generate the Erlang module and header
    exporter = ErlangExporter()
    exporter.export(node=top, path='out.erl')


Exporter Class
--------------

.. autoclass:: peakrdl_beam.exporter.ErlangExporter
    :members:
