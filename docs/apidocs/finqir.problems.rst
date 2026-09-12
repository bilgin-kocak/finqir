.. _finqir-problems:

Structured finance problems
===========================

.. automodule:: finqir.problems
   :members:
   :show-inheritance:

Mean-variance example
---------------------

The expected-return and risk components remain separately inspectable even
after they are combined into one minimization objective.

.. code-block:: python

   from finqir import (
       Asset,
       Cardinality,
       ExpectedReturn,
       StructuredPortfolioProblem,
       VarianceRisk,
   )

   problem = StructuredPortfolioProblem(
       assets=[Asset("bond"), Asset("equity")],
       objectives=[
           ExpectedReturn([0.04, 0.10], weight=-1.0),
           VarianceRisk([[0.01, 0.0], [0.0, 0.09]], weight=0.5),
       ],
       constraints=[Cardinality(exactly=1)],
   )

   evaluation = problem.evaluate((0, 1))
   assert abs(evaluation.total + 0.055) < 1e-12
   assert problem.check_feasibility((0, 1)).is_feasible
