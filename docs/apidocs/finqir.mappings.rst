.. _finqir-mappings:

Financial mappings
==================

.. automodule:: finqir.mappings
   :members:
   :show-inheritance:

``ConstraintHandling.PENALTY`` keeps the named constraint in the constrained
model and records it for later calibrated-penalty materialization.
``ConstraintHandling.FEASIBLE_SUBSPACE`` records the constraint as a mixer
invariant so it can be excluded from a future cost Hamiltonian. The 0.2
pipeline classifies these choices; it does not silently invent penalty values.
