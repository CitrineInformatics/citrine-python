Design Spaces
=====================

A Design Space defines a set of materials that should be searched over when performing a material design.
Design Spaces must be registered to be used in a :doc:`design workflow <design_workflows>`.
Currently, there are four Design Spaces:

-  `ProductDesignSpace <#product-design-space>`__
-  `HierarchicalDesignSpace <#hierarchical-design-space>`__
-  `DataSourceDesignSpace <#data-source-design-space>`__
-  `FormulationDesignSpace <#formulation-design-space>`__

Product Design Space
--------------------

Materials from a :class:`~citrine.informatics.design_spaces.product_design_space.ProductDesignSpace` are composed of the `Cartesian product`_ of independent factors.
Each factor can be a separate design space *or* a univariate dimension.
Any other type of design space can be a valid subspace.
Subspaces are defined anonymously and embedded in the product design space.

A :class:`~citrine.informatics.dimensions.Dimension` defines valid values of a single variable.
Valid values can be discrete sets (i.e., enumerated using a list) or continuous ranges (i.e., defined by upper and lower bounds on real numbers).
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
The bounds of the descriptor define the minimum and maximum temperatures that could be considered valid, e.g. our furnace can only reach 1000K.
The bounds of the dimension are the bounds we wish to search between, e.g., restrict the search to between 300 and 400K (even though the furnace can go to much higher temperatures).

A product design space combines subspaces in a similar manner, although subspaces are often multivariate.
However the same principle holds for sampling: all combinations of finite factors are enumerated, while infinite factors are sampled continuously.
Note, each factor must be **independent**.
This means that the same descriptor may not appear more than once in a product design space.

As an example, let's create a produt design space that defines the ways in which we might mix two pigments together and stir at some temperature.
We are only interested in specific amounts of each pigment, so we create a data source design space that references a data source defining the amounts we wish to test.
The mixing speed is discrete, so we describe it with an enumerated dimension.
And temperature is described by a continuous dimension.

.. code:: python

    from citrine.informatics.data_sources import GemTableDataSource
    from citrine.informatics.descriptors import CategoricalDescriptor, RealDescriptor
    from citrine.informatics.design_spaces import DataSourceDesignSpace, ProductDesignSpace
    from citrine.informatics.dimensions import ContinuousDimension, EnumeratedDimension

    pigment_data_source = data_source=GemTableDataSource(table_id=table_id, table_version=table_version)
    enumerated_space = DataSourceDesignSpace(
        name="amounts of pigments A and B",
        description="total amount of pigment is 100 grams",
        data_source=pigment_data_source
    )

    temp_descriptor = RealDescriptor(key='Temperature', lower_bound=273, upper_bound=1000, units='K')
    temp_dimension = ContinuousDimension(descriptor=temp_descriptor, lower_bound=300, upper_bound=400)

    speed_descriptor = CategoricalDescriptor(key='Mixing Speed', categories=["Slow", "Medium", "Fast"])
    speed_dimension = EnumeratedDimension(descriptor=speed_descriptor, values=["Slow", "Fast"])

    product_space = ProductDesignSpace(
        name="Mix 2 pigments at some speed and temperature",
        description="Pigments A and B, temperatures between 300 and 400 K, and either Slow or Fast",
        subspaces=[enumerated_space],
        dimensions=[temp_dimension, speed_dimension]
    )

    product_space = project.design_spaces.register(product_space)

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

Hierarchical Design Space
-------------------------

A :class:`~citrine.informatics.design_spaces.hierarchical_design_space.HierarchicalDesignSpace` produces candidates that represent full material histories.
Unlike a :class:`~citrine.informatics.design_spaces.product_design_space.ProductDesignSpace`, which produces flat candidates with composition represented only by raw ingredients, a hierarchical design space generates candidates with a tree structure: a terminal (root) material connected to sub-materials through formulation ingredients.

The design space is defined by a **root** node and zero or more **sub-nodes**, each represented by a :class:`~citrine.informatics.design_spaces.hierarchical_design_space.MaterialNodeDefinition`.
The root node defines the attributes and formulation contents of the terminal material in each candidate.
Sub-nodes define any new materials that appear in the history of the terminal material.

Commonly, each node in a hierarchical design space contains a :class:`~citrine.informatics.design_spaces.formulation_design_space.FormulationDesignSpace` as its ``formulation_subspace``, which defines the ingredients, labels, and constraints for that level of the material history.
See `Formulation Design Space <#formulation-design-space>`__ below for details on configuring formulation subspaces.

Nodes are connected through formulation ingredient names.
If the root node contains a formulation subspace with an ingredient named ``"New Mixture-001"``, and a sub-node has its ``name`` set to ``"New Mixture-001"``, the resulting candidate will include that sub-node's material as an ingredient in the root material's formulation.
This linking can be extended to sub-nodes referencing other sub-nodes, allowing arbitrarily deep material history shapes.

