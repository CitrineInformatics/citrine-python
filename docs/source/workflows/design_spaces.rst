Design Spaces
=============

A design space defines a set of materials that should be searched over when performing a material design.
Design Spaces must be registered to be used in a :doc:`design workflow <design_workflows>`.
Currently, there are four design spaces:

-  `ProductDesignSpace <#product-design-space>`__
-  `EnumeratedDesignSpace <#enumerated-design-space>`__
-  `DataSourceDesignSpace <#data-source-design-space>`__
-  `FormulationDesignSpace <#formulation-design-space>`__

Product design space
--------------------

Materials from a product design space are composed from the `Cartesian product`_ of univariate dimensions.
A dimension defines valid values of a single variable.
Valid values can be discrete sets (i.e. enumerated using a list) or continuous ranges (i.e. defined by upper and lower bounds on real numbers).
This design space samples materials by taking one element from each of the dimensions.
For example, given dimensions ``temperature = [300, 400]`` and ``time = [1, 5, 10]`` the Cartesian product is:

.. _`Cartesian product`: https://en.wikipedia.org/wiki/Cartesian_product

.. code:: python

   candidates = [
     {"temperature": 300, "time": 1},
     {"temperature": 300, "time": 5},
     {"temperature": 300, "time": 10},
     {"temperature": 400, "time": 1},
     {"temperature": 400, "time": 5},
     {"temperature": 400, "time": 10}
   ]

The defining method of a design space is the ability to draw samples from it.
If a continuous range is included, a random sample is drawn for that variable, and finite variables are exhaustively enumerated.
Once all combinations of finite variables have been sampled, the cycle repeats while continuing to sample new values from the infinite dimension.

Finite sets of value are defined using an :class:`~citrine.informatics.dimensions.EnumeratedDimension`.
Valid variable values are specified using a list of strings.
An enumerated dimension of two temperatures, for example, can be specified using the python SDK via:

.. code:: python

   from citrine.informatics.descriptors import RealDescriptor
   from citrine.informatics.dimensions import EnumeratedDimension

   descriptor = RealDescriptor(key='Temperature', lower_bound=273, upper_bound=1000, units='K')
   dimension = EnumeratedDimension(descriptor, values=['300', '400'])

Continuous ranges of values are defined using a :class:`~citrine.informatics.dimensions.ContinuousDimension`.
Upper and lower bounds define the range of values we wish to uniformly sample from.
If, using the previous example, temperature can be any value between 300 and 400K the dimension would be created using:

.. code:: python

   from citrine.informatics.dimensions import ContinuousDimension

   dimension = ContinuousDimension(descriptor, lower_bound=300, upper_bound=400)

Note, the upper and lower bounds of the dimension do not need to match those of the descriptor.
The bounds of the descriptor define the minimum and maximum temperatures that could be considered valid, e.g. our furnace can only reach 1000K.
The bounds of the dimension are the bounds we wish to search between, e.g. restrict the search between 300 and 400K (even though the furnace heat go to much higher temperatures).

Multiple :class:`~citrine.informatics.dimensions.EnumeratedDimension` and :class:`~citrine.informatics.dimensions.ContinuousDimension` objects can be combined to form a :class:`~citrine.informatics.design_spaces.product_design_space.ProductDesignSpace`:

.. code:: python

    from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor
    from citrine.informatics.dimensions import ContinuousDimension, EnumeratedDimension
    from citrine.informatics.design_spaces import ProductDesignSpace

    temp_descriptor = RealDescriptor(key='Temperature', lower_bound=273, upper_bound=1000, units='K')
    temp_dimension = ContinuousDimension(temp_descriptor, lower_bound=300, upper_bound=400)

    speed_descriptor = CategoricalDescriptor(key='Mixing Speed', categories=["Slow", "Medium", "Fast"])
    speed_dimension = EnumeratedDimension(speed_descriptor, values=["Slow", "Fast"])

    speed_and_temp = ProductDesignSpace(
        name="Speed and temperature",
        description="Temperatures between 300 and 400 K and either Slow or Fast",
        dimensions=[temp_dimension, speed_dimension]
    )

    speed_and_temp_design_space = project.design_spaces.register(speed_and_temp)

Enumerated design space
-----------------------

An enumerated design space is composed of an explicit list of candidates.
Each candidate is specified using a dictionary keyed on the key of a corresponding :class:`~citrine.informatics.descriptors.Descriptor`.
A list of descriptors defines what key-value pairs must be present in each candidate.
If a candidate is missing a descriptor key-value pair, contains extra key-value pairs or any value is not valid for the corresponding descriptor, it is removed from the design space.

As an example, an enumerated design space that represents points from a 2D Cartesian coordinate system can be created using the python SDK:

.. code:: python

   from citrine.informatics.descriptors import RealDescriptor
   from citrine.informatics.design_spaces import EnumeratedDesignSpace

   x = RealDescriptor(key='x', lower_bound=0, upper_bound=10)
   y = RealDescriptor(key='y', lower_bound=0, upper_bound=10)
   descriptors = [x, y]

   # create a list of candidates
   # invalid candidates will be removed from the design space
   candidates = [
     {'x': 0, 'y': 0},
     {'x': 0, 'y': 1},
     {'x': 2, 'y': 3},
     {'x': 10, 'y': 10},
     # invalid because x > 10
     {'x': 11, 'y': 10},
     # invalid because z isn't in descriptors
     {'x': 11, 'y': 10, 'z': 0},
     # invalid because y is missing
     {'x': 10}
   ]

   design_space = EnumeratedDesignSpace(
     name='2D coordinate system',
     description='Design space that contains (x, y) points',
     descriptors=descriptors,
     data=candidates
   )

   registered_design_space = project.design_spaces.register(design_space)

