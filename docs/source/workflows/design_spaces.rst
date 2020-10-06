Design spaces
=============

A design space defines a set of materials that should be searched over when performing a material design. Design Spaces must be registered to be used in a :doc:`design workflow <design_workflows>`.
Currently, there are two design spaces:

-  `ProductDesignSpace <#product-design-space>`__
-  `EnumeratedDesignSpace <#enumerated-design-space>`__

Product design space
--------------------

Materials from a product design space are composed from the `Cartesian product`_ of univariate dimensions.
A dimension defines valid values of a single variable.
Valid values can be discrete sets (i.e. enumerated using a list) or continuous ranges (i.e. defined by upper and lower bounds on real numbers).
This design space samples materials by taking one element from each of the dimensions.
For example, given dimensions ``temperature = [300, 400]`` and ``time = [1, 5, 10]`` the Cartesian product is:

.. _`Cartesian product`: https://en.wikipedia.org/wiki/Cartesian_product

::

   candidates = [
     {"temperature": 300, "time": 1},
     {"temperature": 300, "time": 5},
     {"temperature": 300, "time": 10},
     {"temperature": 400, "time": 1},
     {"temperature": 400, "time": 5},
     {"temperature": 400, "time": 10},
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

Multiple :class:`~citrine.informatics.dimensions.EnumeratedDimension` and :class:`~citrine.informatics.dimensions.ContinuousDimension` objects can be combined to form a :class:`~citrine.informatics.design_spaces.ProductDesignSpace`:

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



.. _enumerated-design-space:

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
