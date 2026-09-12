.. _finqir-benchmarks:

Benchmarks and baselines
========================

.. automodule:: finqir.benchmarks
   :members:
   :show-inheritance:

TRUBA adapter
-------------

Validate compatible hackathon inputs and compute exact SciPy MILP baselines:

.. code-block:: console

   python -m finqir.benchmarks.truba validate --input-dir /path/to/truba/inputs

Official contest inputs are not redistributed with FinQIR. Each loaded input
records its SHA-256 digest so benchmark reports can identify source data.