Material Node Definitions
~~~~~~~~~~~~~~~~~~~~~~~~~

Each :class:`~citrine.informatics.design_spaces.hierarchical_design_space.MaterialNodeDefinition` describes a single node in the material history and has the following fields:

- ``name``: A unique identifier used to reference materials produced by this node.
  When a formulation subspace on another node includes this name as an ingredient, the nodes become linked in the resulting candidate.
- ``attributes``: A list of :class:`~citrine.informatics.dimensions.Dimension` objects defining the processing parameters on the materials produced by this node.
  These dimensions are explored independently during Candidate Generation.
- ``formulation_subspace``: An optional :class:`~citrine.informatics.design_spaces.formulation_design_space.FormulationDesignSpace` defining the ingredients, labels, and constraints for formulations on materials produced by this node.
- ``template_link``: An optional :class:`~citrine.informatics.design_spaces.hierarchical_design_space.TemplateLink` linking the node to material and process templates on the Citrine Platform.
- ``scope``: An optional custom scope used to identify the materials produced by this node.
- ``display_name``: An optional display name for identifying the node on the Citrine Platform (does not appear in generated candidates).

Template Links
~~~~~~~~~~~~~~

A :class:`~citrine.informatics.design_spaces.hierarchical_design_space.TemplateLink` associates a node with on-platform material and process templates via their UUIDs.
Template names can optionally be provided for readability.

Data Sources
~~~~~~~~~~~~

:class:`~citrine.informatics.data_sources.DataSource` objects can be included on the design space to allow design over "known" materials.
When constructing candidates, the Citrine Platform looks up ingredient names from formulation subspaces in the provided data sources and injects their composition and properties into the material history.
When constructing a default hierarchical design space, the platform includes any data sources found on the associated predictor configuration.

Creating a Hierarchical Design Space
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The easiest way to build a hierarchical design space is to use :func:`~citrine.resources.design_space.DesignSpaceCollection.create_default` with ``mode=DefaultDesignSpaceMode.HIERARCHICAL``.
This inspects the predictor's training data to infer the material history shape and automatically constructs the root node, sub-nodes, dimensions, and formulation subspaces:

.. code:: python

    from citrine.informatics.design_spaces import DefaultDesignSpaceMode

    design_space = project.design_spaces.create_default(
        predictor_id=predictor_id,
        predictor_version=predictor_version,
        mode=DefaultDesignSpaceMode.HIERARCHICAL,
    )

    registered_design_space = project.design_spaces.register(design_space)

If you already have a registered :class:`~citrine.informatics.design_spaces.product_design_space.ProductDesignSpace`, you can convert it into an equivalent hierarchical design space using :func:`~citrine.resources.design_space.DesignSpaceCollection.convert_to_hierarchical`:

.. code:: python

    hierarchical_ds = project.design_spaces.convert_to_hierarchical(
        product_design_space.uid,
        predictor_id=predictor_id,
        predictor_version=predictor_version,
    )

    registered_design_space = project.design_spaces.register(hierarchical_ds)

Manual Construction Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following example creates a hierarchical design space for a coating material manually.
The root node represents the final coating, which is a formulation of a binder and a pigment mixture.
The pigment mixture is defined as a sub-node with its own formulation and a processing temperature attribute.

.. code:: python

    from citrine.informatics.constraints import IngredientCountConstraint
    from citrine.informatics.data_sources import GemTableDataSource
    from citrine.informatics.descriptors import FormulationDescriptor, RealDescriptor
    from citrine.informatics.design_spaces import (
        FormulationDesignSpace,
        HierarchicalDesignSpace,
    )
    from citrine.informatics.design_spaces.hierarchical_design_space import (
        MaterialNodeDefinition,
    )
    from citrine.informatics.dimensions import ContinuousDimension

    # Define the formulation descriptor used across the design space
    formulation_descriptor = FormulationDescriptor.hierarchical()

    # --- Sub-node: Pigment Mixture ---
    # This node defines a mixture of two pigments with a processing temperature.
    pigment_formulation = FormulationDesignSpace(
        name="Pigment blend",
        description="Blend of pigment A and pigment B",
        formulation_descriptor=formulation_descriptor,
        ingredients={"Pigment A", "Pigment B"},
        labels={"pigment": {"Pigment A", "Pigment B"}},
        constraints={
            IngredientCountConstraint(
                formulation_descriptor=formulation_descriptor, min=2, max=2
            )
        },
    )

    temp_descriptor = RealDescriptor(
        key="Mixing Temperature", lower_bound=273, upper_bound=500, units="K"
    )
    temp_dimension = ContinuousDimension(
        descriptor=temp_descriptor, lower_bound=300, upper_bound=400
    )

    pigment_node = MaterialNodeDefinition(
        name="Pigment Mixture",
        attributes=[temp_dimension],
        formulation_subspace=pigment_formulation,
        display_name="Pigment Mixture",
    )

    # --- Root node: Final Coating ---
    # The coating is a formulation of a binder and the pigment mixture defined above.
    # The ingredient name "Pigment Mixture" matches the sub-node's name,
    # which links them in the resulting candidates.
    coating_formulation = FormulationDesignSpace(
        name="Coating formulation",
        description="Binder plus pigment mixture",
        formulation_descriptor=formulation_descriptor,
        ingredients={"Binder", "Pigment Mixture"},
        labels={"resin": {"Binder"}, "filler": {"Pigment Mixture"}},
        constraints={
            IngredientCountConstraint(
                formulation_descriptor=formulation_descriptor, min=2, max=2
            )
        },
    )

    root_node = MaterialNodeDefinition(
        name="Final Coating",
        formulation_subspace=coating_formulation,
        display_name="Final Coating",
    )

    # --- Assemble the hierarchical design space ---
    design_space = HierarchicalDesignSpace(
        name="Coating design space",
        description="Designs coatings from binder and a pigment mixture",
        root=root_node,
        subspaces=[pigment_node],
        data_sources=[
            GemTableDataSource(table_id=table_id, table_version=table_version)
        ],
    )

    registered_design_space = project.design_spaces.register(design_space)

