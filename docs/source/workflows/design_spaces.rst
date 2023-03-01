Design Spaces
=====================

A Design Space defines a set of materials that should be searched over when performing a material design.
Design Spaces must be registered to be used in a :doc:`design workflow <design_workflows>`.
Currently, there are four Design Spaces:

-  `EnumeratedDesignSpace <#enumerated-design-space>`__
-  `ProductDesignSpace <#product-design-space>`__
-  `DataSourceDesignSpace <#data-source-design-space>`__
-  `FormulationDesignSpace <#formulation-design-space>`__

Enumerated design space
-----------------------

An :class:`~citrine.informatics.design_spaces.enumerated_design_space.EnumeratedDesignSpace` is composed of an explicit list of candidates.
Each candidate is specified using a dictionary keyed on the key of a corresponding :class:`~citrine.informatics.descriptors.Descriptor`.
A list of descriptors defines what key-value pairs must be present in each candidate.
If a candidate is missing a descriptor key-value pair, contains extra key-value pairs or any value is not valid for the corresponding descriptor, it is removed from the design space.

As an example, an enumerated design space that represents points from a 2D Cartesian coordinate system can be created using the Citrine Python client:

.. code:: python

   from citrine.informatics.descriptors import RealDescriptor
   from citrine.informatics.design_spaces import EnumeratedDesignSpace

   x = RealDescriptor(key='x', lower_bound=0, upper_bound=10, units="")
   y = RealDescriptor(key='y', lower_bound=0, upper_bound=10, units="")
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

Product design space
--------------------

Materials from a :class:`~citrine.informatics.design_spaces.product_design_space.ProductDesignSpace` are composed of the `Cartesian product`_ of independent factors.
Each factor can be a separate design space _or_ a univariate dimension.
Any other type of design space can be a valid subspace.
Subspaces can either be registered on the platform and referenced through their uid, or they can be defined anonymously and embedded in the product design space.

A :class:`~citrine.informatics.dimensions.Dimension` defines valid values of a single variable.
Valid values can be discrete sets (i.e., enumerated using a list) or continuous ranges (i.e., defined by upper and lower bounds on real numbers).
The product design space samples materials by taking all combinations of one element from each dimension.
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

The defining characteristic of a design space is the ability to draw samples from it.
If a continuous range is included, a random sample is drawn for that variable, and finite variables are exhaustively enumerated.
Once all combinations of finite variables have been sampled, the cycle repeats while continuing to sample new values from the infinite dimension.

Finite sets of value are defined using an :class:`~citrine.informatics.dimensions.EnumeratedDimension`.
Valid variable values are specified using a list of strings.
An enumerated dimension of two temperatures, for example, can be specified using the Citrine Python client via:

.. code:: python

   from citrine.informatics.descriptors import RealDescriptor
   from citrine.informatics.dimensions import EnumeratedDimension

   descriptor = RealDescriptor(key='Temperature', lower_bound=273, upper_bound=1000, units='K')
   dimension = EnumeratedDimension(descriptor=descriptor, values=['300', '400'])

Continuous ranges of values are defined using a :class:`~citrine.informatics.dimensions.ContinuousDimension`.
Upper and lower bounds define the range of values we wish to uniformly sample from.
If, using the previous example, temperature can be any value between 300 and 400K the dimension would be created using:

.. code:: python

   from citrine.informatics.dimensions import ContinuousDimension

   dimension = ContinuousDimension(descriptor, lower_bound=300, upper_bound=400)

Note, the upper and lower bounds of the dimension do not need to match those of the descriptor.
The bounds of the descriptor define the minimum and maximum temperatures that could be considered valid, e.g. our furnace can only reach 1000K.
The bounds of the dimension are the bounds we wish to search between, e.g., restrict the search to between 300 and 400K (even though the furnace can go to much higher temperatures).

A product design space combines subspaces in a similar manner, although subspaces are often multivariate.
However the same principle holds for sampling: all combinations of finite factors are enumerated, while infinite factors are sampled continuously.
Note, each factor must be **independent**.
This means that the same descriptor may not appear more than once in a product design space.

As an example, let's create a produt design space that defines the ways in which we might mix two pigments together and stir at some temperature.
We are only interested in specific amounts of each pigment, so we create an enumerated design space that defines the amounts we wish to test.
The mixing speed is discrete, so we describe it with an enumerated dimension.
And temperature is described by a continuous dimension.

