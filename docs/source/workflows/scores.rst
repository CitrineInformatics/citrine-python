Scores
======

Scores rank materials according to a set of objectives and constraints.
An objective defines the goal for a scalar value associated with a particular descriptor.
The goal can be to either maximize or minimize a value by using :class:`~citrine.informatics.objectives.ScalarMaxObjective` or :class:`~citrine.informatics.objectives.ScalarMinObjective`, respectively.
Constraints represent a set of conditions on variables that should be satisfied.
Constraints can used to restrict either a design space or descriptor values in design candidates.
There are five constraint types:

- :class:`~citrine.informatics.constraints.scalar_range_constraint.ScalarRangeConstraint` restricts a scalar value between lower and upper bounds.
- :class:`~citrine.informatics.constraints.categorical_constraint.AcceptableCategoriesConstraint` restricts a descriptor value to a set of acceptable values.
- :class:`~citrine.informatics.constraints.ingredient_count_constraint.IngredientCountConstraint` constrains the total number of ingredients in a formulation, or the total number of ingredients within a labeled class of ingredients.
- :class:`~citrine.informatics.constraints.ingredient_fraction_constraint.IngredientFractionConstraint` restricts the fractional amount of a formulation ingredient between minimum and maximum bounds.
- :class:`~citrine.informatics.constraints.label_fraction_constraint.LabelFractionConstraint` restricts the total fraction of ingredients with a given label in a formulation between minimum and maximum bounds.

A candidate is scored based on the objective value and likelihood of satisfying the constraints.
Higher scores represent “better” materials.

Currently, there are three scores:

-  `Expected improvement <#expected-improvement>`__
-  `Likelihood of improvement <#likelihood-of-improvement>`__
-  `Expected value <#expected-value>`__

Expected improvement
---------------------

Expected improvement (EI) is the magnitude of the expected value of improvement calculated as the integral from the best training objective (i.e. baseline) to infinity of ``p(x)(x-a)``, where ``a`` is the best objective value in the training set.
:class:`~citrine.informatics.scores.EIScore` supports 0 or 1 objective.
If no objective is provided, the score is the probability of satisfying all constraints.

EI is calculated from two components: predicted value and uncertainty.
Higher scores result from a more optimal predicted value, higher uncertainty or both.
Higher predicted values exploit information known about the current dataset, e.g. materials of a given type are known to perform well.
Higher uncertainty leads to exploration of a design space, e.g. little is known about a certain class materials, but materials from this region of the design space could perform well.

Likelihood of improvement
-------------------------

Likelihood of improvement (LI) is the probability that a candidate satisfies a set of constraints and is an improvement over known objective values.
:class:`~citrine.informatics.scores.LIScore` supports 0 or more objectives.
If no objectives are provided, the LI score is 0.
When multiple objectives are present, the score is the probability of the objective that is most likely to be improved.
LI scores are bounded by 0 and 1.

The following demonstrates how to create an LI score and use it when triggering a design workflow:

.. code:: python

   from citrine.informatics.objectives import ScalarMaxObjective
   from citrine.informatics.scores import LIScore

   # create an objective to maximize Shear modulus
   objective = ScalarMaxObjective(descriptor_key='Shear modulus')

   # Baseline is the highest shear modulus from the training data
   # (assumed to be 150 here)
   baseline = 150.0

   # Create an LI score from the objective and baseline
   score = LIScore(
       objectives=[objective],
       baselines=[150.0]
   )

   # assuming you have a validated workflow, the score can be used in a design run via:
   execution = workflow.design_executions.trigger(score)


Expected value
---------------------

Expected value (EV) is the expected value of the objective, penalized if the constraints are unlikely to be satisfied.
:class:`~citrine.informatics.scores.EVScore` supports 0 or 1 objective.
If no objective is provided, the score is the probability of satisfying all constraints.

EV is a purely exploitative scoring strategy.
The candidate with the highest score will be the candidate that is expected to be the best at achieving the objectives
and satisfying the constraints, neglecting any additional value for gaining information about materials being modeled.
EV is unique among the currently available scores in that it ignores the predicted uncertainty in the objectives.
