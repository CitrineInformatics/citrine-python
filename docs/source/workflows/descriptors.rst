Descriptors
===========

Descriptors allow users to define a controlled vocabulary with which to describe the physical context of an AI task.
Each descriptor defines a term in that vocabulary, which is comprised of a name, a datatype, and bounds on that data type.
If you are familiar with the GEMD data model, descriptors are roughly equivalent to :class:`AttributeTemplates <citrine.resources.attribute_templates.AttributeTemplate>`.

The AI Engine currently supports 5 kinds of descriptors:

-  `Real Descriptors <#real-descriptor>`__
-  `Categorical Descriptor <#categorical-descriptor>`__
-  `Chemical Formula Descriptor <#chemical-formula-descriptor>`__
-  `Molecular Structure Descriptor <#molecular-structure-descriptor>`__
-  `Formulation Descriptor <#formulation-descriptor>`__

Real Descriptor
---------------

:class:`~citrine.informatics.descriptors.RealDescriptor` is used to represent continuous variables.
Each Real Descriptor must provide a lower and upper bound, which is used to both validate input data and as a prior when making predictions.
If you are not sure what bounds to use, you may want to look at the attribute templates to see if another user has defined bounds for you.
It is better to err on the side of broader bounds rather than narrower ones.

Additionally, each Real Descriptor defines the units of every variable associated with that descriptor.
Any `GEMD-compatible <https://citrineinformatics.github.io/gemd-python/depth/unit_parsing.html>`__ unit string may be used.
If a variable is dimensionless, you can use an empty string.

Categorical Descriptor
----------------------

:class:`~citrine.informatics.descriptors.CategoricalDescriptor` is used to represent variables that can take one of
a set of values, i.e. categories.
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

:class:`~citrine.informatics.descriptors.FormulationDescriptor` is used to represent variables that contain information
about mixtures of other materials.
The Formulation Descriptor has no parameters other than a name.


Platform Vocabularies
=====================

A set of descriptors defines a controlled vocabulary with which to describe AI tasks.
The :class:`~citrine.builders.descriptors.PlatformVocabulary` class is provided to collect a set of descriptors,
associate them with short convenient names, and provide them via a familiar dictionary interface.

While descriptors cannot be independently saved on the platform for reuse, :class:`~citrine.resources.attribute_templates.AttributeTemplate`s can be.
Therefore, common descriptors can be saved as attribute templates to the data platform, effectively sharing them with other users.
:meth:`~citrine.builders.descriptors.PlatformVocabulary.from_templates` facilitates this pattern by automatically downloading attribute templates and converting them into descriptors.
Attribute templates must be associated with a namespace via custom identifiers (the `uids` field).
When calling ``from_templates``, a scope is provided to select one of those namespaces.
The descriptors can then be associated with the names from that namespace.

.. code:: python

   from citrine import Citrine
   from citrine.resources.property_template import PropertyTemplate
   from citrine.builders.descriptors import PlatformVocabulary

   # create a session with citrine using your API key
   session = Citrine(api_key = API_KEY)

   # create project
   project = session.projects.register('Example project')

   # create an property template for density
   project.property_templates.register(PropertyTemplate(
       name="density",
       uids={"my_templates": "rho"},
       bounds=RealBounds(lower_bound=0, upper_bound=100, default_units="g/cm^3")
   ))

   # create a condition template for temperature
   project.property_templates.register(PropertyTemplate(
       name="temperature",
       uids={"my_templates": "T"},
       bounds=RealBounds(lower_bound=0, upper_bound=1000000, default_units="kelvin")
   ))

   # create a PlatformVocabulary from the templates
   pv = PlatformVocabulary.from_templates(project=project, scope="my_templates")

   # see the terms in the platform vocabulary
   print(list(pv))
   # returns ["rho", "T"]

   # access a descriptor from the platform vocabulary
   print(pv["T"])
   # returns RealDescriptor(key="temperature", lower_bound=0, upper_bound=1000000, units="K")
