Introduction
============

PeakRDL BEAM is a python package which can be used to generate a register
abstraction layer for supported BEAM languages (Erlang and Elixir) a SystemRDL definition.

Features:

* Generates Erlang ``record`` definitions
* Field bit offset, width, mask, etc ``-define`` macros.
* Generates register bit-field and accessor help functions.
.. * Optionally generates a test-case to validate correctness of the generated header.


Installing
----------

Install from `PyPi`_ using pip

.. code-block:: bash

    python3 -m pip install peakrdl-beam

.. _PyPi: https://pypi.org/project/peakrdl-beam


Quick Start
-----------
The easiest way to use PeakRDL-beam is via the `PeakRDL command line tool <https://peakrdl.readthedocs.io/>`_:

.. code-block:: bash

    # Install the command line tool
    python3 -m pip install peakrdl

    # Generate an Erlang module and header
    peakrdl beam example.rdl -o example.erl

Using the generated module and header, you can access your device registers by name!

.. code-block:: erlang

    -include("example.hrl")

    main() ->
        Data = read_register_from_hw(),

        CtrlRecord = example:des_example__CTRL_f(Data),

        io:format("CTRL register ~p~n", [CtrlRecord#atxmega_spi__CTRL.mode]).


Links
-----

- `Source repository <https://github.com/joaohf/PeakRDL-beam>`_
- `Release Notes <https://github.com/joaohf/PeakRDL-beam/releases>`_
- `Issue tracker <https://github.com/joaohf/PeakRDL-beam/issues>`_
- `PyPi <https://pypi.org/project/peakrdl-beam>`_
- `SystemRDL Specification <http://accellera.org/downloads/standards/systemrdl>`_


.. toctree::
    :hidden:

    self
    header_output
    module_output
    configuring
    api
    licensing