Data Source Design Space
------------------------

A data source design space is similar in spirit to an enumerated design space, but the candidates are drawn from an existing data source instead of being specified through a list of dictionaries.
Any data source can be used and no additional information is needed.

For example, assume you have a :class:`~citrine.resources.gemtables.GemTable` that contains one
:class:`~citrine.gemtables.rows.Row` for each candidate that you wish to test.
Assume the table's `table_id` and `table_version` are known.
The example code below creates a registers a design space based on this Gem Table.

.. code:: python

    from citrine.informatics.data_sources import GemTableDataSource
    from citrine.informatics.design_spaces import DataSourceDesignSpace

    data_source = GemTableDataSource(
        table_id=table_id,
        table_version=table_version
    )

    design_space = DataSourceDesignSpace(
        name="my candidates",
        description="450 potential formulations",
        data_source=data_source
    )

    registered_design_space = project.design_spaces.register(design_space)

Formulation Design Space
------------------------

A formulation design space defines the set of formulations that can be produced from a given set of ingredient names, labels and constraints.
Ingredient names are specified as a set of strings, where each string is a unique ingredient name, e.g., ``{'water', 'salt'}`` to a design space with two ingredients.
Labels are specified as a mapping from each label to a set of ingredient names that should be given that label is present in a formulation, e.g., ``{'solute': {'salt'}}``.
An ingredient may be given multiple labels, and these labels are static.
An ingredient will always be given all applicable labels when present in a formulation.

Constraints restrict the total number or fractional amount of ingredients in formulations sampled from the design space.
There are three constraints that can be specified as part of a formulation design space:

- :class:`~citrine.informatics.constraints.ingredient_count_constraint.IngredientCountConstraint` constrains the total number of ingredients in a formulation.
  At least one ingredient count constraint that constrains the total number of ingredients in formulations emitted from the space is required.
  Formulation design spaces without this constraint will fail validation.
  Additional ingredient count constraints may specify a label.
  If specified, only ingredients with the given label count towards the constraint total.
  This could be used, for example, to constrain the total number of solutes in a formulation.
- :class:`~citrine.informatics.constraints.ingredient_fraction_constraint.IngredientFractionConstraint` restricts the fractional amount of a single formulation ingredient between minimum and maximum bounds.
- :class:`~citrine.informatics.constraints.label_fraction_constraint.LabelFractionConstraint` restricts the total fraction of ingredients with a given label in a formulation between minimum and maximum bounds.
  This could be used, for example, to ensure the total fraction of ingredients labeled as solute is within a given range.

All minimum and maximum bounds for these three formulation constraints are inclusive.
Additionally, fractional constraints have an ``is_required`` flag.
By default ``is_required == True``, and ingredient and label fractions must be within the minimum and maximum bound defined by the constraint.
If set to ``False``, the fractional amount must be within the specified bounds *only* when the constrained ingredient (for ingredient fraction constraints) or any ingredient with the given label (for label fraction constraints) present in a formulation.
Setting ``is_required`` to ``False`` effectively adds 0 as a valid value.

Formulation design spaces define an inherent ``resolution`` for formulations sampled from the domain.
This resolution defines the minimum step size between consecutive formulations sampled from the space.
Resolution does not impose a grid over fractional ingredient amounts.
Instead, it provides a manner to specify the characteristic length scale for the problem.
Set resolution to the minimum changed to a fractional ingredient amount that your problem is sensitive to.
The default resolution is 0.01, which means consecutive samples from the domain will displace a fractional amount 0.01 or greater between two ingredients.

Formulations sampled from the design space will be stored using the :class:`~citrine.informatics.descriptors.FormulationDescriptor` defined when the design space is configured.
Each formulation contains two pieces of information: a recipe and information about ingredient labels.
Each recipe can be thought of as a map from ingredient name to its fractional amount, e.g., ``{'water': 0.99, 'salt': 0.01}``.
Ingredient fractions in recipes sampled from a formulation design space will always sum to 1.
Label information define which labels applied to each ingredient in the recipe.
These labels will always be a subset of all labels from the design space.

The following demonstrates how to create a formulation design space of saline solutions.
There are three ingredients: water, salt and boric acid (a common antiseptic).
We will require that formulations contain 2 ingredients, no more than 1 solute is present and the total fraction of water is between 0.95 and 0.99.

.. code:: python

  from citrine.informatics.descriptors import FormulationDescriptor
  from citrine.informatics.design_spaces import FormulationDesignSpace
  from citrine.informatics.constraints import IngredientCountConstraint, IngredientFractionConstraint

  # define a descriptor to store formulations
  descriptor = FormulationDescriptor('saline solution')

  # set of unique ingredient names
  ingredients = {'water', 'salt', 'boric acid'}

  # labels for each ingredient
  labels = {
    'solute': {'water'},
    'solvent': {'salt', 'boric acid'}
  }

  # constraints on formulations emitted from the design space
  constraints = {
    IngredientCountConstraint(descriptor, min=2, max=2),
    IngredientCountConstraint(descriptor, label='solute' min=1, max=1),
    IngredientFractionConstraint(descriptor, ingredient='water', min=0.95, max=0.99)
  }

  design_space = FormulationDesignSpace(
    name = 'Saline solution design space',
    description = 'Composes formulations from water, salt and boric acid',
    ingredients = ingredients,
    labels = labels,
    constraints = constraints
  )

  registered_design_space = project.design_spaces.register(design_space)