.. code:: python

    from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor
    from citrine.informatics.dimensions import ContinuousDimension, EnumeratedDimension
    from citrine.informatics.design_spaces import ProductDesignSpace, EnumeratedDesignSpace

    pigmentA_descriptor = RealDescriptor(key='Amount of Pigment A', lower_bound=0, upper_bound=100, units='g')
    pigmentB_descriptor = RealDescriptor(key='Amount of Pigment B', lower_bound=0, upper_bound=100, units='g')
    enumerated_space = EnumeratedDesignSpace(
        name="amounts of pigments A and B",
        description="total amount of pigment is 100 grams",
        data=[
            {'Amount of Pigment A': 10.0, 'Amount of Pigment B': 90.0},
            {'Amount of Pigment A': 15.0, 'Amount of Pigment B': 85.0},
            {'Amount of Pigment A': 20.0, 'Amount of Pigment B': 80.0}
        ]
    )
    enumerated_space_registered = project.design_spaces.register(enumerated_space)
    enumerated_space_uid = enumerated_space_registered.uid

    temp_descriptor = RealDescriptor(key='Temperature', lower_bound=273, upper_bound=1000, units='K')
    temp_dimension = ContinuousDimension(descriptor=temp_descriptor, lower_bound=300, upper_bound=400)

    speed_descriptor = CategoricalDescriptor(key='Mixing Speed', categories=["Slow", "Medium", "Fast"])
    speed_dimension = EnumeratedDimension(descriptor=speed_descriptor, values=["Slow", "Fast"])

    product_space = ProductDesignSpace(
        name="Mix 2 pigments at some speed and temperature",
        description="Pigments A and B, temperatures between 300 and 400 K, and either Slow or Fast",
        subspaces=[enumerated_space_uid],
        dimensions=[temp_dimension, speed_dimension]
    )

    product_space = project.design_spaces.register(product_space)

In the approach shown above, the enumerated design space is registered on-platform and can be used in other contexts.
It would also be valid, however, to not register the enumerated design space and to include it in the product design space directly as opposed to through its uid: `subspaces=[enumerated_space]`.

The enumerated design space defined in this way might product the following candidates:

.. code:: python

    candidates = [
        {"Amount of Pigment A": 10.0, "Amount of Pigment B": 90.0, "Mixing Speed": "Slow", "Temperature": 329.1356},
        {"Amount of Pigment A": 10.0, "Amount of Pigment B": 90.0, "Mixing Speed": "Fast", "Temperature": 391.5329},
        {"Amount of Pigment A": 15.0, "Amount of Pigment B": 85.0, "Mixing Speed": "Slow", "Temperature": 388.2350},
        {"Amount of Pigment A": 15.0, "Amount of Pigment B": 85.0, "Mixing Speed": "Fast", "Temperature": 347.9817},
        {"Amount of Pigment A": 20.0, "Amount of Pigment B": 80.0, "Mixing Speed": "Slow", "Temperature": 381.8395},
        {"Amount of Pigment A": 20.0, "Amount of Pigment B": 80.0, "Mixing Speed": "Fast", "Temperature": 305.8001},
        {"Amount of Pigment A": 10.0, "Amount of Pigment B": 90.0, "Mixing Speed": "Slow", "Temperature": 338.1545},
        ... # enumerated factors repeat while continuously sampling Temperature
   ]

Data Source Design Space
------------------------

A :class:`~citrine.informatics.design_spaces.data_source_design_space.DataSourceDesignSpace` is similar in spirit to an enumerated design space, but the candidates are drawn from an existing data source instead of being specified through a list of dictionaries.
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

A :class:`~citrine.informatics.design_spaces.formulation_design_space.FormulationDesignSpace` defines the set of formulations that can be produced from a given set of ingredient names, labels, and constraints.
Ingredient names are specified as a set of strings, each mapping to a unique ingredient in a design space.
For example, ``{"water","salt"}`` may be the set of names for a design space with two ingredients.
Labels provide a way to map a string to a set of ingredient names.
For example, salt can be labeled as a solute by specifying the mapping ``{"solute": {"salt"}}``.
An ingredient may be given multiple labels, and an ingredient will always be given all applicable labels when present in a formulation.

Constraints restrict the total number or fractional amount of ingredients in formulations sampled from the design space.
There are three types of constraint that can be specified as part of a formulation design space:

