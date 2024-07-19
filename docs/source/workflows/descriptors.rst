.. _descriptors:

Descriptors
===========

Descriptors allow users to define a controlled vocabulary with which to describe the physical context of an AI task.
Each descriptor defines a term in that vocabulary, which is comprised of a name, a datatype, and bounds on that data type.
If you are familiar with the GEMD data model, descriptors are roughly equivalent to :class:`AttributeTemplates <citrine.resources.attribute_templates.AttributeTemplate>`.

The AI Engine currently supports 5 kinds of descriptors:

-  `Real Descriptors <#real-descriptor>`__
-  `Integer Descriptor <#integer-descriptor>`__
-  `Categorical Descriptor <#categorical-descriptor>`__
-  `Chemical Formula Descriptor <#chemical-formula-descriptor>`__
-  `Molecular Structure Descriptor <#molecular-structure-descriptor>`__
-  `Formulation Descriptor <#formulation-descriptor>`__

Real Descriptor
---------------

:class:`~citrine.informatics.descriptors.RealDescriptor` is used to represent continuous variables.
Each Real Descriptor must provide a lower and upper bound, which is used to both validate input data and as a prior when making predictions.
If you are not sure what bounds to use, you may want to look at the attribute templates to see if another user has defined bounds for you.
It is better to err on the side of broader bounds than narrower ones.

Additionally, each Real Descriptor defines the units of every variable associated with that descriptor.
Any `GEMD-compatible <https://citrineinformatics.github.io/gemd-python/depth/unit_parsing.html>`__ unit string may be used.
If a variable is dimensionless, you can use an empty string.

Integer Descriptor
------------------

:class:`~citrine.informatics.descriptors.IntegerDescriptor` is used to represent discrete, dimensionless variables.
Each Integer Descriptor must provide a lower and upper bound, which is used to both validate input data and as a prior when making predictions.
If you are not sure what bounds to use, you may want to look at the attribute templates to see if another user has defined bounds for you.
It is better to err on the side of broader bounds than narrower ones.

Integer Descriptors are dimensionless and units cannot be specified.

Categorical Descriptor
----------------------

:class:`~citrine.informatics.descriptors.CategoricalDescriptor` is used to represent variables that can take one of
a set of values, i.e., categories.
All of the possible categories must be known ahead of time and specified in the Categorical Descriptor.

Chemical Formula Descriptor
---------------------------

:class:`~citrine.informatics.descriptors.ChemicalFormulaDescriptor` is used to represent variables that should be
interpreted as chemical formulas.
The Chemical Formula Descriptor has no parameters other than a name.

Molecular Structure Descriptor
------------------------------

:class:`~citrine.informatics.descriptors.MolecularStructureDescriptor` is used to represent variables that should be
interpreted as molecular structures.
Both `SMILES <https://en.wikipedia.org/wiki/Simplified_molecular-input_line-entry_system>`__
and `InChI <https://en.wikipedia.org/wiki/International_Chemical_Identifier>`__ are supported.
The Molecular Structure Descriptor has no parameters other than a name.

Formulation Descriptor
------------------------------

:class:`~citrine.informatics.descriptors.FormulationDescriptor`
is used to represent variables that contain information about mixtures of other materials.
The Formulation Descriptor has no parameters other than a name,
of which the two allowed values are 'Formulation' and 'Flat Formulation'.
The key 'Formulation' should be used when referring to mixtures found directly in the training data,
for which the ingredients may be other mixtures themselves.
The key 'Flat Formulation' should be reserved for mixtures comprised of only raw ingredients
produced by a :class:`~citrine.informatics.predictors.simple_mixture_predictor.SimpleMixturePredictor`.

The two allowed formulation descriptors can be obtained by the helper methods
``FormulationDescriptor.hierarchical()`` and ``FormulationDescriptor.flat()``
that produce descriptors with the keys 'Formulation' and 'Flat Formulation', respectively.
