[![Documentation Status](https://readthedocs.org/projects/peakrdl-beam/badge/?version=latest)](https://peakrdl-beam.readthedocs.io)
[![build](https://github.com/joaohf/PeakRDL-beam/workflows/build/badge.svg)](https://github.com/joaohf/PeakRDL-beam/actions?query=workflow%3Abuild+branch%3Amain)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/peakrdl-beam.svg)](https://pypi.org/project/peakrdl-beam)

# PeakRDL for BEAM languages

Generate Erlang or Elixir modules from a SystemRDL register model.

For the command line tool, see the [PeakRDL project](https://peakrdl.readthedocs.io).

This plugin was strongly based on [PeakRDL cheader](https://github.com/SystemRDL/PeakRDL-cheader).

## TODO

* Implement Elixir generator
* Add unit tests

## Documentation

See the [PeakRDL BEAM Documentation](https://peakrdl-beam.readthedocs.io) for more details.

## Development

* Python virtual env

  ```
  python3 -m venv venv
  venv/bin/active
  ```

* Install dependencies

  ```
  pip install -e .
  pip install peakrdl
  ```