- :class:`~citrine.informatics.constraints.ingredient_count_constraint.IngredientCountConstraint` constrains the total number of ingredients in a formulation.
  At least one constraint on the total number of ingredients is required.
  Formulation Design Spaces without this constraint will fail validation.
  Additional ingredient count constraints may specify a label.
  If specified, only ingredients with the given label count towards the constraint total.
  This could be used, for example, to constrain the total number of solutes in a formulation without constraining the number of solvents.
- :class:`~citrine.informatics.constraints.ingredient_fraction_constraint.IngredientFractionConstraint` restricts the fractional amount of a single formulation ingredient between minimum and maximum bounds.
- :class:`~citrine.informatics.constraints.label_fraction_constraint.LabelFractionConstraint` places minimum and maximum bounds on the sum of fractional amounts of ingredients that have a specified label.
  This could be used, for example, to ensure the total fraction of ingredients labeled as solute is within a given range.

All minimum and maximum bounds for these three formulation constraints are inclusive.

:class:`~citrine.informatics.constraints.ingredient_fraction_constraint.IngredientFractionConstraint` and :class:`~citrine.informatics.constraints.label_fraction_constraint.LabelFractionConstraint` also have an ``is_required`` flag.
By default ``is_required == True``, indicating that ingredient and label fractions unconditionally must be within the minimum and maximum bound defined by the constraint.
If set to ``False``, the fractional amount may be either zero or within the specified bounds.
In other words, the fractional amount is restricted to the specified bounds *only* when the formulation contains the constrained ingredient (for ingredient fraction constraints) or any ingredient with the given label (for label fraction constraints).
Setting ``is_required`` to ``False`` effectively adds 0 as a valid value.

Formulation Design Spaces define an inherent ``resolution`` for formulations sampled from the domain.
This resolution defines the minimum step size between consecutive formulations sampled from the space.
Resolution does not impose a grid over fractional ingredient amounts.
Instead, it provides a way to specify the characteristic length scale for the problem.
The resolution should be set to the minimum change in fractional ingredient amount that can be expected to make a difference in your problem.
The default resolution is 0.0001, which means that at least one ingredient fraction will differ by at least 0.0001 between consecutive candidates sampled from the formulation design space.

Formulations sampled from the design space are stored using the :class:`~citrine.informatics.descriptors.FormulationDescriptor` passed to the design space when it is configured.
Each formulation contains two pieces of information: a recipe and a collection of ingredient labels.
Each recipe can be thought of as a map from ingredient name to its fractional amount, e.g., ``{"water": 0.99, "salt": 0.01}``.
Ingredient fractions in recipes sampled from a formulation design space will always sum to 1.
Label information defines which labels are applied to each ingredient in the recipe.
These labels will always be a subset of all labels from the design space.

The following demonstrates how to create a formulation design space of saline solutions containing three ingredients: water, salt, and boric acid (a common antiseptic).
We will require that formulations contain 2 ingredients, that no more than 1 solute is present, and that the total fraction of water is between 0.95 and 0.99.

.. code:: python

  from citrine.informatics.descriptors import FormulationDescriptor
  from citrine.informatics.design_spaces import FormulationDesignSpace
  from citrine.informatics.constraints import IngredientCountConstraint, IngredientFractionConstraint

  # define a descriptor to store formulations
  descriptor = FormulationDescriptor(key="saline solution")

  # set of unique ingredient names
  ingredients = {"water", "salt", "boric acid"}

  # labels for each ingredient
  labels = {
    "solute": {"water"},
    "solvent": {"salt", "boric acid"}
  }

  # constraints on formulations emitted from the design space
  constraints = {
    IngredientCountConstraint(formulation_descriptor=descriptor, min=2, max=2),
    IngredientCountConstraint(formulation_descriptor=descriptor, label="solute", min=1, max=1),
    IngredientFractionConstraint(formulation_descriptor=descriptor, ingredient="water", min=0.95, max=0.99)
  }

  design_space = FormulationDesignSpace(
    name = "Saline solution design space",
    description = "Composes formulations from water, salt, and boric acid",
    formulation_descriptor = descriptor,
    ingredients = ingredients,
    labels = labels,
    constraints = constraints
  )

  registered_design_space = project.design_spaces.register(design_space)

Material History Design Space
-----------------------------