In this example, each candidate produced by the design space will contain a terminal coating material whose formulation includes a "Binder" (resolved from the data source) and a "Pigment Mixture" (a newly designed material with its own formulation and mixing temperature).

Data Source Design Space
------------------------

A :class:`~citrine.informatics.design_spaces.data_source_design_space.DataSourceDesignSpace` draws its candidates from an existing data source.
Any data source can be used and no additional information is needed.
When registered, this type of design space must be a subspace of a :class:`~citrine.informatics.design_spaces.product_design_space.ProductDesignSpace`.

For example, assume you have a :class:`~citrine.resources.gemtables.GemTable` that contains one
:class:`~citrine.gemtables.rows.Row` for each candidate that you wish to test.
Assume the table's ``table_id`` and ``table_version`` are known.
The example code below creates a registers a design space based on this Gem Table.

.. code:: python

    from citrine.informatics.data_sources import GemTableDataSource
    from citrine.informatics.design_spaces import DataSourceDesignSpace, ProductDesignSpace

    data_source = GemTableDataSource(
        table_id=table_id,
        table_version=table_version
    )

    data_source_design_space = DataSourceDesignSpace(
        name="my candidates",
        description="450 potential formulations",
        data_source=data_source
    )

    design_space = ProductDesignSpace(
        name="top-level design space",
        description="contains a single data source design space.",
        subspaces=[data_source_design_space]
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

When registered, this type of design space must be a subspace of a :class:`~citrine.informatics.design_spaces.product_design_space.ProductDesignSpace` or part of a :class:`~citrine.informatics.design_spaces.hierarchical_design_space.HierarchicalDesignSpace`.

The following demonstrates how to create a formulation design space of saline solutions containing three ingredients: water, salt, and boric acid (a common antiseptic).
We will require that formulations contain 2 ingredients, that no more than 1 solute is present, and that the total fraction of water is between 0.95 and 0.99.

.. code:: python

  from citrine.informatics.descriptors import FormulationDescriptor
  from citrine.informatics.design_spaces import FormulationDesignSpace
  from citrine.informatics.constraints import IngredientCountConstraint, IngredientFractionConstraint

  # define the default descriptor to store formulations
  descriptor = FormulationDescriptor.hierarchical()

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

  formulation_design_space = FormulationDesignSpace(
    name = "Saline solution design space",
    description = "Composes formulations from water, salt, and boric acid",
    formulation_descriptor = descriptor,
    ingredients = ingredients,
    labels = labels,
    constraints = constraints
  )
    
  design_space = ProductDesignSpace(
    name="top-level design space",
    description="contains a single formulation design space.",
    subspaces=[formulation_design_space]
  )

  registered_design_space = project.design_spaces.register(design_space)

Sampling from Design Spaces
---------------------------

To sample candidates from a registered design space, follow the example below:

.. code:: python

   from citrine import Citrine
   from citrine.jobs.waiting import wait_while_executing
   from citrine.informatics.design_spaces.sample_design_space import SampleDesignSpaceInput

   sample_input = SampleDesignSpaceInput(n_candidates=50)
   sample_design_space_collection = design_space.sample_design_space_executions
   sample_design_space_execution = sample_design_space_collection.trigger(sample_input)

   execution = wait_while_executing(
       collection=sample_design_space_collection, execution=sample_design_space_execution
   )

   sampled_candidates = [candidate.material for candidate in execution.results()]
   root_materials = [candidate.root for candidate in sampled_candidates]
