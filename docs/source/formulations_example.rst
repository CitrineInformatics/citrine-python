.. formulations_example:

Formulations Example
====================

The Citrine Platform is a powerful tool to analyze formulations data.
A formulation is, generally speaking, a mixture of mixtures.
Individual ingredients are mixed together to form more complex ingredients, which may themselves be mixed with other ingredients and/or mixtures, and so on.
Generally, the top-level formulation has some properties that we with to optimize.
The ingredients themselves may also have known properties, which are useful for understanding the properties of the top-level formulation.
In addition, each mixing process may be characterized by attributes such as the temperature of a reaction vessel or the speed of a mixing element.

The GEMD data model provides a way to record all of the information relevant to a formulations problem,
and Citrine's AI Engine turns this information into trained models that can predict the properties of novel formulations.
This section demonstrates how to express a complete formulations example in Citrine-python, from data ingestion to new candidate generation.